import os

import matplotlib
import matplotlib.pyplot as plt

from src.expplvisualizer.plot_adapter import PlotAdapterPort


def _backend_is_interactive():
    """Return True if the current matplotlib backend can display a GUI."""
    backend = matplotlib.get_backend().lower()
    non_interactive = {"agg", "cairo", "pdf", "ps", "svg", "template"}
    return backend not in non_interactive


def _extract_coordinates(curve_points):
    """Pull out separate lists of prices and P&L values."""
    prices = [point[0] for point in curve_points]
    pnls = [point[1] for point in curve_points]
    return prices, pnls


def _draw_pnl_curve(ax, prices, pnls):
    """Plot the main P&L line in blue."""
    ax.plot(prices, pnls, label="P&L at Expiration", color="blue", linewidth=2)


def _draw_breakeven_points(ax, breakeven_points):
    """Mark each breakeven with a green dashed line and a dot at y=0."""
    if breakeven_points:
        for be in breakeven_points:
            ax.axvline(x=be, color="green", linestyle="--", alpha=0.7)
            ax.scatter([be], [0], color="green", s=80, zorder=5)
        ax.scatter([], [], color="green", label="Breakeven", s=80)


def _draw_max_loss_marker(ax, marker):
    """Draw a large black dot at the worst-loss coordinate."""
    ax.scatter(
        [marker["x"]],
        [marker["y"]],
        color=marker["color"],
        s=120,
        zorder=5,
        label="Max Loss"
    )


def _draw_zero_line(ax):
    """Add a faint horizontal reference line at y=0."""
    ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)


def _apply_labels_and_legend(ax):
    """Set axis labels, title, legend, and grid."""
    ax.set_xlabel("Underlying Price")
    ax.set_ylabel("P&L")
    ax.set_title("P&L Payoff at Expiration")
    ax.legend()
    ax.grid(True, alpha=0.3)


def _save_figure(fig, filename):
    """Persist the figure to disk, creating parent directories if needed."""
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    fig.savefig(filename)
    print(f"P&L plot saved to: {os.path.abspath(filename)}")


def _maybe_show_plot():
    """Open an interactive window only when a GUI backend is available."""
    if _backend_is_interactive():
        plt.show()


def _close_figure(fig):
    """Free matplotlib resources for this figure."""
    plt.close(fig)


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

        prices, pnls = _extract_coordinates(plot_data.curve_points)
        _draw_pnl_curve(ax, prices, pnls)
        _draw_breakeven_points(ax, plot_data.breakeven_points)
        _draw_max_loss_marker(ax, plot_data.max_loss_marker)
        _draw_zero_line(ax)
        _apply_labels_and_legend(ax)

        plt.tight_layout()
        _save_figure(fig, self.filename)
        _maybe_show_plot()
        _close_figure(fig)
