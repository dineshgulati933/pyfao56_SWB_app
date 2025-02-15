# =====================================================
# Utility Functions for Flask App - utils.py (Updated)
# =====================================================
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json
import os
import time

plt.rcParams['font.size'] = 16
plt.rcParams['font.family'] = 'Arial'

# Note: The `wb_plot` function is used in the `results.py` file to generate a water balance plot for download and later we are thinking to discard this function and use the `wb_plot_interactive` function instead.
# This is more reptetative and we can use the `wb_plot_interactive` function to generate the plot and save it as an image. This function also does not updated for depletion plot adjustment.

def wb_plot(results, save_plot: bool = False, plot_name: str = 'wb_plot.jpeg', print_wb: bool = False):
    """
    Plots and visualizes different water balance components and optionally saves the plot.

    Parameters:
    -----------
    results : pandas.DataFrame
        A DataFrame containing the water balance data. The DataFrame is expected to have the following columns:
        - Ks: Soil water depletion coefficient
        - ETc: Crop evapotranspiration
        - ETcadj: Adjusted crop evapotranspiration
        - Rain: Rainfall
        - Irrig: Irrigation
        - Runoff: Runoff
        - TAW: Total available water
        - RAW: Readily available water
        - Dr: Depletion of soil water
        - DP: Deep percolation
        - DOY (Day of Year): Day of year, typically used as the index or a column for x-axis.
    
    save_plot : bool, optional, default: False
        If True, the plot will be saved to a file with the specified `plot_name`.

    plot_name : str, optional, default: 'wb_plot.jpeg'
        The filename for the saved plot. The file will be saved in the current working directory.
        Ensure that the `plot_name` includes the appropriate file extension (e.g., '.jpeg', '.png').

    print_wb : bool, optional, default: True
        If True, a summary of the water balance components will be displayed as the plot's title.

    Returns:
    --------
    None
        The function displays the plot in the current output cell (if using a Jupyter notebook) or in a separate window (if using a script).
        If `save_plot` is True, the plot is saved to the specified file.

    Notes:
    ------
    - The `results` DataFrame must contain all the necessary columns; otherwise, the function will raise an error.
    - The plot is composed of three subplots:
        1. The first subplot shows Ks, ETc, and adjusted ETc.
        2. The second subplot shows Rainfall, Irrigation, and Runoff.
        3. The third subplot shows TAW, RAW, soil water depletion, and deep percolation.
    - The function uses a monospaced font for the plot title to ensure proper alignment of the water balance summary.
    """
    sns.set_style('ticks')

    fig, axes = plt.subplots(3, 1, figsize=(16, 9), dpi=250, sharex=True)

    # ===============================================
    # First subplot (Ks, ETc, and adjusted ETc)
    # ===============================================
    axes[0].plot(results.iloc[:, 1], results['Ks'], color='green', ls='--', label='Ks')
    axes[0].set_ylabel('Ks')
    ax01 = axes[0].twinx()
    ax01.plot(results.iloc[:, 1], results['ETc'], color='coral', label='ETc')
    ax01.plot(results.iloc[:, 1], results['ETcadj'], color='olive', label='ETc adj')
    ax01.set_ylabel('ETc & ETc adj (mm)')
    ax01.set_xticks([])

    # ===============================================
    # Second subplot (Rainfall, Irrigation, and Runoff)
    # ===============================================
    axes[1].bar(results.iloc[:, 1], results['Rain'], color='dodgerblue', alpha=0.6, label='Rainfall')
    axes[1].bar(results.iloc[:, 1], results['Irrig'], color='green', alpha=0.6, label='Irrigation')
    axes[1].bar(results.iloc[:, 1], results['Runoff'], color='yellow', label='Runoff')
    axes[1].set_ylabel('Rainfall & Runoff (mm)')
    axes[1].set_xticks([])

    # ===============================================
    # Third subplot (TAW, RAW, soil water depletion, and deep percolation)
    # ===============================================
    axes[2].set_ylim(results['TAW'].iloc[-1] + 10, 0)
    axes[2].plot(results.iloc[:, 1], results['TAW'], color='blue', label='TAW')
    axes[2].plot(results.iloc[:, 1], results['RAW'], color='darkslategrey', lw=2, label='RAW')
    axes[2].plot(results.iloc[:, 1], results['Dr'], color='red', alpha=0.7, label='Dr')
    axes[2].bar(results.iloc[:, 1], results['DP'], color='goldenrod', label='Percolation')
    axes[2].set_xlabel('DOY')
    axes[2].set_ylabel('TAW, RAW, Dr & DP (mm)')

    # ===============================================
    # Set x-ticks at regular intervals (every 10 days, for example)
    # ===============================================
    try:
        x_tic = [day.split('-')[-1] for day in results.iloc[:, 1]]
        tick_positions = range(0, len(x_tic), 10)

        for ax in axes:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels([x_tic[i] for i in tick_positions], rotation=45)
    except Exception as e:
        print(f"An error occurred while setting x-ticks: {e}")
        for ax in axes:
            ax.set_xticks([])

    # ===============================================
    # Collecting all legend handles and labels
    # ===============================================
    handles, labels = [], []

    # First subplot legends (primary and secondary axis)
    h1, l1 = axes[0].get_legend_handles_labels()
    h2, l2 = ax01.get_legend_handles_labels()
    handles.extend(h1 + h2)
    labels.extend(l1 + l2)

    # Second subplot legend
    h3, l3 = axes[1].get_legend_handles_labels()
    handles.extend(h3)
    labels.extend(l3)

    # Third subplot legend
    h4, l4 = axes[2].get_legend_handles_labels()
    handles.extend(h4)
    labels.extend(l4)

    # ===============================================
    # Creating a common legend above the subplots
    # ===============================================
    fig.legend(handles, labels, loc='upper center', ncol=4, bbox_to_anchor=(0.5, 1.0), fontsize=10)

    # ===============================================
    # Print water balance summary in plot title
    # ===============================================
    if print_wb:
        plt.suptitle(f'''ETc = {round(results.ETc.sum(), 2)}, ETc adj = {round(results.ETcadj.sum(), 2)}
Rain = {round(results.Rain.sum(), 2)}, Irrig. = {round(results.Irrig.sum(), 2)}, Irrig. count = {(results['Irrig'] != 0).sum()}
Runoff = {round(results.Runoff.sum(), 2)}, Percolation = {round(results.DP.sum(), 2)}''', fontfamily='monospace')

    plt.tight_layout(rect=[0, 0, 1, 0.94])  # Adjust layout to make space for the title and legend
    # ===============================================
    # Save the plot if required
    # ===============================================
    if save_plot:
        plt.savefig(plot_name, bbox_inches='tight')


    # # Save the plot as a PNG image and encode it to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_img = base64.b64encode(img.getvalue()).decode()

    # plot_html = mpld3.fig_to_html(fig)

    plt.close()
    # Display the plot
    return f'data:image/png;base64,{plot_img}'


