import os

import matplotlib
import matplotlib.pyplot as plt

from src.plvisualizer.plot_adapter import PlotAdapterPort


def _backend_is_interactive():
    """Return True if the current matplotlib backend can display a GUI."""
    backend = matplotlib.get_backend().lower()
    non_interactive = {"agg", "cairo", "pdf", "ps", "svg", "template"}
    return backend not in non_interactive


class MatplotlibPlotAdapter(PlotAdapterPort):
    """Concrete plot adapter using matplotlib.

    Renders P&L curve, breakeven points, and max loss marker.

    In non-interactive environments (e.g. servers, CI, headless Linux)
    the plot is saved to a file instead of displayed with ``plt.show()``.
    """

    DEFAULT_FILENAME = "figures/pl_payoff.png"

    def __init__(self, filename=None):
        """
        Args:
            filename: Path to save the plot image. Defaults to
                      ``figures/pl_payoff.png`` relative to the current
                      working directory.
        """
        self.filename = filename or self.DEFAULT_FILENAME

    def render(self, plot_data):
        """Render plot_data using matplotlib.

        Args:
            plot_data: PlotData object with curve_points, max_loss_marker,
                       and breakeven_points.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract x and y from curve points
        prices = [point[0] for point in plot_data.curve_points]
        pnls = [point[1] for point in plot_data.curve_points]

        # Plot P&L curve
        ax.plot(prices, pnls, label="P&L at Expiration", color="blue", linewidth=2)

        # Plot breakeven points
        if plot_data.breakeven_points:
            for be in plot_data.breakeven_points:
                ax.axvline(x=be, color="green", linestyle="--", alpha=0.7)
                ax.scatter([be], [0], color="green", s=80, zorder=5)
            ax.scatter([], [], color="green", label="Breakeven", s=80)

        # Plot max loss marker
        marker = plot_data.max_loss_marker
        ax.scatter(
            [marker["x"]],
            [marker["y"]],
            color=marker["color"],
            s=120,
            zorder=5,
            label="Max Loss"
        )

        # Horizontal line at zero
        ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)

        ax.set_xlabel("Underlying Price")
        ax.set_ylabel("P&L")
        ax.set_title("P&L Payoff at Expiration")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Always save to file — works in every environment
        output_dir = os.path.dirname(self.filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        fig.savefig(self.filename)
        print(f"P&L plot saved to: {os.path.abspath(self.filename)}")

        # Only try to open a GUI window when an interactive backend is active
        if _backend_is_interactive():
            plt.show()

        plt.close(fig)
