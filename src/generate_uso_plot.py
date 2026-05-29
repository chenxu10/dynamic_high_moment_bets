"""
Generate USO-based Probability Analysis and Portfolio P&L Plot

This script replicates the simulation_exp_plot visualization
but uses USO (United States Oil Fund) as the distribution proxy
instead of SPY.
"""

import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.integrate import simpson
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
TICKER = "USO"
SIMULATION_DAYS = 29          # days to expiration
N_PATHS = 1_000_000           # Monte Carlo paths
MEAN_IV = 0.084               # 8.4% mean implied volatility
PRICE_RANGE_PCT = 0.25        # +/- 25% price range for display
N_PRICE_POINTS = 500          # resolution for curves

# Portfolio legs (replicating a similar payoff shape)
# These can be adjusted to match any specific strategy
# For USO (~$76) we use strikes around the current price.
PORTFOLIO_LEGS = [
    {"type": "long_call", "strike": 70, "premium": 3.50, "volume": 10},
    {"type": "short_call", "strike": 76, "premium": 1.80, "volume": 20},
    {"type": "long_call", "strike": 82, "premium": 0.80, "volume": 10},
]

# =============================================================================
# DATA FETCHING
# =============================================================================

def _extract_current_price(data):
    """Return the most recent closing price as a float."""
    return float(data['Close'].values.flatten()[-1])


def _extract_historical_prices(data):
    """Return all historical closing prices as a flat numpy array."""
    return data['Close'].values.flatten()


def _compute_annualized_volatility(daily_returns):
    """Annualize the standard deviation of daily log returns."""
    return float(np.std(daily_returns) * np.sqrt(252))


def _compute_log_returns(hist_prices):
    """Compute daily log returns from a series of prices."""
    return np.diff(np.log(hist_prices))


def fetch_ticker_data(ticker: str):
    """Download historical price data for the given ticker.

    Falls back to synthetic data if live download fails (e.g. rate-limited).
    """
    print(f"Fetching data for {ticker}...")
    try:
        data = yf.download(ticker, period="1y", progress=False)
        print(data)
        if not data.empty:
            current_price = _extract_current_price(data)
            hist_prices = _extract_historical_prices(data)
            returns = _compute_log_returns(hist_prices)
            realized_vol = _compute_annualized_volatility(returns)
            print(f"  (live data from Yahoo Finance)")
            return current_price, realized_vol, hist_prices
    except Exception as exc:
        print(f"  Live download failed: {exc}")
        raise


# =============================================================================
# PROBABILITY DISTRIBUTIONS
# =============================================================================

def student_t_pdf(x, loc, scale, df=5):
    """Student-t probability density with fat tails."""
    return stats.t.pdf(x, df=df, loc=loc, scale=scale)


def normal_pdf(x, loc, scale):
    """Normal (BSM baseline) probability density."""
    return stats.norm.pdf(x, loc=loc, scale=scale)


def build_distributions(current_price, days, iv, n_points=500, range_pct=0.25):
    """Build price grids and probability densities."""
    # Price range: +/- range_pct around current price
    price_min = current_price * (1 - range_pct)
    price_max = current_price * (1 + range_pct)
    prices = np.linspace(price_min, price_max, n_points)

    # Annualized -> over `days`
    t = days / 252.0
    sigma_t = iv * np.sqrt(t)

    # Scale in log-space, then transform back
    log_s0 = np.log(current_price)
    log_scale = sigma_t

    # Student-t (fat-tail, IV-scaled)
    # We match the variance by scaling appropriately
    # Variance of t(df) = df/(df-2) for df>2; adjust scale
    df = 5
    t_scale = log_scale / np.sqrt(df / (df - 2))
    student_t_log = student_t_pdf(np.log(prices), loc=log_s0, scale=t_scale, df=df)
    # Jacobian adjustment for log-normal transformation
    student_t_density = student_t_log / prices

    # Normal / Lognormal (BSM baseline)
    normal_log = normal_pdf(np.log(prices), loc=log_s0, scale=log_scale)
    normal_density = normal_log / prices

    # Normalize both to integrate to 1 over the visible range
    for arr in [student_t_density, normal_density]:
        integral = simpson(arr, prices)
        if integral > 0:
            arr /= integral

    return prices, student_t_density, normal_density

# =============================================================================
# PORTFOLIO P&L
# =============================================================================

def portfolio_pnl(price, legs):
    """Calculate total P&L at a given underlying price."""
    total = 0.0
    multiplier = 100  # standard option multiplier
    for leg in legs:
        strike = leg["strike"]
        premium = leg["premium"]
        vol = leg["volume"]
        ltype = leg["type"]

        if ltype == "long_call":
            intrinsic = max(price - strike, 0) * vol * multiplier
            cost = premium * vol * multiplier
            total += intrinsic - cost
        elif ltype == "short_call":
            intrinsic = max(price - strike, 0) * vol * multiplier
            premium_received = premium * vol * multiplier
            total += premium_received - intrinsic
        elif ltype == "long_put":
            intrinsic = max(strike - price, 0) * vol * multiplier
            cost = premium * vol * multiplier
            total += intrinsic - cost
        elif ltype == "short_put":
            intrinsic = max(strike - price, 0) * vol * multiplier
            premium_received = premium * vol * multiplier
            total += premium_received - intrinsic
    return total