# Define the directory to store weather data
DATA_DIR = 'weather_storage'
os.makedirs(DATA_DIR, exist_ok=True)  # Ensure directory exists

def save_weather_data(lat, lon, data):
    '''
    Saves weather data as a JSON file with appropriate formatting and error handling.

    Parameters:
    -----------
    lat : float
        Latitude coordinate for the weather data location.
    lon : float
        Longitude coordinate for the weather data location.
    data : pandas.DataFrame or list of dict
        Weather data to be saved. If it is a DataFrame, it will be converted 
        to a list of dictionaries. NaN values will be replaced with `None`.

    File Format:
    ------------
    The saved JSON file will have the following structure:
    {
        'latitude': <lat>,
        'longitude': <lon>,
        'timestamp': <current_unix_time>,
        'weather_data': [
            {
                'Date': 'YYYY-MM-DD',
                'srad': <float>,
                'tmmx': <float>,
                'tmmn': <float>,
                'rmax': <float>,
                'rmin': <float>,
                'vs': <float>,
                'pr': <float>
            },
            ...
        ]
    }

    File Naming Convention:
    -----------------------
    The file will be saved in the directory specified by `DATA_DIR` 
    with the naming pattern:
        weather_<lat>_<lon>.json

    Example:
    --------
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> df = pd.DataFrame({
    ...     'Date': [datetime(2024, 4, 1), datetime(2024, 4, 2)],
    ...     'srad': [10.5, 11.2],
    ...     'tmmx': [25.5, 26.0],
    ...     'tmmn': [10.5, 11.0],
    ...     'rmax': [80, 85],
    ...     'rmin': [40, 45],
    ...     'vs': [3.5, 3.6],
    ...     'pr': [0.0, 0.5]
    ... })
    >>> save_weather_data(43.60889, -116.19407, df)

    Notes:
    ------
    - This function ensures safe file writing by using a temporary file (`.tmp`) 
      and then renaming it to avoid partial writes or corruption issues.
    - Converts Pandas Timestamp objects to string dates ('YYYY-MM-DD').
    - Converts all `NaN` values from Pandas DataFrames to `None` for JSON compatibility.

    Error Handling:
    ---------------
    - If the file write operation fails due to IO errors or OS errors, 
      the error will be printed.
    - In the event of a failure during the temporary file creation, 
      the temporary file is cleaned up.

    Returns:
    --------
    None
    '''
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)  # Create directory if it doesn't exist

    file_path = os.path.join(DATA_DIR, f'weather_{lat}_{lon}.json')

    # Ensure data['weather_data'] is properly formatted
    if isinstance(data, pd.DataFrame):
        data = data.where(pd.notna(data), None)  # Convert NaN to None
        data = data.to_dict(orient='records')  # Convert DataFrame to list of dictionaries

        # Convert all `Timestamp` values to string ('YYYY-MM-DD')
        for row in data:
            if 'Date' in row and isinstance(row['Date'], pd.Timestamp):
                row['Date'] = row['Date'].strftime('%Y-%m-%d')

    data_json = {}
    data_json['latitude'] = lat
    data_json['longitude'] = lon
    # Add a timestamp while saving file
    data_json['timestamp'] = time.time()
    data_json['weather_data'] = data

    try:
        # **Safe file writing to prevent Windows locking issues**
        temp_file_path = file_path + '.tmp'

        with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
            json.dump(data_json, temp_file, indent=4)

        # Overwrite the original file **after writing is completed**
        os.replace(temp_file_path, file_path)

    except (IOError, OSError) as e:
        print(f'File-related error saving weather data: {e}')

    finally:
        # Explicitly close file handles (if using additional file handling)
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)  # Cleanup if failed



