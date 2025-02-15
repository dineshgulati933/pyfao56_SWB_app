import pandas as pd
from geopy.distance import geodesic
import requests
from io import StringIO

def fetch_daily_data_df(start_date, end_date, stations, parameters):
    '''
    Fetch daily data from USBR\'s Hydromet/AgriMet service as a CSV,
    then read it into a pandas DataFrame.
    '''
    # Use the .pl extension in the URL
    base_url = 'https://www.usbr.gov/pn-bin/daily.pl'
    
    def build_st_par_str(stations, parameters):
        return ','.join(f'{stn} {par}' for stn in stations for par in parameters)

    # Build query parameters
    params = {
        'list': build_st_par_str(stations, parameters), 
        'start': start_date,       # e.g. '2016-04-01'
        'end': end_date,           # e.g. '2016-04-20'
        'format': 'csv'            
    }
    
    # Make the request
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    
    # Convert the text to a file-like object
    data_str = StringIO(response.text)
    
    df = pd.read_csv(data_str)
    df = data_pre_process(df)
    
    return df

def data_pre_process(df):
    df.columns = ['Date', 'srad', 'tmmx', 'tmmn', 'tdew', 'vs', 'pr']
    df['srad'] *= 0.041868 #langleys to MJ/m2/days
    df['tmmx'] = (df['tmmx'] - 32) * (5/9) # F to C
    df['tmmn'] = (df['tmmn'] - 32) * (5/9) # F to C
    df['tdew'] = (df['tdew'] - 32) * (5/9) # F to C
    df['vs'] *= 0.44704 #mph to m/s
    df['pr'] *= 25.4 # inch to mm
    return df

def get_agrimet(lat, lon, buffer_km, start_date):
    """
    Find AgriMet stations within a buffer radius and return sorted list by distance.
    
    Parameters:
    - lat (float): Latitude of the location.
    - lon (float): Longitude of the location.
    - buffer_km (float): Buffer radius in kilometers.
    - planting_date (str): Planting date in 'YYYY-MM-DD' format.

    Returns:
    - list of dicts: Nearby stations sorted by distance.
    """
    start_date = pd.to_datetime(start_date)
    stations_df = pd.read_csv('agmet_stations.csv')
    
    nearby_stations = []

    for _, row in stations_df.iterrows():
        distance = geodesic((lat, lon), (row['latitude'], row['longitude'])).km
        
        if distance <= buffer_km:
            stn = row.to_dict()
            stn['distance'] = round(distance, 2)  # Distance in km

            # Include stations if install date is missing or if installed before planting date
            install_date = pd.to_datetime(stn.get('install'), errors='coerce')

            if pd.isna(install_date) or install_date <= start_date:
                nearby_stations.append(stn)

    # Sort stations by distance
    stations = sorted(nearby_stations, key=lambda x: x['distance'])

    return stations

def get_agrimet_data(stations, start_date, end_date, parameters):
    """
    Retrieve AgriMet data from the nearest available station.
    
    Parameters:
    - stations (list): List of station dictionaries including 'distance'.
    - start_date (str): Start date in 'YYYY-MM-DD' format.
    - end_date (str): End date in 'YYYY-MM-DD' format.
    
    Returns:
    - dict: The weather data from the first successful station.
    - str: The station ID from which data was retrieved.
    """
    
    for station in stations:
        siteid = station['siteid']
        print(f"Attempting to fetch data from {siteid} ({station['distance']} km away)...")
        
        data = fetch_daily_data_df(start_date, end_date, stations=[siteid], parameters=parameters)
        
        if data is not None and not data.empty:
            print(f"Data successfully retrieved from station {siteid}")
            return {
                'station_info': station,
                'weather_data': data
            }
    
    print("No AgriMet data available from any nearby stations.")
    return None


# Example Usage
def fetch_agrimet(lat, lon, start_date, end_date, buffer_km):
    stns = get_agrimet(lat, lon, buffer_km, start_date)
    data_dict = get_agrimet_data(stns, start_date, end_date, parameters=['SR', 'MX', 'MN', 'YM', 'UA', 'PP'])
    return data_dict