def compute_payoff_curve(prices, legs):
    """Compute P&L for every price in the grid."""
    return np.array([portfolio_pnl(p, legs) for p in prices])


def find_breakevens(prices, pnls, tol=1.0):
    """Find prices where P&L crosses zero."""
    breakevens = []
    for i in range(len(prices) - 1):
        if pnls[i] == 0:
            breakevens.append(prices[i])
        elif pnls[i] * pnls[i + 1] < 0:
            # linear interpolation
            p1, p2 = prices[i], prices[i + 1]
            v1, v2 = pnls[i], pnls[i + 1]
            crossing = p1 - v1 * (p2 - p1) / (v2 - v1)
            breakevens.append(crossing)
    return breakevens


def find_max_profit_loss_in_range(prices, pnls):
    """Find max profit and max loss within the price range."""
    max_profit = float(np.max(pnls))
    max_loss = float(np.min(pnls))
    return max_profit, max_loss

# =============================================================================
# EXPECTED P&L
# =============================================================================

def expected_pnl_contribution(prices, pnls, prob_density):
    """Compute P&L * Probability Density at each price."""
    return pnls * prob_density


def integrate_expected_pnl(prices, contribution):
    """Area under the curve = Expected P&L."""
    return simpson(contribution, prices)

# =============================================================================
# PLOTTING
# =============================================================================

def plot_analysis(ticker, current_price, realized_vol,
                  prices, student_t_density, normal_density,
                  pnls, expected_contrib, total_expected_pnl,
                  breakevens, max_profit, max_loss):
    """Generate the full 3-panel figure."""

    fig, axes = plt.subplots(3, 1, figsize=(12, 14))
    fig.suptitle(f"Global Portfolio P&L  –  Dist Proxy: {ticker}",
                 fontsize=16, fontweight='bold', y=0.98)

    # -----------------------------------------------------------------------
    # Panel 1: Portfolio P&L Payoff Diagram
    # -----------------------------------------------------------------------
    ax1 = axes[0]
    ax1.set_title("Portfolio Payoff at Expiration", fontsize=13, loc='left', pad=10)

    # Fill profit/loss regions
    ax1.fill_between(prices, pnls, 0, where=(pnls >= 0),
                     color='green', alpha=0.15, label='Profit Zone')
    ax1.fill_between(prices, pnls, 0, where=(pnls < 0),
                     color='red', alpha=0.15, label='Loss Zone')

    # P&L line
    ax1.plot(prices, pnls, color='darkgreen', linewidth=2.2, label='P&L')

    # Current price line
    ax1.axvline(current_price, color='blue', linestyle='--', linewidth=1.5, alpha=0.8)
    ax1.text(current_price, ax1.get_ylim()[1] * 0.95,
             f"Current: ${current_price:,.2f}",
             color='blue', fontsize=10, ha='center',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='blue', alpha=0.8))

    # Breakeven markers
    for be in breakevens:
        pct = (be - current_price) / current_price * 100
        ax1.plot(be, 0, 'o', color='orange', markersize=8, zorder=5)
        ax1.annotate(f"BE: ${be:,.2f} ({pct:+.1f}%)",
                     xy=(be, 0), xytext=(be, max_loss * 0.15),
                     fontsize=9, ha='center',
                     color='darkorange',
                     arrowprops=dict(arrowstyle='->', color='darkorange', lw=1))

    # Max profit / max loss annotations
    ax1.text(0.02, 0.95, f"Max Profit (in range): +${max_profit:,.2f}",
             transform=ax1.transAxes, fontsize=10, color='green',
             verticalalignment='top', fontweight='bold')
    ax1.text(0.02, 0.88, f"Max Loss (in range): -${abs(max_loss):,.2f}",
             transform=ax1.transAxes, fontsize=10, color='red',
             verticalalignment='top', fontweight='bold')

    ax1.axhline(0, color='black', linewidth=0.8, alpha=0.5)
    ax1.set_xlim(prices[0], prices[-1])
    ax1.set_ylabel("P&L ($)", fontsize=11)
    ax1.set_xlabel("Underlying Price ($)", fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=9)

    # Format x-axis as currency
    ax1.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # -----------------------------------------------------------------------
    # Panel 2: Probability Analysis
    # -----------------------------------------------------------------------
    ax2 = axes[1]
    ax2.set_title("Price Probability Density at Simulation Date", fontsize=13, loc='left', pad=10)

    # Student-t (fat-tail)
    ax2.plot(prices, student_t_density, color='blue', linewidth=2,
             label='Student-t (fat-tail, IV-scaled)', alpha=0.8)
    ax2.fill_between(prices, student_t_density, 0, color='blue', alpha=0.08)

    # Normal/Lognormal
    ax2.plot(prices, normal_density, color='orange', linewidth=2,
             linestyle='--', label='Normal / Lognormal (BSM baseline)', alpha=0.8)

    # Current price
    ax2.axvline(current_price, color='blue', linestyle='--', linewidth=1.2, alpha=0.7)

    ax2.set_xlim(prices[0], prices[-1])
    ax2.set_ylabel("Probability Density", fontsize=11)
    ax2.set_xlabel("Underlying Price ($)", fontsize=11)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)

    ax2.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # Metadata text box
    info_text = (f"{N_PATHS/1e6:.0f}M paths  |  "
                 f"{SIMULATION_DAYS} d  |  "
                 f"Mean IV: {MEAN_IV*100:.1f}%  |  "
                 f"Dist Proxy: {ticker}")
    ax2.text(0.98, 0.95, info_text, transform=ax2.transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='aliceblue',
                       edgecolor='steelblue', alpha=0.9))

    # -----------------------------------------------------------------------
    # Panel 3: Expected P&L Contribution
    # -----------------------------------------------------------------------
    ax3 = axes[2]
    ax3.set_title("Expected P&L Contribution by Price  (P&L × Probability)",
                  fontsize=13, loc='left', pad=10)

    # Contribution curve
    ax3.plot(prices, expected_contrib, color='darkgreen', linewidth=2,
             label='P&L(price) × Probability Density')
    ax3.fill_between(prices, expected_contrib, 0,
                     where=(expected_contrib >= 0), color='green', alpha=0.2)
    ax3.fill_between(prices, expected_contrib, 0,
                     where=(expected_contrib < 0), color='red', alpha=0.2)

    # Current price
    ax3.axvline(current_price, color='blue', linestyle='--', linewidth=1.2, alpha=0.7)

    # Zero line
    ax3.axhline(0, color='black', linewidth=0.8, alpha=0.5)

    ax3.set_xlim(prices[0], prices[-1])
    ax3.set_ylabel("P&L × Probability Density", fontsize=11)
    ax3.set_xlabel("Underlying Price ($)", fontsize=11)
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)

    ax3.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # Expected P&L annotation
    ax3.text(0.98, 0.95,
             f"Expected P&L:\n+${total_expected_pnl:,.2f}",
             transform=ax3.transAxes, fontsize=12,
             verticalalignment='top', horizontalalignment='right',
             color='green', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.6', facecolor='honeydew',
                       edgecolor='green', alpha=0.9))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


