from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import pandas as pd
from main.gridMET_fetch import WeatherDataFetcher
from datetime import datetime
import logging
from main.utils import save_weather_data

weather_blueprint = Blueprint('weather', __name__, template_folder='../templates')

@weather_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        elevation = request.form.get('elevation')
        data_source = request.form.get('data_source')

        # Ensure plant dates exist in the session
        plant_data = session.get('plant_data', {})
        planting_date = plant_data.get('planting_date')
        maturity_date = plant_data.get('maturity_date')

        try:
            planting_date = datetime.strptime(planting_date, '%Y-%m-%d')
            maturity_date = datetime.strptime(maturity_date, '%Y-%m-%d')

        except Exception as e:
            logging.error(f"Error occurred with dates: {str(e)}")
            flash("Invalid planting or maturity date format.", "danger")
            return redirect(url_for('weather.index'))

        if data_source == 'upload':
            file = request.files.get('file')

            if not file:
                flash("No file uploaded. Please upload a valid file.", "danger")
                return redirect(url_for('weather.index'))

            try:
                # Validate and read file
                if file.filename.endswith('.csv'):
                    data = pd.read_csv(file)
                elif file.filename.endswith('.xlsx'):
                    data = pd.read_excel(file)
                else:
                    flash("Invalid file format. Please upload a CSV or Excel file.", "danger")
                    return redirect(url_for('weather.index'))

                # validation for column names
                required_columns = ['Date', 'srad', 'tmmx', 'tmmn', 'rmax', 'rmin', 'vs', 'pr']
                missing_columns = [col for col in required_columns if col not in data.columns]

                if missing_columns:
                    flash(f"Missing required columns: {', '.join(missing_columns)}", "danger")
                    return redirect(url_for('weather.index'))

                # Convert Date column to string to ensure compatibility
                data.columns = required_columns
                data.insert(4, 'vpar', '')
                data.insert(5, 'tdew', '')
                data.insert(10, 'ET', '')
                data.insert(11, 'MorP', '')
                data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')

                # Save data to JSON file
                save_weather_data(lat, lon, data)

                # Save metadata in session
                session['weather_data'] = {
                    'latitude': lat,
                    'longitude': lon,
                    'elevation': elevation,
                    'data_source': data_source
                }

                flash("Weather parameters saved successfully!", "success")
                return redirect(url_for('soil.index'))

            except Exception as e:
                logging.error(f"File processing error: {str(e)}")
                flash("Something went wrong while processing the file.", "danger")
                return redirect(url_for('weather.index'))

        elif data_source == 'fetch':
            et_option = request.form.get('et_option') #this is not longer needed

            try:
                # Fetch weather data from API
                data = fetch_weather_data(lat, lon, planting_date, maturity_date)

                # Convert DataFrame to JSON and save
                save_weather_data(lat, lon, data)

                # Save metadata in session
                session['weather_data'] = {
                    'latitude': lat,
                    'longitude': lon,
                    'elevation': elevation,
                    'data_source': data_source
                }

                flash("Weather parameters saved successfully!", "success")
                return redirect(url_for('soil.index'))

            except Exception as e:
                logging.error(f"Weather fetch error: {str(e)}")
                flash("Failed to fetch weather data.", "danger")
                return redirect(url_for('weather.index'))

        return redirect(url_for('soil.index'))

    return render_template('weather.html')


def fetch_weather_data(lat, lon, planting_date, maturity_date):
    """ Fetches weather data from gridMET """
    varname = ['srad', 'tmmx', 'tmmn', 'rmax', 'rmin', 'vs', 'pr']
    wth_data = WeatherDataFetcher(lat, lon, varname).fetch_data_for_date_range(planting_date, maturity_date)
    data = WeatherDataFetcher.unit_conversion_pyfao56(wth_data)

    return data