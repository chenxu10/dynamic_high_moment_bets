"""
Probability Analysis Charts
===========================
Python translation of the JS probability analysis module.
Provides Monte Carlo simulation (Student-t distribution) and two
matplotlib-based charts:

  Chart 2 — Price Probability Density at the simulation date
            (t-distribution fill vs. lognormal dashed line)
  Chart 3 — Expected P&L Density  =  P&L(s) × f_t(s)

Plus a single-number Expected P&L badge = ∫ P&L(s) × f_t(s) ds
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.integrate import simpson

# Matplotlib is optional at import time so the module can be loaded
# in headless environments that only need the data-prep helpers.
try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:  # pragma: no cover
    _HAS_MPL = False

# -----------------------------------------------------------------------
# 1.  Monte Carlo Simulation (replaces the inline Web Worker)
# -----------------------------------------------------------------------


def _box_muller(n: int) -> np.ndarray:
    """Vectorised Box-Muller: n independent N(0,1) samples."""
    u1 = np.random.uniform(1e-15, 1.0, size=n)
    u2 = np.random.uniform(0.0, 1.0, size=n)
    return np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)


def _gamma_ms(alpha: float, n: int) -> np.ndarray:
    """Marsaglia-Tsang Gamma(alpha, 1) — vectorised via scipy."""
    return stats.gamma.rvs(a=alpha, scale=1.0, size=n)


def _t_sample(df: float, loc: float, scale: float, n: int) -> np.ndarray:
    """
    Draw n samples from Student-t(df) scaled to (loc, scale).
    Uses the Normal / chi2 decomposition so the random stream
    matches the spirit of the original JS worker.
    """
    z = _box_muller(n)
    chi2 = 2.0 * _gamma_ms(df / 2.0, n)
    return loc + scale * z / np.sqrt(chi2 / df)


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    """Fast Normal CDF (scipy)."""
    return stats.norm.cdf(x)


def _bsm_d1_d2(S, K, T, r, sigma):
    """Black-Scholes d1 and d2."""
    v_sqrt_T = sigma * np.sqrt(T)
    inv_v_sqrt_T = 1.0 / v_sqrt_T
    d1_const = (-np.log(K) + (r + 0.5 * sigma * sigma) * T) * inv_v_sqrt_T
    log_S = np.log(S)
    d1 = log_S * inv_v_sqrt_T + d1_const
    d2 = d1 - v_sqrt_T
    return d1, d2


def _bsm_option_value(S, K, T, r, sigma, option_type="call"):
    """Black-Scholes-Merton value for a single option leg."""
    if T <= 0:
        if option_type == "call":
            return np.maximum(S - K, 0.0)
        return np.maximum(K - S, 0.0)
    d1, d2 = _bsm_d1_d2(S, K, T, r, sigma)
    if option_type == "call":
        return S * _normal_cdf(d1) - K * np.exp(-r * T) * _normal_cdf(d2)
    return K * np.exp(-r * T) * _normal_cdf(-d2) - S * _normal_cdf(-d1)


def run_monte_carlo(
    df: float,
    loc: float,
    new_scale: float,
    n_days: int,
    n_paths: int,
    current_price: float,
    min_s: float,
    max_s: float,
    bins: int,
    legs: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Main Monte Carlo simulation — direct replacement for the JS Worker.

    Returns
    -------
    t_density : np.ndarray, shape (bins,)
    bin_centers : np.ndarray, shape (bins,)
    bin_width : float
    exact_expected_pnl : float
    """
    bin_width = (max_s - min_s) / bins
    counts = np.zeros(bins, dtype=np.float64)

    # --- Precompute Leg Constants (same logic as the JS worker) ---
    worker_legs: List[Dict[str, Any]] = []
    if legs:
        for leg in legs:
            wl = dict(leg)
            if wl.get("isUnderlyingLeg"):
                worker_legs.append(wl)
                continue
            v = wl.get("v", 0.0)
            if v <= 0:
                v = 0.0001
            T = wl.get("T", 0.0)
            wl["is_expired"] = T <= 0
            if not wl["is_expired"]:
                v_sqrt_T = v * np.sqrt(T)
                wl["v_sqrt_T"] = v_sqrt_T
                wl["inv_v_sqrt_T"] = 1.0 / v_sqrt_T
                wl["d1_const"] = (
                    -np.log(wl["K"]) + (wl["r"] + 0.5 * v * v) * T
                ) / v_sqrt_T
                wl["K_exp_rT"] = wl["K"] * np.exp(-wl["r"] * T)
            worker_legs.append(wl)

    exact_pnl_sum = 0.0

    # Process in vectorised chunks for memory efficiency
    chunk_size = min(n_paths, 100_000)
    n_chunks = (n_paths + chunk_size - 1) // chunk_size

    for chunk in range(n_chunks):
        this_chunk = min(chunk_size, n_paths - chunk * chunk_size)

        # Accumulate n_days of daily log-returns
        log_ret = np.zeros(this_chunk, dtype=np.float64)
        for _d in range(n_days):
            log_ret += _t_sample(df, loc, new_scale, this_chunk)

        final_prices = current_price * np.exp(log_ret)

        # Histogram counts
        bin_idx = np.floor((final_prices - min_s) / bin_width).astype(np.int64)
        in_range = (bin_idx >= 0) & (bin_idx < bins)
        np.add.at(counts, bin_idx[in_range], 1)

        # Exact BSM path pricing
        if worker_legs:
            path_pnl = np.zeros(this_chunk, dtype=np.float64)
            for wl in worker_legs:
                leg_price = final_prices * wl.get("underlyingScale", 1.0)
                safe_leg_price = np.where(leg_price > 0, leg_price, 0.0001)

                fixed = wl.get("fixedPrice")
                if fixed is not None:
                    v_opt = np.full(this_chunk, fixed, dtype=np.float64)
                elif wl.get("isUnderlyingLeg"):
                    v_opt = safe_leg_price
                elif wl.get("is_expired"):
                    if wl["type"] == "call":
                        v_opt = np.maximum(safe_leg_price - wl["K"], 0.0)
                    else:
                        v_opt = np.maximum(wl["K"] - safe_leg_price, 0.0)
                else:
                    log_S = np.log(safe_leg_price)
                    d1 = log_S * wl["inv_v_sqrt_T"] + wl["d1_const"]
                    d2 = d1 - wl["v_sqrt_T"]
                    if wl["type"] == "call":
                        v_opt = (
                            safe_leg_price * _normal_cdf(d1)
                            - wl["K_exp_rT"] * _normal_cdf(d2)
                        )
                    else:
                        v_opt = (
                            wl["K_exp_rT"] * _normal_cdf(-d2)
                            - safe_leg_price * _normal_cdf(-d1)
                        )

                path_pnl += wl["posMultiplier"] * v_opt - wl["costBasis"]
            exact_pnl_sum += float(np.sum(path_pnl))

    exact_expected_pnl = exact_pnl_sum / n_paths if n_paths > 0 else 0.0

    # Normalise to probability density
    norm_factor = n_paths * bin_width
    t_density = counts / norm_factor

    # Bin centres
    bin_centers = min_s + (np.arange(bins) + 0.5) * bin_width

    return t_density, bin_centers, bin_width, exact_expected_pnl


