import pandas as pd
import numpy as np
import base64
from io import BytesIO
from langchain_community.tools import tool
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple, Optional, Union

def get_basic_statistics(ts: pd.DataFrame):
    stats = {
        "num_rows": ts.shape[0],
        "num_columns": ts.shape[1],
        "columns": list(ts.columns),
        "dtypes": ts.dtypes.astype(str).to_dict(),
        "mean_per_column": ts.mean(numeric_only=True).to_dict(),
        "std_per_column": ts.std(numeric_only=True).to_dict(),
        "min_per_column": ts.min(numeric_only=True).to_dict(),
        "max_per_column": ts.max(numeric_only=True).to_dict(),
    }
    return stats

class PlotViewer:
    def __init__(self, ts: pd.DataFrame, sync_callback=None) -> None:
        """Initialize a PlotViewer instance for time series visualization.

        Args:
            ts (pd.DataFrame): The time series data to visualize. Must be a pandas DataFrame
                             where each column represents a different channel/variable.
            sync_callback (callable, optional): Callback function to sync view changes with frontend.
                                               Should accept (start_idx, end_idx) parameters.

        The viewer automatically calculates initial view ranges and maintains state for:
        - X-axis view range (index-based)
        - Y-axis view range for each column
        - Guidelines for both axes
        - Zoom state
        """
        self.ts = ts
        self.len_ts = self.ts.shape[0]
        ts_y_range = ts.max(axis='index')-ts.min(axis='index')
        self.y_init_range = {col: [ts.min(axis='index')[col]-0.1*ts_y_range[col], ts.max(axis='index')[col]+0.1*ts_y_range[col]] for col in ts.columns.values.tolist()}
        self.current_x_view_range = [0, self.len_ts]
        self.x_init_range = [0, self.len_ts]
        self.x_guidelines = []
        self.y_guidelines = {}
        self.y_zoomed = False
        self.max_window_size = 500
        self.nb_channels = ts.shape[1]
        self.sync_callback = sync_callback

    def _sync_view_range(self, x_view_range: List[int]) -> None:
        """Sync the current view range with the frontend if callback is available"""
        if self.sync_callback:
            self.sync_callback(x_view_range[0], x_view_range[1])

    def _plot_window(self, x_view_range: List[int], y_view_range: Dict[str, List[float]]) -> str:
        """Plots a windowed segment of the time series data and returns the plot as a base64-encoded PNG image.

        Args:
            x_view_range (List[int]): A list [start_idx, end_idx] specifying the range of indices to plot along the x-axis.
            y_view_range (Dict[str, List[float]]): A dictionary mapping column names to [ymin, ymax] lists specifying 
                                                  the y-axis limits for each column.

        Returns:
            str: A base64-encoded string representing the PNG image of the plotted window.

        Notes:
            - The function creates a subplot for each column in the selected window of the time series.
            - The x-axis is shared among all subplots.
            - The resulting plot is not saved to disk but is encoded in base64 for further use (e.g., embedding in HTML).
        """

        window_ts = self.ts.iloc[x_view_range[0]: x_view_range[1]]
        fig, axes = plt.subplots(window_ts.shape[1], 1, figsize=(14, 3 * window_ts.shape[1]), sharex=True)
        if window_ts.shape[1] == 1:
            axes = [axes]
        for i, col in enumerate(window_ts.columns):
            axes[i].plot(window_ts.index, window_ts[col], label=col)
            axes[i].set_ylabel(col)
            ylim_min = y_view_range[col][0]
            ylim_max = y_view_range[col][1]
            if ylim_min==ylim_max:
                ylim_min = ylim_min - 1
                ylim_max = ylim_max + 1
            axes[i].set_ylim(ylim_min, ylim_max)
            axes[i].tick_params(axis='x', which='both', labelbottom=True)
            axes[i].grid(True)
        axes[-1].set_xlabel('Index')
        plt.tight_layout()
        # fig.savefig('test.png')

        # Encode the figure to base64 without saving to disk
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        fig_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        return fig_base64
    
    def _plot_window_with_ranges(self, x_view_range: List[int], y_zoomed: Union[bool, dict]) -> str:
        """Plot a window of time series data with dynamic y-axis range adjustment.

        This method plots the time series data within the specified x-axis range and adjusts
        the y-axis range based on the zoom state.

        Args:
            x_view_range (List[int]): A list containing [start_idx, end_idx] specifying 
                                    the range for the x-axis (time/index) window to plot.

        Returns:
            str: A base64-encoded string of the plotted figure.

        Notes:
            - If self.y_zoomed is True, the y-axis range is set to slightly beyond the min and max values 
              of the data in the window for each column, providing a zoomed-in view.
            - If self.y_zoomed is False, the initial y-axis range (self.y_init_range) is used.
            - Updates self.current_x_view_range to the provided x_view_range.
        """
        # Update current view range and sync with frontend
        self.current_x_view_range = x_view_range
        self._sync_view_range(x_view_range)

        ts_window = self.ts.iloc[x_view_range[0]: x_view_range[1]]
        ts_window_y_range = ts_window.max(axis='index') - ts_window.min(axis='index')
        if y_zoomed is True:
            y_view_range = {col: [ts_window.min(axis='index')[col]-0.1*ts_window_y_range[col], ts_window.max(axis='index')[col]+0.1*ts_window_y_range[col]] for col in ts_window.columns.values.tolist()}
        else:
            y_view_range = self.y_init_range
        self.y_zoomed = y_zoomed
        fig = self._plot_window(x_view_range, y_view_range)
        self.current_x_view_range = x_view_range
        return fig
    
    def _get_description(self) -> str:
        """Generate a structured description of the current window of time series data.

        Returns:
            str: A structured description optimized for LLM understanding
        """
        ts = self.ts[self.current_x_view_range[0]:self.current_x_view_range[1]]
        
        # Build structured description
        desc_parts = []
        
        # Window information
        desc_parts.append(f"WINDOW: [{ts.index[0]}, {ts.index[-1]}] ({ts.index[-1] - ts.index[0] + 1} points)")
        
        # Position context
        if ts.index[0] == 0:
            desc_parts.append("POSITION: At beginning of dataset")
        elif ts.index[-1] >= self.len_ts - 1:
            desc_parts.append("POSITION: At end of dataset")
        else:
            points_before = ts.index[0]
            points_after = self.len_ts - ts.index[-1] - 1
            desc_parts.append(f"POSITION: {points_before} points before, {points_after} points after")
        
        # Y-axis zoom state
        zoom_status = "ZOOMED" if self.y_zoomed else "UNZOOMED"
        desc_parts.append(f"Y_AXIS: {zoom_status} (adapted to {'window' if self.y_zoomed else 'full dataset'})")
        
        # Channel ranges
        channel_ranges = []
        for col in ts.columns.values.tolist():
            min_val = ts[col].min()
            max_val = ts[col].max()
            channel_ranges.append(f"{col}: [{min_val:.3f}, {max_val:.3f}]")
        
        desc_parts.append(f"CHANNEL_RANGES: {'; '.join(channel_ranges)}")
        
        return "\n".join(desc_parts)

    def _get_description_global(self) -> str:
        """Generate a structured description of the entire time series dataset.

        Returns:
            str: A structured description of the complete dataset
        """
        ts_min = self.ts.min(axis='index')
        ts_max = self.ts.max(axis='index')
        
        # Build structured description
        desc_parts = []
        
        # Dataset overview
        desc_parts.append(f"DATASET: Complete time series ({self.len_ts} total points)")
        desc_parts.append(f"X_RANGE: [0, {self.len_ts-1}]")
        
        # Channel ranges
        channel_ranges = []
        for col in self.ts.columns.values.tolist():
            min_val = ts_min[col]
            max_val = ts_max[col]
            channel_ranges.append(f"{col}: [{min_val:.3f}, {max_val:.3f}]")
        
        desc_parts.append(f"CHANNEL_RANGES: {'; '.join(channel_ranges)}")
        
        return "\n".join(desc_parts)
    
    # @tool(response_format='content_and_artifact')
    def plot_all(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """
        Plot the entire time series data.
        """

        fig = self._plot_window(x_view_range=self.x_init_range, y_view_range=self.y_init_range)
        desc = self._get_description_global()
        
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_window(self, start: int, end: int, y_zoomed: bool) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Plot a specific window of the time series data given the starting and ending index of the window.

        Args:
            start (int): The starting index of the window to plot (inclusive).
            end (int): The ending index of the window to plot (exclusive).
        """
        fig = self._plot_window_with_ranges([start, end], y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_window_with_window_size(self, mid_idx: int, window_size: int, y_zoomed:bool) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Plot a window of time series data centered around a specific index.

        Args:
            mid_idx (int): The center index of the window.
            window_size (int): The size of the window (number of data points).
        """
        x_view_range = [mid_idx-window_size//2, mid_idx+window_size//2]
        if x_view_range[0]<0:
            x_view_range = [0, 2*window_size]
            if x_view_range[1]>self.len_ts:
                x_view_range[1] = self.len_ts
        if x_view_range[1]>self.len_ts:
            x_view_range = [self.len_ts-2*window_size, self.len_ts]
            if x_view_range[0]<0:
                x_view_range[0]=0
        fig = self._plot_window_with_ranges(x_view_range, y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    def plot_derivative(self, channels: List[str]) -> Tuple[str, Dict[str, Union[str, str]]]:
        """
        Plot the selected channels and their derivatives for the current window.

        Args:
            channels (List[str]): List of channel names to plot.

        Returns:
            Dict[str, str]: Dictionary with 'desc' (description) and 'fig' (base64-encoded PNG).
        """
        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        fig, axes = plt.subplots(len(channels)*2, 1, figsize=(14, 3*2*len(channels)), sharex=True)
        ts_window_y_range = window_ts.max(axis='index') - window_ts.min(axis='index')
        if self.y_zoomed is True:
            y_view_range = {col: [window_ts.min(axis='index')[col]-0.1*ts_window_y_range[col], window_ts.max(axis='index')[col]+0.1*ts_window_y_range[col]] for col in window_ts.columns.values.tolist()}
        else:
            y_view_range = self.y_init_range
        for i, col in enumerate(channels):
            if col not in self.ts.columns:
                raise ValueError(f"Channel '{col}' not found in the time series data. Please check the input channel name.")
            axe_raw = axes[i*2]
            axe_raw.plot(window_ts.index, window_ts[col], label=col)
            axe_raw.set_ylabel(col)
            ylim_min, ylim_max = y_view_range[col][0], y_view_range[col][1]
            if ylim_min == ylim_max:
                ylim_min = ylim_min - np.abs(ylim_min)/10
                ylim_max = ylim_max + np.abs(ylim_max)/10
            axe_raw.set_ylim(ylim_min, ylim_max)
            axe_raw.tick_params(axis='x', which='both', labelbottom=True)
            axe_raw.grid(True)

            derivative = np.gradient(window_ts[col])
            ax_deriv = axes[i*2+1]
            ax_deriv.plot(window_ts.index, derivative, label=f"{col} (derivative)", color="orange")
            ax_deriv.set_ylabel(f"{col} (derivative)")
            ax_deriv.set_xlabel("Index")
            # Set y range for derivative with 10% margin
            dmin = np.min(derivative)
            dmax = np.max(derivative)
            dmargin = 0.1 * (dmax - dmin) if dmax > dmin else 1.0
            ax_deriv.set_ylim(dmin - dmargin, dmax + dmargin)
            ax_deriv.tick_params(axis='x', which='both', labelbottom=True)
            ax_deriv.grid(True)
        axes[-1].set_xlabel('Index')

        plt.tight_layout()
        # fig.savefig('test.png')

        # Encode the figure to base64 without saving to disk
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        fig_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        desc = f"DERIVATIVE_PLOT: Window [{window_ts.index[0]}, {window_ts.index[-1]}] | Channels: {', '.join(channels)} | Shows raw data + first derivatives"
        return {'desc': desc, 'fig':fig_base64}


    def plot_second_derivative(self, channels: List[str]) -> Dict[str, str]:
        """
        Plot the selected channels and their second derivatives for the current window.

        Args:
            channels (List[str]): List of channel names to plot.

        Returns:
            Dict[str, str]: Dictionary with 'desc' (description) and 'fig' (base64-encoded PNG).
        """
        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        fig, axes = plt.subplots(len(channels)*2, 1, figsize=(14, 3*2*len(channels)), sharex=True)
        ts_window_y_range = window_ts.max(axis='index') - window_ts.min(axis='index')
        if self.y_zoomed is True:
            y_view_range = {col: [window_ts.min(axis='index')[col]-0.1*ts_window_y_range[col], window_ts.max(axis='index')[col]+0.1*ts_window_y_range[col]] for col in window_ts.columns.values.tolist()}
        else:
            y_view_range = self.y_init_range
        for i, col in enumerate(channels):
            if col not in self.ts.columns:
                raise ValueError(f"Channel '{col}' not found in the time series data. Please check the input channel name.")
            axe_raw = axes[i*2]
            axe_raw.plot(window_ts.index, window_ts[col], label=col)
            axe_raw.set_ylabel(col)
            ylim_min, ylim_max = y_view_range[col][0], y_view_range[col][1]
            if ylim_min == ylim_max:
                ylim_min = ylim_min - np.abs(ylim_min)/10
                ylim_max = ylim_max + np.abs(ylim_max)/10
            axe_raw.set_ylim(ylim_min, ylim_max)
            axe_raw.tick_params(axis='x', which='both', labelbottom=True)
            axe_raw.grid(True)

            # Compute second derivative
            second_derivative = np.gradient(np.gradient(window_ts[col]))
            ax_second_deriv = axes[i*2+1]
            ax_second_deriv.plot(window_ts.index, second_derivative, label=f"{col} (second derivative)", color="green")
            ax_second_deriv.set_ylabel(f"{col} (second derivative)")
            ax_second_deriv.set_xlabel("Index")
            # Set y range for second derivative with 10% margin
            dmin = np.min(second_derivative)
            dmax = np.max(second_derivative)
            dmargin = 0.1 * (dmax - dmin) if dmax > dmin else 1.0
            ax_second_deriv.set_ylim(dmin - dmargin, dmax + dmargin)
            ax_second_deriv.tick_params(axis='x', which='both', labelbottom=True)
            ax_second_deriv.grid(True)
        axes[-1].set_xlabel('Index')

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        fig_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        desc = f"SECOND_DERIVATIVE_PLOT: Window [{window_ts.index[0]}, {window_ts.index[-1]}] | Channels: {', '.join(channels)} | Shows raw data + second derivatives"
        return {'desc': desc, 'fig': fig_base64}
    
    # @tool(response_format='content_and_artifact')
    def plot_zoom_in_x(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Zoom in on the x-axis by reducing the window size.

        This tool creates a new view with a window size that's half the current size,
        centered on the current window's center point.
        """
        window_size = self.current_x_view_range[1]-self.current_x_view_range[0]
        x_view_range = [self.current_x_view_range[0]+window_size//4, self.current_x_view_range[1]-window_size//4]
        fig = self._plot_window_with_ranges(x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_zoom_out_x(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Zoom out on the x-axis by increasing the window size.

        This tool creates a new view with a window size that's double the current size,
        centered on the current window's center point. The window size is adjusted if it
        would exceed the data boundaries.
        """
        window_size = self.current_x_view_range[1]-self.current_x_view_range[0]
        x_view_range = [self.current_x_view_range[0]-window_size//2, self.current_x_view_range[1]+window_size//2]
        if x_view_range[0]<0:
            x_view_range = [0, 2*window_size]
            if x_view_range[1]>self.len_ts:
                x_view_range[1] = self.len_ts
        if x_view_range[1]>self.len_ts:
            x_view_range = [self.len_ts-2*window_size, self.len_ts]
            if x_view_range[0]<0:
                x_view_range[0]=0
        fig = self._plot_window_with_ranges(x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_zoom_out_y(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Reset the y-axis range to show the full data range.

        This tool switches to showing the entire data range on the y-axis instead
        of the current window's range.
        """
        if not self.y_zoomed:
            return {'desc': 'STATUS: Already zoomed out (y-axis shows full dataset range)'}
        self.y_zoomed = False
        fig = self._plot_window_with_ranges(self.current_x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    def plot_with_y_ranges(self, y_ranges: List[Dict]):
        # INSERT_YOUR_CODE
        """
        Plot the current time series window with custom y-axis ranges for each channel.

        Args:
            y_ranges (List[Dict]): A list of dictionaries specifying the y-axis range for each channel/column.
                Each dictionary should map the column name to a list or tuple of [ymin, ymax].

        Returns:
            dict: A dictionary containing:
                - 'desc': A description of the plot or current view.
                - 'fig': The matplotlib figure object of the plot.
        """
        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        for col in y_ranges:
            low = y_ranges[col][0]
            high = y_ranges[col][1]
            span = high-low
            y_ranges[col][0], y_ranges[col][1] = low-0.05*span, high+0.05*span

        fig, axes = plt.subplots(window_ts.shape[1], 1, figsize=(14, 3 * window_ts.shape[1]), sharex=True)
        if window_ts.shape[1] == 1:
            axes = [axes]
        for i, col in enumerate(window_ts.columns):
            axes[i].plot(window_ts.index, window_ts[col], label=col)
            axes[i].set_ylabel(col)
            ylim_min = y_ranges[col][0]
            ylim_max = y_ranges[col][1]
            if ylim_min==ylim_max:
                ylim_min = ylim_min - 1
                ylim_max = ylim_max + 1
            axes[i].set_ylim(ylim_min, ylim_max)
            axes[i].tick_params(axis='x', which='both', labelbottom=True)
            axes[i].grid(True)
        axes[-1].set_xlabel('Index')
        plt.tight_layout()
        # fig.savefig('test.png')

        # Encode the figure to base64 without saving to disk
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        fig_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

        # Create custom description for custom y-ranges
        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        desc_parts = []
        desc_parts.append(f"CUSTOM_Y_RANGES: Window [{window_ts.index[0]}, {window_ts.index[-1]}]")
        desc_parts.append("Y_AXIS: Custom ranges applied")
        
        # Add custom range info
        custom_ranges = []
        for col, range_vals in y_ranges.items():
            custom_ranges.append(f"{col}: [{range_vals[0]:.3f}, {range_vals[1]:.3f}]")
        desc_parts.append(f"CUSTOM_RANGES: {'; '.join(custom_ranges)}")
        
        desc = "\n".join(desc_parts)
        return {'desc': desc, 'fig': fig_base64}
    
    # @tool(response_format='content_and_artifact')
    def plot_zoom_in_y(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Adjust the y-axis range to focus on the current window's data range.

        This tool adapts the y-axis limits to show only the range of values
        present in the current window, providing a more detailed view of the data.
        """
        if self.y_zoomed:
            return {'desc': 'STATUS: Already zoomed in (y-axis adapted to window data)'}
        self.y_zoomed = True
        fig = self._plot_window_with_ranges(self.current_x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_left(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Move the view window to the left by 3/4 window width.

        This tool shifts the current view window to the left by 3/4 window width,
        maintaining the same window size. It handles boundary conditions when reaching
        the start of the data.
        """
        window_size = self.current_x_view_range[1]-self.current_x_view_range[0]
        x_view_range = [
            self.current_x_view_range[0]-int(window_size/4*3), 
            self.current_x_view_range[1]-int(window_size/4*3)
        ]
        if x_view_range[0]<0:
            x_view_range = [0, window_size]
        if x_view_range[1]>self.len_ts:
            x_view_range = [self.len_ts-window_size, self.len_ts]
        fig = self._plot_window_with_ranges(x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}
    
    # @tool(response_format='content_and_artifact')
    def plot_right(self) -> Tuple[str, Dict[str, Union[str, str]]]:
        """Move the view window to the right by 3/4 window width.

        This tool shifts the current view window to the right by 3/4 window width,
        maintaining the same window size. It handles boundary conditions when reaching
        the end of the data.
        """
        window_size = self.current_x_view_range[1]-self.current_x_view_range[0]
        x_view_range = [
            self.current_x_view_range[0]+int(window_size/4*3), 
            self.current_x_view_range[1]+int(window_size/4*3)
        ]
        if x_view_range[0]<0:
            x_view_range = [0, window_size]
        if x_view_range[1]>self.len_ts:
            x_view_range = [self.len_ts-window_size, self.len_ts]
        fig = self._plot_window_with_ranges(x_view_range, y_zoomed=self.y_zoomed)
        desc = self._get_description()
        return {'desc': desc, 'fig': fig}

    # @tool(response_format='content')
    def lookup_x(self, x_list: List[int]) -> str:
        """Look up y-values for specific x-indices in the current window. For indices in the window, returns all y-values from all channels.

        Args:
            x_list (List[int]): List of x-indices to look up values for.
        """
        not_in_window_x = []
        in_window_x = []
        for x in x_list:
            if x > self.current_x_view_range[1] or x < self.current_x_view_range[0]:
                not_in_window_x.append(x)
                continue
            y_value = self.ts.iloc[x].to_dict()
            in_window_x.append([x, y_value])

        # Build structured response
        desc_parts = []
        
        if len(in_window_x) > 0:
            desc_parts.append(f"FOUND: {len(in_window_x)} indices in current window")
            for idx, values in in_window_x:
                value_str = ', '.join([f"{k}={v:.3f}" if isinstance(v, (int, float)) else f"{k}={v}" for k, v in values.items()])
                desc_parts.append(f"  Index {idx}: {value_str}")
        else:
            desc_parts.append("FOUND: No indices in current window")
        
        if len(not_in_window_x) > 0:
            desc_parts.append(f"WARNING: {len(not_in_window_x)} indices outside window: {', '.join(map(str, not_in_window_x))}")
        
        desc = "\n".join(desc_parts)
        return {'desc': desc}

    # @tool(response_format='content')
    def lookup_y(self, col: str, y_value: List[float]) -> str:
        """Find x-indices where a channel reaches specific y-values.

        This tool searches the current window for locations where a specific channel
        crosses or equals given y-values. It includes both exact matches and interpolated
        crossings.

        Args:
            col (str): The name of the channel/column to search in.
            y_value (List[float]): List of y-values to find in the data.
        """
        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        channel = window_ts[col]
        indices = {y: [] for y in y_value}
        for y in y_value:
            for idx in range(1, window_ts.shape[0]):
                if channel.iloc[idx] == y:
                    indices[y].append(str(channel.index[idx]))
                if channel.iloc[idx]>y and channel.iloc[idx-1]<y or channel.iloc[idx]<y and channel.iloc[idx-1]>y:
                    x0, y0 = channel.index[idx], channel.iloc[idx]
                    x1, y1 = channel.index[idx-1], channel.iloc[idx-1]
                    if y1 != y0:
                        interp_idx = round(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
                    else:
                        interp_idx = x0
                    indices[y].append(str(interp_idx))
        
        # Build structured response
        desc_parts = []
        
        if len(indices) == 0:
            desc_parts.append(f"FOUND: No crossings for {col}={', '.join(map(str, y_value))}")
        else:
            desc_parts.append(f"FOUND: {sum(len(indices[y]) for y in indices)} crossings for {col}")
            for y in y_value:
                if indices[y]:
                    indices_str = ', '.join(indices[y])
                    desc_parts.append(f"  {col}={y}: x=[{indices_str}]")
                else:
                    desc_parts.append(f"  {col}={y}: No crossings found")
        
        desc = "\n".join(desc_parts)
        return {'desc': desc}

    # @tool(response_format='content')
    def get_value(self):
        """
        Returns a formatted string representation of time series data with smart downsampling.
        This tool provides a string representation of the current time series window. If the window size exceeds
        the maximum allowed size, it automatically downsamples the data while preserving important patterns using
        a downsampling algorithm.
        """

        window_ts = self.ts.iloc[self.current_x_view_range[0]: self.current_x_view_range[1]]
        window_size = self.current_x_view_range[1]-self.current_x_view_range[0]
        # Build structured description
        desc_parts = []
        desc_parts.append(f"DATA_WINDOW: [{window_ts.index[0]}, {window_ts.index[-1]}] ({window_size} points)")
        
        if window_size > self.max_window_size:
            # For simplification, just sample every nth point instead of using lttb
            step = window_size // self.max_window_size
            downsampled_df = window_ts.iloc[::step]
            downsampled_df = downsampled_df.astype(float).round(3)
            
            result = downsampled_df.to_string()
            desc_parts.append("PROCESSING: Downsampled (large window)")
            desc_parts.append("NOTE: Some details may be missing due to downsampling")
        else:
            result = window_ts.to_string()
            desc_parts.append("PROCESSING: Raw data (no downsampling)")
        
        desc_parts.append("DATA:")
        desc_parts.append(result)
        desc = "\n".join(desc_parts)
        return {'desc': desc}

