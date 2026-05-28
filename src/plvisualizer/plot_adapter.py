from abc import ABC, abstractmethod


class PlotAdapterPort(ABC):
    """PORT: Abstract interface for plot rendering.

    Any plotting adapter (matplotlib, plotly, web, etc.) must implement
    this interface. This decouples data preparation from rendering.
    """

    @abstractmethod
    def render(self, plot_data):
        """Render the given plot data.

        Args:
            plot_data: A PlotData object containing curve_points,
                       max_loss_marker, and breakeven_points.
        """
        pass