# -----------------------------------------------------------------------
# 2.  Math helpers
# -----------------------------------------------------------------------


def calibrate_scale(df: float, portfolio_iv: float) -> float:
    """
    Recalibrate the t-distribution scale so that its std equals IV/sqrt(365).
    Keeps df (tail shape) and loc (drift) from the historical fit.
    """
    target_daily_vol = portfolio_iv / np.sqrt(365.0)
    if df <= 2.001:
        return target_daily_vol
    return target_daily_vol / np.sqrt(df / (df - 2.0))


def lognormal_density(
    s: np.ndarray,
    s0: float,
    portfolio_iv: float,
    loc: float,
    n_days: int,
) -> np.ndarray:
    """
    Lognormal (normal-model) probability density for the price S at the
    simulation date, using the same drift as the t-model (historical loc).
    """
    if s0 <= 0 or n_days <= 0:
        return np.zeros_like(s)
    sigma = (portfolio_iv / np.sqrt(365.0)) * np.sqrt(n_days)
    mu = loc * n_days
    if sigma <= 0:
        return np.zeros_like(s)
    z = (np.log(s / s0) - mu) / sigma
    return (
        1.0 / (s * sigma * np.sqrt(2.0 * np.pi))
    ) * np.exp(-0.5 * z * z)


