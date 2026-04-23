"""
Visualize Kahneman's value function (Prospect Theory) applied to thick-tailed
and thin-tailed distributions, mimicking the structure of nnt_fat_tail.png.

This script generates a figure with three panels:
1. S(x) - Kahneman's value function
2. Distribution of X (Student's t with df=3 for thick tails)
3. Distribution of S(x) - the transformed distribution

The layout mimics one row of nnt_fat_tail.png.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def kahneman_value(x, alpha=0.88, beta=0.88, lam=2.25):
    """
    Kahneman & Tversky prospect theory value function.

    Parameters
    ----------
    x : float or np.ndarray
        Outcome relative to reference point (usually 0).
    alpha : float
        Curvature parameter for gains (x >= 0). Typical value ~0.88.
    beta : float
        Curvature parameter for losses (x < 0). Typical value ~0.88.
    lam : float
        Loss aversion coefficient. Typical value ~2.25.

    Returns
    -------
    float or np.ndarray
        Subjective value of x.
    """
    x = np.asarray(x)
    result = np.empty_like(x, dtype=float)
    # Gains: concave (risk averse)
    mask_pos = x >= 0
    result[mask_pos] = x[mask_pos] ** alpha
    # Losses: convex (risk seeking), steeper (loss aversion)
    mask_neg = ~mask_pos
    result[mask_neg] = -lam * ((-x[mask_neg]) ** beta)
    return result


def transformed_pdf(s, base_pdf, alpha=0.88, beta=0.88, lam=2.25):
    """
    Compute the PDF of S = v(X) where v is Kahneman's value function,
    using the change-of-variables formula.

    base_pdf should accept an array of x-values and return the PDF.
    """
    s = np.asarray(s)
    result = np.zeros_like(s, dtype=float)

    # s > 0  =>  x = s**(1/alpha)
    mask_pos = s > 0
    sp = s[mask_pos]
    xp = sp ** (1.0 / alpha)
    dx_ds = (1.0 / alpha) * sp ** ((1.0 / alpha) - 1.0)
    result[mask_pos] = base_pdf(xp) * dx_ds

    # s < 0  =>  x = -(-s/lam)**(1/beta)
    mask_neg = s < 0
    sn = s[mask_neg]
    xn = -((-sn / lam) ** (1.0 / beta))
    dx_ds = (1.0 / (beta * lam)) * ((-sn / lam) ** ((1.0 / beta) - 1.0))
    result[mask_neg] = base_pdf(xn) * dx_ds

    # s == 0 contributes zero density because of the kink / infinite slope
    return result


def plot_kahneman_value_fat_tail(
    alpha=0.88,
    beta=0.88,
    lam=2.25,
    xlim=(-8, 8),
    n_points=2000,
    output_path="figures/kahneman_value_thick_tail.png",
):
    """
    Generate a 1x3 figure mimicking one row of nnt_fat_tail.png:
      - S(x)  (Kahneman value function)
      - Distribution of X  (Student's t, df=3)
      - Distribution of S(x)
    """
    # --- 1. Grid for X ---
    x = np.linspace(xlim[0], xlim[1], n_points)

    # --- 2. Base distribution: thick-tailed (Student's t, df=3) ---
    df = 3
    base_dist = stats.t(df=df, loc=0, scale=1)
    pdf_x = base_dist.pdf(x)

    # --- 3. Value function S(x) ---
    s_x = kahneman_value(x, alpha=alpha, beta=beta, lam=lam)

    # --- 4. Transformed distribution S(x) ---
    # Determine appropriate s-range based on transformation of x-range
    s_min = kahneman_value(np.array([xlim[0]]), alpha, beta, lam)[0]
    s_max = kahneman_value(np.array([xlim[1]]), alpha, beta, lam)[0]
    s = np.linspace(s_min, s_max, n_points)
    pdf_s = transformed_pdf(s, base_dist.pdf, alpha=alpha, beta=beta, lam=lam)

    # --- 5. Plotting ---
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    # Panel 1: S(x)
    ax = axes[0]
    ax.plot(x, s_x, color="darkorange", linewidth=2.2)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="-")
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title("S(x)", fontsize=13)
    ax.set_xlim(xlim)
    ax.set_ylim(s_min * 1.1, s_max * 1.1)
    ax.set_xlabel("x")
    ax.set_ylabel("S(x)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 2: Distribution of X
    ax = axes[1]
    ax.plot(x, pdf_x, color="blue", linewidth=2.2)
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title("Distribution of X", fontsize=13)
    ax.set_xlim(xlim)
    ax.set_ylim(0, max(pdf_x) * 1.15)
    ax.set_xlabel("x")
    ax.set_ylabel("Density")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Panel 3: Distribution of S(x)
    ax = axes[2]
    ax.plot(s, pdf_s, color="red", linewidth=2.2)
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title("Distribution of S(x)", fontsize=13)
    ax.set_xlim(s_min * 1.1, s_max * 1.1)
    ax.set_ylim(0, max(pdf_s) * 1.15)
    ax.set_xlabel("S(x)")
    ax.set_ylabel("Density")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure to {output_path}")


if __name__ == "__main__":
    # Ensure output directory exists
    import os

    os.makedirs("figures", exist_ok=True)

    # Generate the requested figure (thick tail + Kahneman value function)
    plot_kahneman_value_fat_tail(
        output_path="figures/kahneman_value_thick_tail.png"
    )