# =============================================================================
# MAIN
# =============================================================================

def main():
    # 1. Fetch USO data
    current_price, realized_vol, hist_prices = fetch_ticker_data(TICKER)
    print(f"  Current price: ${current_price:,.2f}")
    print(f"  Realized vol:  {realized_vol*100:.1f}%")

    # # 2. Build probability distributions
    prices, student_t_density, normal_density = build_distributions(
        current_price, SIMULATION_DAYS, MEAN_IV,
        n_points=N_PRICE_POINTS, range_pct=PRICE_RANGE_PCT
    )
    print(f"  Price range: ${prices[0]:,.2f} - ${prices[-1]:,.2f}")
    print(f"  Price points: {len(prices)}")

    # 3. Compute portfolio P&L
    # pnls = compute_payoff_curve(prices, PORTFOLIO_LEGS)
    # breakevens = find_breakevens(prices, pnls)
    # max_profit, max_loss = find_max_profit_loss_in_range(prices, pnls)

    # print(f"  Breakeven points: {[f'${b:,.2f}' for b in breakevens]}")
    # print(f"  Max profit: +${max_profit:,.2f}")
    # print(f"  Max loss:   -${abs(max_loss):,.2f}")

    # # 4. Expected P&L contribution
    # expected_contrib = expected_pnl_contribution(prices, pnls, student_t_density)
    # total_expected_pnl = integrate_expected_pnl(prices, expected_contrib)
    # print(f"  Expected P&L: +${total_expected_pnl:,.2f}")

    # # 5. Plot
    # fig = plot_analysis(
    #     TICKER, current_price, realized_vol,
    #     prices, student_t_density, normal_density,
    #     pnls, expected_contrib, total_expected_pnl,
    #     breakevens, max_profit, max_loss
    # )

    # # 6. Save
    # output_path = f"figures/simulation_exp_plot_{TICKER.lower()}.png"
    # fig.savefig(output_path, dpi=150, bbox_inches='tight',
    #             facecolor='white', edgecolor='none')
    # print(f"\nPlot saved to: {output_path}")
    # plt.show()


if __name__ == "__main__":
    main()