def smooth(arr: np.ndarray, window: int = 7) -> np.ndarray:
    """Simple moving-average smoother."""
    result = np.empty_like(arr)
    half = window // 2
    for i in range(len(arr)):
        start = max(0, i - half)
        end = min(len(arr), i + half + 1)
        result[i] = np.mean(arr[start:end])
    return result


# -----------------------------------------------------------------------
# 3.  Portfolio P&L helpers
# -----------------------------------------------------------------------


def compute_portfolio_pnl_at_price(
    price: float,
    legs: List[Any],
) -> float:
    """
    Compute the portfolio's P&L at a given underlying price.

    Supports two leg representations:
      * dicts with keys: type, K, posMultiplier, costBasis, fixedPrice,
        isUnderlyingLeg, underlyingScale, is_expired, etc.
      * objects from src.position_builder (LongCall, ShortCall, ...)
    """
    total = 0.0
    for leg in legs:
        if isinstance(leg, dict):
            total += _pnl_for_dict_leg(price, leg)
        else:
            total += _pnl_for_object_leg(price, leg)
    return total


def _pnl_for_dict_leg(price: float, leg: Dict[str, Any]) -> float:
    """P&L for a worker-style dictionary leg."""
    fixed = leg.get("fixedPrice")
    if fixed is not None:
        v_opt = fixed
    elif leg.get("isUnderlyingLeg"):
        v_opt = price * leg.get("underlyingScale", 1.0)
    elif leg.get("is_expired"):
        if leg["type"] == "call":
            v_opt = max(price - leg["K"], 0.0)
        else:
            v_opt = max(leg["K"] - price, 0.0)
    else:
        # Live BSM price (simplified single-point evaluation)
        S = price * leg.get("underlyingScale", 1.0)
        S = max(S, 0.0001)
        v_opt = float(
            _bsm_option_value(
                S,
                leg["K"],
                leg["T"],
                leg["r"],
                leg["v"],
                leg["type"],
            )
        )
    return leg["posMultiplier"] * v_opt - leg["costBasis"]


def _pnl_for_object_leg(price: float, leg: Any) -> float:
    """P&L for a src.position_builder leg object at expiration."""
    # Dispatch via duck typing on known classes
    cls_name = type(leg).__name__
    c = leg.contract
    if cls_name == "LongCall":
        intrinsic = max(price - c.strike, 0.0) * c.volume * 100
        return intrinsic - c.unit_premium * c.volume * 100
    elif cls_name == "ShortCall":
        intrinsic = max(price - c.strike, 0.0) * c.volume * 100
        return c.unit_premium * c.volume * 100 - intrinsic
    elif cls_name == "LongPut":
        intrinsic = max(c.strike - price, 0.0) * c.volume * 100
        return intrinsic - c.unit_premium * c.volume * 100
    elif cls_name == "ShortPut":
        intrinsic = max(c.strike - price, 0.0) * c.volume * 100
        return c.unit_premium * c.volume * 100 - intrinsic
    elif cls_name == "LongStock":
        return (price - c.strike) * c.volume
    else:
        # Fallback: try the object's pnl_at method
        return leg.pnl_at(price)


# -----------------------------------------------------------------------
# 4.  Data containers (decouple preparation from rendering)
# -----------------------------------------------------------------------


@dataclass
class ProbabilityPlotData:
    """Prepared data for Chart 2 (Price Probability Density)."""

    bin_centers: np.ndarray
    t_density: np.ndarray
    normal_density: np.ndarray
    min_s: float
    max_s: float
    current_price: float
    anchor_info: Optional[Dict[str, Any]] = None


@dataclass
class ExpectedPnLPlotData:
    """Prepared data for Chart 3 (Expected P&L Density)."""

    bin_centers: np.ndarray
    pnl_values: np.ndarray
    fev: np.ndarray
    min_s: float
    max_s: float
    current_price: float
    anchor_info: Optional[Dict[str, Any]] = None
    exact_expected_pnl: float = 0.0


@dataclass
class ProbabilityAnalysisResult:
    """Complete result bundle from the probability analysis pipeline."""

    prob_plot_data: ProbabilityPlotData
    epnl_plot_data: ExpectedPnLPlotData
    exact_expected_pnl: float
    info_text: str = ""


