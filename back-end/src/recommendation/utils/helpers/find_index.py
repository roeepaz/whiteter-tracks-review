import pandas as pd

def find_plot_index(df: pd.DataFrame, plot: dict) -> int:
    """Find the row index of a given plot in the DataFrame.

    Parameters:
        df: DataFrame containing plot data.
        plot: Plot record, must include 'plot_id' and 'system_id' keys.

    Returns:
        Index of the matching plot row in `df`.

    Raises:
        ValueError: If no matching plot is found.
    """
    matches = df[
        (df['plot_id'] == plot['plot_id']) &
        (df['system_id'] == plot['system_id'])
    ]
    if matches.empty:
        raise ValueError(f"Root plot not found: {plot}")
    return matches.index[0]