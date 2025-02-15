import pandas as pd
import xarray as xr

'''Note: This class was initially made for general purpose to fetch weather data from gridMET dataset for any location and variables. There are various methods to extract data for a single year, multiple years,
specific date range, and specific date range across multiple years. The unit conversion methods are also provided to convert the units of the fetched data. The unit conversion method for pyfao56 is also provided.
These unit conversion methods are introduced as static methods. The unit conversion method for pyfao56 also adds additional columns to the DataFrame otherwise pyfao56 throws an error. The weather class in pyfao56 expects
these additional columns. In general pyfao56 expects a .wth file for weather parmeters but we are custom loading the data in pyfao56.'''

class WeatherDataFetcher:
    def __init__(self, lat, lon, variables):
        """
        Initializes the WeatherDataFetcher with location and variables.

        Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        variables (list): List of variables to fetch.
        """
        self.lat = lat
        self.lon = lon
        self.variables = variables

    def fetch_yearly_data(self, year):
        """
        Fetches weather data for the specified year.

        Args:
        year (int): Year of the dataset.

        Returns:
        pd.DataFrame: Consolidated dataframe for the year.
        """
        all_data = []
        for var in self.variables:
            url = f'http://thredds.northwestknowledge.net:8080/thredds/dodsC/MET/{var}/{var}_{year}.nc'
            dataset = xr.open_dataset(url)
            data = dataset.sel(lat=self.lat, lon=self.lon, method="nearest")
            df = data.to_dataframe().reset_index()

            if 'time' in df.columns:
                df.rename(columns={'time': 'day'}, inplace=True)

            var_column = df.columns[-1]
            df = df[['day', var_column]]
            df.rename(columns={'day': 'Date', var_column: var}, inplace=True)  # Rename data column to var name

            all_data.append(df)

        # Merge all variables into one DataFrame
        consolidated_df = all_data[0]
        for df in all_data[1:]:
            consolidated_df = consolidated_df.merge(df, on='Date', how='outer')

        return consolidated_df

    def fetch_data_for_years(self, years):
        """
        Fetches weather data for multiple years.

        Args:
        years (list): List of years to fetch data for.

        Returns:
        pd.DataFrame: Consolidated dataframe for all years.
        """
        all_years_data = [self.fetch_yearly_data(year) for year in years]
        consolidated_df = pd.concat(all_years_data, ignore_index=True)
        consolidated_df.sort_values(by='Date', inplace=True)
        return consolidated_df

    def fetch_data_for_date_range(self, start_date, end_date):
        """
        Fetches weather data for a specific date range.

        Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
        pd.DataFrame: Filtered dataframe for the date range.
        """
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)

        if start_date_dt > end_date_dt:
            raise ValueError("Start date cannot be later than end date.")

        years = list(range(start_date_dt.year, end_date_dt.year + 1))
        data = self.fetch_data_for_years(years)
        data['Date'] = pd.to_datetime(data['Date'])
        filtered_data = data[(data['Date'] >= start_date_dt) & (data['Date'] <= end_date_dt)].reset_index(drop=True)
        return filtered_data

    def fetch_data_for_specific_date_range(self, start_date, end_date):
        """
        Fetches weather data for a specific date range across multiple years.

        Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
        pd.DataFrame: Consolidated dataframe for the specific date range across multiple years.
        """
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)

        if start_date_dt > end_date_dt:
            raise ValueError("Start date cannot be later than end date.")

        years = list(range(start_date_dt.year, end_date_dt.year + 1))
        st_month, st_day = start_date_dt.month, start_date_dt.day
        en_month, en_day = end_date_dt.month, end_date_dt.day

        all_years_data = []

        for year in years:
            data = self.fetch_yearly_data(year)
            data['Date'] = pd.to_datetime(data['Date'])
            start_date_year = pd.to_datetime(f'{year}-{st_month:02d}-{st_day:02d}')
            end_date_year = pd.to_datetime(f'{year}-{en_month:02d}-{en_day:02d}')
            filtered_data = data[(data['Date'] >= start_date_year) & (data['Date'] <= end_date_year)]
            all_years_data.append(filtered_data)

        return pd.concat(all_years_data, ignore_index=True)

    @staticmethod
    def unit_conversion(df):
        """
        Applies unit conversion to the dataframe.

        Args:
        df (pd.DataFrame): DataFrame to apply conversions to.

        Returns:
        pd.DataFrame: Converted DataFrame.
        """
        df['srad'] *= 0.0864
        df['tmmx'] -= 273.15
        df['tmmn'] -= 273.15
        return df.round(3)

    @staticmethod
    def unit_conversion_pyfao56(df):
        """
        Applies unit conversion and adds additional placeholder columns.

        Args:
        df (pd.DataFrame): DataFrame to apply conversions to.

        Returns:
        pd.DataFrame: Converted DataFrame with additional columns.
        """
        df['srad'] *= 0.0864
        df['tmmx'] -= 273.15
        df['tmmn'] -= 273.15
        df.insert(4, 'vpar', '')
        df.insert(5, 'tdew', '')
        df.insert(10, 'ET', '')
        df.insert(11, 'MorP', '')
        return df.round(3)