# -----------------------------------------------------------------------
# 5.  Matplotlib rendering (adapter-style, optional)
# -----------------------------------------------------------------------


def render_probability_chart(plot_data: ProbabilityPlotData, ax=None):
    """Render Chart 2 — Price Probability Density."""
    if not _HAS_MPL:
        raise RuntimeError("matplotlib is required for rendering")

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
    else:
        fig = ax.figure

    bc = plot_data.bin_centers
    t_smooth = smooth(plot_data.t_density, 7)
    n_smooth = smooth(plot_data.normal_density, 5)

    # t-distribution: filled area + outline
    ax.fill_between(
        bc, t_smooth, alpha=0.18, color="#6366F1",
        label="Student-t (fat-tail, IV-scaled)",
    )
    ax.plot(bc, t_smooth, color="#6366F1", linewidth=2, alpha=0.9)

    # Normal / lognormal: dashed line
    ax.plot(
        bc, n_smooth, color="#F97316", linewidth=2,
        linestyle="--", alpha=0.9,
        label="Normal / Lognormal (BSM baseline)",
    )

    # Current price vertical reference
    cp = plot_data.current_price
    if plot_data.min_s <= cp <= plot_data.max_s:
        ax.axvline(cp, color="#6366F1", linestyle="--", linewidth=1.5, alpha=0.8)
        y_top = ax.get_ylim()[1] if ax.has_data() else 0.01
        ax.text(
            cp, y_top * 0.95,
            f"Current: ${cp:,.2f}",
            color="#6366F1", fontsize=10, ha="center",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="white",
                edgecolor="#6366F1", alpha=0.8,
            ),
        )

    ax.set_xlim(plot_data.min_s, plot_data.max_s)
    ax.set_ylabel("Probability Density")
    ax.set_xlabel("Underlying Price ($)")
    ax.set_title("Price Probability Density at Simulation Date")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    return fig


def render_expected_pnl_chart(plot_data: ExpectedPnLPlotData, ax=None):
    """Render Chart 3 — Expected P&L Density."""
    if not _HAS_MPL:
        raise RuntimeError("matplotlib is required for rendering")

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
    else:
        fig = ax.figure

    bc = plot_data.bin_centers
    fev_smooth = smooth(plot_data.fev, 7)

    # Positive region (profit contribution) — green fill
    ax.fill_between(
        bc, fev_smooth, 0, where=(fev_smooth >= 0),
        color="green", alpha=0.20, label="Profit contribution",
    )
    # Negative region (loss contribution) — red fill
    ax.fill_between(
        bc, fev_smooth, 0, where=(fev_smooth < 0),
        color="red", alpha=0.20, label="Loss contribution",
    )

    # Curve outline
    ax.plot(bc, fev_smooth, color="darkgreen", linewidth=2, label="E[P&L] density")

    # Zero baseline
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)

    # Current price reference
    cp = plot_data.current_price
    if plot_data.min_s <= cp <= plot_data.max_s:
        ax.axvline(cp, color="#6366F1", linestyle="--", linewidth=1.5, alpha=0.7)

    ax.set_xlim(plot_data.min_s, plot_data.max_s)
    ax.set_ylabel("P&L × Probability Density")
    ax.set_xlabel("Underlying Price ($)")
    ax.set_title("Expected P&L Contribution by Price  (area = E[P&L])")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    # Expected P&L annotation badge
    ev = plot_data.exact_expected_pnl
    sign = "+" if ev >= 0 else ""
    ax.text(
        0.98, 0.95,
        f"Expected P&L:\n{sign}${ev:,.2f}",
        transform=ax.transAxes, fontsize=12,
        verticalalignment="top", horizontalalignment="right",
        color="green" if ev >= 0 else "red", fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.6", facecolor="honeydew",
            edgecolor="green", alpha=0.9,
        ),
    )
    return fig