def load_weather_data(lat, lon):
    '''
    Load weather data from a JSON file based on latitude and longitude.

    Parameters:
    -----------
    lat : float
        Latitude coordinate for the weather data location.
    lon : float
        Longitude coordinate for the weather data location.

    File Naming Convention:
    -----------------------
    The function looks for a file named:
        weather_<lat>_<lon>.json
    in the directory specified by `DATA_DIR`.

    Example:
    --------
    >>> data = load_weather_data(43.60889, -116.19407)
    >>> if data:
    ...     print('Weather data loaded successfully')
    ... else:
    ...     print('No weather data available')

    File Format:
    ------------
    The JSON file is expected to have the following structure:
    {
        'latitude': <lat>,
        'longitude': <lon>,
        'timestamp': <float>,         # UNIX timestamp when data was saved
        'weather_data': [
            {
                'Date': 'YYYY-MM-DD',
                'srad': <float>,
                'tmmx': <float>,
                'tmmn': <float>,
                'rmax': <float>,
                'rmin': <float>,
                'vs': <float>,
                'pr': <float>
            },
            ...
        ]
    }

    Returns:
    --------
    dict or None
        - A dictionary containing the weather data if the file exists and is successfully loaded.
        - `None` if the file does not exist.

    Notes:
    ------
    - This function expects that the weather data file is saved using `save_weather_data()`.
    - The file is read and returned as a JSON object.
    - If the file is missing or cannot be found, it returns `None` without raising an error.
    '''
    file_path = os.path.join(DATA_DIR, f'weather_{lat}_{lon}.json')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None  # If no file exists, return None


# =====================================================
# Delete Weather Data

# def delete_weather_data(lat, lon):
#     """ Delete weather data JSON file when the user session ends """
#     file_path = os.path.join(DATA_DIR, f"weather_{lat}_{lon}.json")
#     if os.path.exists(file_path):
#         os.remove(file_path)  # Delete file

def delete_old_files():
    '''
    Deletes weather data files older than 6 hours from the `DATA_DIR`, ensuring they are not in use.

    This function scans the directory for files with names starting with 'weather_',
    reads their timestamps from the JSON content, and deletes them if they are older
    than 6 hours from the current time.

    Parameters:
    -----------
    None

    File Naming Convention:
    -----------------------
    The function targets files named:
        weather_<lat>_<lon>.json

    File Structure:
    ---------------
    {
        'latitude': <float>,
        'longitude': <float>,
        'timestamp': <float>,  # Unix timestamp
        'weather_data': [...]
    }

    Notes:
    ------
    - Uses the file's `timestamp` key to determine its age.
    - Skips files currently in use (raises `PermissionError`).
    - Skips files that are corrupted (invalid JSON).

    Error Handling:
    ---------------
    - If a file is locked (`PermissionError`), it is skipped with a message.
    - If the file cannot be read or is not a proper JSON (`JSONDecodeError`), it is skipped.
    - If the file disappears during the operation (`FileNotFoundError`), it is ignored.

    Returns:
    --------
    None

    Example:
    --------
    >>> delete_old_files()
    Deleted old weather data: /path/to/weather_43.60889_-116.19407.json
    Skipping deletion: /path/to/weather_42.12345_-115.67890.json is still in use.
    '''
    now = time.time()
    six_hours = 6 * 3600  # 6 hours in seconds

    for file in os.listdir(DATA_DIR):
        if file.startswith('weather_'):
            file_path = os.path.join(DATA_DIR, file)

            try:
                # Attempt to open the file before deletion
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Check if file has a timestamp and is older than 6 hours
                if 'timestamp' in data and now - data['timestamp'] > six_hours:
                    try:
                        os.remove(file_path)  # Attempt to delete
                        print(f'Deleted old weather data: {file_path}')
                    except PermissionError:
                        print(f'Skipping deletion: {file_path} is still in use.')

            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                print(f'Error reading or deleting: {file_path} - {e}')

