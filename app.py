from flask import Flask, render_template, redirect, url_for, flash, session
from modules.plant import plant_blueprint
from modules.weather import weather_blueprint
from modules.soil import soil_blueprint
from modules.results import results_blueprint
from modules.irrigation import irrigation_blueprint
from main.utils import delete_old_files
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('flask_key')
if not app.secret_key:
    raise ValueError('ERROR: No secret key set for Flask. Check your .env file.')

@app.before_request
def cleanup_old_data():
    """ Automatically remove old weather data if it is older than 6 hours """
    delete_old_files()  # Call the cleanup function before each request

@app.route('/')
def start():
    return render_template('start.html')

# Register blueprints
app.register_blueprint(plant_blueprint, url_prefix='/plant-parameters')
app.register_blueprint(weather_blueprint, url_prefix='/weather')
app.register_blueprint(soil_blueprint, url_prefix='/soil')
app.register_blueprint(irrigation_blueprint, url_prefix='/irrigation')
app.register_blueprint(results_blueprint, url_prefix='/results')

@app.before_request
def initialize_session():
    # Clear session only if not already initialized
    if 'initialized' not in session:
        session.clear()
        session['initialized'] = True

@app.route('/clear-session')
def clear_session():
    session.clear()
    flash("Session cleared successfully!", "success")
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('base.html')

# @app.teardown_request
# def remove_weather_data(exception=None):
#     """ Automatically remove weather data when the user session ends """
#     weather_metadata = session.get('weather_data', {})
#     if weather_metadata:
#         delete_weather_data(weather_metadata['latitude'], weather_metadata['longitude'])

if __name__ == '__main__':
    app.run(debug=True)