def save_figure(fig, output_path: str, dpi: int = 150):
    """Persist figure to disk, creating parent directories if needed."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"Plot saved to: {os.path.abspath(output_path)}")


# -----------------------------------------------------------------------
# 6.  Main orchestrator (translation of updateProbCharts)
# -----------------------------------------------------------------------


def update_prob_charts(
    current_price: float,
    portfolio_iv: float,
    n_days: int,
    min_s: float,
    max_s: float,
    t_params: Optional[Dict[str, float]] = None,
    legs: Optional[List[Any]] = None,
    use_random_walk: bool = False,
    n_paths: int = 1_000_000,
    bins: int = 500,
    figsize: Tuple[float, float] = (12, 10),
    output_path: Optional[str] = None,
    distribution_symbol: Optional[str] = None,
) -> ProbabilityAnalysisResult:
    """
    Main orchestrator — Python equivalent of JS ``updateProbCharts()``.

    Parameters
    ----------
    current_price : float
        Current underlying price (anchor).
    portfolio_iv : float
        Portfolio mean implied volatility (annualised decimal).
    n_days : int
        Calendar days to simulation / expiration.
    min_s, max_s : float
        Price range for the charts.
    t_params : dict, optional
        Historical t-distribution parameters: {"df": ..., "loc": ...}.
    legs : list, optional
        Portfolio legs (dicts or position_builder objects).
    use_random_walk : bool
        If True, forces loc = 0 (random-walk mode).
    n_paths : int
        Monte Carlo paths (default 1_000_000).
    bins : int
        Histogram bins (default 500).
    figsize : tuple
        Matplotlib figure size.
    output_path : str, optional
        If given, saves the figure to this path.
    distribution_symbol : str, optional
        Symbol name for info text (e.g. "USO" or "SPY").

    Returns
    -------
    ProbabilityAnalysisResult
        Bundled data objects, exact expected P&L, and status text.
    """
    if t_params is None:
        t_params = {}

    df = float(t_params.get("df", 5.0))
    raw_loc = float(t_params.get("loc", 0.0))
    loc = 0.0 if use_random_walk else raw_loc
    new_scale = calibrate_scale(df, portfolio_iv)

    # Show status
    drift_label = " | Random Walk" if use_random_walk else ""
    proxy_info = (
        f" | Dist Proxy: {distribution_symbol}"
        if distribution_symbol else ""
    )
    info_text = (
        f"Simulating {n_paths/1e6:.0f}M paths × {n_days} cd  "
        f"(IV {portfolio_iv*100:.1f}%{drift_label}){proxy_info}…"
    )

    # 1. Monte Carlo
    t_density, bin_centers, _bin_width, exact_expected_pnl = run_monte_carlo(
        df=df,
        loc=loc,
        new_scale=new_scale,
        n_days=n_days,
        n_paths=n_paths,
        current_price=current_price,
        min_s=min_s,
        max_s=max_s,
        bins=bins,
        legs=legs,
    )

    # 2. Normal / lognormal comparison (analytical, no sampling)
    normal_density = lognormal_density(
        bin_centers, current_price, portfolio_iv, loc, n_days
    )
    integral = simpson(normal_density, bin_centers)
    if integral > 0:
        normal_density /= integral

    # 3. P&L curve at each bin centre
    if legs:
        pnl_values = np.array([
            compute_portfolio_pnl_at_price(b, legs) for b in bin_centers
        ])
    else:
        pnl_values = np.zeros_like(bin_centers)

    # 4. Expected P&L density: f_ev = pnl × t_density
    fev = pnl_values * t_density

    prob_plot_data = ProbabilityPlotData(
        bin_centers=bin_centers,
        t_density=t_density,
        normal_density=normal_density,
        min_s=min_s,
        max_s=max_s,
        current_price=current_price,
    )

    epnl_plot_data = ExpectedPnLPlotData(
        bin_centers=bin_centers,
        pnl_values=pnl_values,
        fev=fev,
        min_s=min_s,
        max_s=max_s,
        current_price=current_price,
        exact_expected_pnl=exact_expected_pnl,
    )

    # 5. Render if matplotlib is available
    if _HAS_MPL:
        fig, axes = plt.subplots(2, 1, figsize=figsize)
        render_probability_chart(prob_plot_data, ax=axes[0])
        render_expected_pnl_chart(epnl_plot_data, ax=axes[1])
        plt.tight_layout()

        if output_path:
            save_figure(fig, output_path)
        # Do not call plt.show() here — caller decides
    else:
        fig = None

    # Update final info text
    final_info = (
        f"{n_paths/1e6:.0f}M paths | {n_days} cd | "
        f"Mean IV: {portfolio_iv*100:.1f}%"
        f"{drift_label}"
        f"{proxy_info}"
    )

    return ProbabilityAnalysisResult(
        prob_plot_data=prob_plot_data,
        epnl_plot_data=epnl_plot_data,
        exact_expected_pnl=exact_expected_pnl,
        info_text=final_info,
    )


# -----------------------------------------------------------------------
# 7.  Convenience entry-point for a Position object
# -----------------------------------------------------------------------


def analyze_position(
    position,
    current_price: float,
    portfolio_iv: float,
    n_days: int,
    min_s: float,
    max_s: float,
    t_params: Optional[Dict[str, float]] = None,
    **kwargs,
) -> ProbabilityAnalysisResult:
    """
    Convenience wrapper that accepts a src.position_builder.Position
    directly and auto-converts its legs to the internal dict format.
    """
    dict_legs = []
    for leg in position.legs:
        cls_name = type(leg).__name__
        multiplier = 1.0
        if cls_name.startswith("Short"):
            multiplier = -1.0
        dict_legs.append({
            "type": cls_name.lower().replace("long", "").replace("short", ""),
            "isUnderlyingLeg": cls_name == "LongStock",
            "K": getattr(leg.contract, "strike", 0.0),
            "r": 0.0,          # default; caller can override via kwargs
            "T": n_days / 365.0,
            "v": portfolio_iv,
            "posMultiplier": multiplier,
            "costBasis": getattr(leg.contract, "unit_premium", 0.0)
            * getattr(leg.contract, "volume", 1)
            * (1 if cls_name == "LongStock" else 100),
            "underlyingScale": 1.0,
            "fixedPrice": None,
        })
    # Merge any extra leg fields passed in kwargs
    if "legs" in kwargs:
        kwargs.pop("legs")
    return update_prob_charts(
        current_price=current_price,
        portfolio_iv=portfolio_iv,
        n_days=n_days,
        min_s=min_s,
        max_s=max_s,
        t_params=t_params,
        legs=dict_legs,
        **kwargs,
    )


# -----------------------------------------------------------------------
# 8.  Hello World — runnable entry point
# -----------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Hello from prob_chart.py!")
    print("=" * 60)

    # Synthetic market data
    CURRENT_PRICE = 100.0
    PORTFOLIO_IV = 0.30          # 30 % annualised implied vol
    N_DAYS = 30                  # 30 calendar days to expiration
    MIN_S = 70.0                 # chart lower bound
    MAX_S = 130.0                # chart upper bound

    # A simple short-put position (1 contract)
    #   Premium received = $5 per share -> $500 per contract
    #   Max profit = $500, Max loss = (strike - 0) * 100 - 500
    LEGS = [
        {
            "type": "put",
            "isUnderlyingLeg": False,
            "K": 100.0,
            "r": 0.0,
            "T": N_DAYS / 365.0,
            "v": PORTFOLIO_IV,
            "posMultiplier": -1.0,          # short
            "costBasis": 5.0 * 100,           # $500 premium received
            "underlyingScale": 1.0,
            "fixedPrice": None,
        }
    ]

    # Historical t-params (synthetic — would normally come from fit_ticker)
    T_PARAMS = {"df": 5.0, "loc": 0.0}

    print(f"\nRunning Monte-Carlo simulation ...")
    print(f"  Current price : ${CURRENT_PRICE:,.2f}")
    print(f"  Portfolio IV  : {PORTFOLIO_IV*100:.1f}%")
    print(f"  Days to exp   : {N_DAYS}")
    print(f"  Price range   : ${MIN_S:,.2f} – ${MAX_S:,.2f}")
    print(f"  Legs          : 1 Short Put @ ${LEGS[0]['K']:,.2f}")

    result = update_prob_charts(
        current_price=CURRENT_PRICE,
        portfolio_iv=PORTFOLIO_IV,
        n_days=N_DAYS,
        min_s=MIN_S,
        max_s=MAX_S,
        t_params=T_PARAMS,
        legs=LEGS,
        n_paths=50_000,          # fast enough for a hello-world run
        bins=200,
        output_path="figures/prob_chart_hello_world.png",
    )

    print(f"\n{result.info_text}")
    sign = "+" if result.exact_expected_pnl >= 0 else ""
    print(f"Exact Expected P&L : {sign}${result.exact_expected_pnl:,.2f}")

    print("\n" + "=" * 60)
    print("Done! Check figures/prob_chart_hello_world.png")
    print("=" * 60)

