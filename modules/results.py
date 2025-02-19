from flask import Blueprint, render_template, session, send_file, redirect, url_for, flash
import pandas as pd
import io
import pyfao56 as fao
import pyfao56.custom as custom
import pyfao56.tools as tools
from main.utils import *
from main.pyfao56_mod import *
from main.grhs import *

results_blueprint = Blueprint('results', __name__, template_folder='../templates')

@results_blueprint.route('/')
def index():
    # Aggregate all data from the session
    plant_data = session.get('plant_data', {})
    weather_data = session.get('weather_data', {})
    soil_data = session.get('soil_data', {})
    irri_data = session.get('irrigation_data', {})

    if not plant_data or not weather_data or not soil_data:
        flash("Incomplete input data. Please complete all sections.", "danger")
        return redirect(url_for('plant.index'))

    # Process water balance sums for table on result page
    simulation_results, swb_cum_data = simulate_model(plant_data, weather_data, soil_data, irri_data)
    swb_cum_table = pd.DataFrame([swb_cum_data]).round(2).to_html(classes='table table-striped', index=False,
                                                                  border=0)
    plot_html = wb_plot_interactive(simulation_results)

    return render_template(
        'results.html',
        swb_cum_table=swb_cum_table,
        plot_html=plot_html,
        plant_data=plant_data,
        weather_data=weather_data,
        soil_data=soil_data,
        irri_data=irri_data
    )


@results_blueprint.route('/download_csv')
def download_csv():
    df, _ = simulate_model(
        session.get('plant_data', {}),
        session.get('weather_data', {}),
        session.get('soil_data', {}),
        session.get('irrigation_data', {})
    )

    # Convert DataFrame to CSV
    csv_file = io.StringIO()
    df.to_csv(csv_file, index=False)
    csv_file.seek(0)

    return send_file(
        io.BytesIO(csv_file.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='simulation_results.csv'
    )


@results_blueprint.route('/download_plot')
def download_plot():
    df,_ = simulate_model(
        session.get('plant_data', {}),
        session.get('weather_data', {}),
        session.get('soil_data', {}),
        session.get('irrigation_data', {})
    )
    plot_img = wb_plot(df)

    # Ensure the base64 string is valid and remove the prefix
    if plot_img.startswith("data:image/png;base64,"):
        img_data = base64.b64decode(plot_img.split(",")[1])
    else:
        return "Invalid plot data", 400

    # Return the decoded image as a downloadable file
    return send_file(
        io.BytesIO(img_data),
        mimetype='image/png',
        as_attachment=True,
        download_name='simulation_plot.png'
    )


def simulate_model(plant_data, weather_data, soil_data, irri_data):
    '''This is the heart of the simulation. It takes in the input data and runs the FAO56 model to simulate the water balance.'''

    planting_date = plant_data.get('planting_date', []) # Get the planting date from the plant data
    maturity_date = plant_data.get('maturity_date', []) # Get the maturity date from the plant data

    start = pd.to_datetime(planting_date).strftime('%Y-%j') # Convert the planting date to the format required by the model
    end = pd.to_datetime(maturity_date).strftime('%Y-%j') # Convert the maturity date to the format required by the model

    # Access nested dictionaries
    layers = soil_data.get('layers', []) # Get the soil layers from the soil data
    depths = [int(layer.get('bottom_depth', 0)) for layer in layers] # Get the bottom depth of each layer from the soil data in centimeters and convert to integer (as required by the model)
    thetaFC = [float(layer.get('field_capacity', 0.0))/100 for layer in layers] # Get the field capacity of each layer from the soil data in percentage and convert to float (as required by the model)
    thetaWP = [float(layer.get('wilting_point', 0.0))/100 for layer in layers] # Get the wilting point of each layer from the soil data in percentage and convert to float (as required by the model)
    thetaIN = [float(layer.get('initial_moisture', 0.0))/100 for layer in layers] # Get the initial moisture of each layer from the soil data in percentage and convert to float (as required by the model)
    print(depths, thetaFC, thetaWP, thetaIN) # Print the soil data for debugging

    # Load soil data

    # Note: In this, I am asking user to input soil properties (depths, FC, PWP, and initial moisture) but later we want to use SSURGO data to get these properties based on the location. I worked on this and will provide in repo.
    sol = custom.ExampleSoil() # Create an instance of the ExampleSoil class from pyfao56
    sol.customload(depths, thetaFC ,thetaWP,thetaIN) # Load the soil data using the soil layers

    lat = float(weather_data.get('latitude')) # Get the latitude from the weather data
    lon = float(weather_data.get('longitude')) # Get the longitude from the weather data

    # Load weather data
    weather_data_dict = load_weather_data(lat, lon) # Load the weather data using the latitude and longitude
    w_data = pd.DataFrame(weather_data_dict['weather_data']) # Convert the weather data to a DataFrame
    w_order  = ['Date','srad','tmmx','tmmn','vpar','tdew','rmax','rmin','vs','pr','ET','MorP'] # Define the order of the columns in the weather data. This order is needed in pyfao56.

    # Handle data type conversion
    def convert_column_types(df):
        # Columns to convert to float
        float_columns = ['srad', 'tmmx', 'tmmn', 'vpar', 'tdew', 'rmax', 'rmin', 'vs', 'pr', 'ET']
        
        # Convert float columns
        for col in float_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to float, set invalid values to NaN
        
        # Convert 'Date' to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert invalid dates to NaT
        
        # Ensure 'MorP' is string
        df['MorP'] = df['MorP'].astype(str).replace({'': None})  # Replace empty strings with None. This is needed for pyfao56 but not necessary for our purposes.

        return df

    # Apply conversion
    w_data = convert_column_types(w_data)

    # Reorder the columns
    w_data = w_data[w_order]

    # Note: The aforementioned weather handling is for gridMET or uploaded weather data where vpar and tdew are not available. In case of Agrimet data, 
    # we have tdew but not rmin and rmax for now. We can run our simulation either with vpar or tdew or rmin and rmax. However, for Kcb adjustments,
    # we need rmin and may need to find a way to get rmin. I will explain this later while using that function.

    # Create an instance of the Parameters class from pyfao56
    par = fao.Parameters()
    # Note: As Meetpal mentioned, we probably will not ask user for these plant and soil related properties. Also, in next version of pyfao56 (1.4.0), we added this as class to load these properties based on crop name.
    
    plant_properties = plant_data.get('plant_properties') # Get the plant properties from the plant data

    #crop parameters
    par.kcbini = float(plant_properties.get('kcb_ini')) # Get the initial crop coefficient from the plant properties
    par.Kcbmid = float(plant_properties.get('kcb_mid')) # Get the mid-season crop coefficient from the plant properties
    par.Kcbend = float(plant_properties.get('kcb_end')) # Get the end-season crop coefficient from the plant properties

    par.Lini = int(plant_properties.get('l_ini')) # Get the initial stage length from the plant properties
    par.Ldev = int(plant_properties.get('l_dev')) # Get the development stage length from the plant properties
    par.Lmid = int(plant_properties.get('l_mid')) # Get the mid-season stage length from the plant properties
    par.Lend = int(plant_properties.get('l_end')) # Get the end-season stage length from the plant properties

    par.hini = float(plant_properties.get('h_ini')) # Get the initial height from the plant properties
    par.hmax = float(plant_properties.get('h_max')) # Get the maximum height from the plant properties

    par.Zrini = float(plant_properties.get('zr_ini')) # Get the initial root depth from the plant properties
    par.Zrmax = float(plant_properties.get('zr_max')) # Get the maximum root depth from the plant properties
    par.pbase = float(plant_properties.get('p')) # Get the depletion fraction from the plant properties

    #print(par.Kcbend)

    #other soil parameters
    par.CN2 = float(plant_properties.get('CN2', 76)) # Get the curve number for surface runoff from the plant properties
    par.Ze = float(soil_data.get('tew_depth', 0.1)) # Get the effective evaporative layer depth from the soil data in meters
    par.REW = float(soil_data.get('rew', 8)) # Get the readily evaporable water from the soil data in millimeters and this varies with soil type



    w_data['Date'] = pd.to_datetime(w_data['Date'], dayfirst=False).dt.strftime('%Y-%j')
    w_data.set_index('Date', inplace=True)

    wth = fao.Weather() # Create an instance of the Weather class from pyfao56
    # Note: In pyfao56, the weather data is loaded from .wth file or need to creare custom function to load the data. Instead, I am working aroud to add weather data directly to the class.
    wth.wdata = w_data.copy() # using copy to potentially using w_data for other purposes in future such as gdd based calutions. We have function for this in utils.py but not implemented here.
    wth.wdata.index.name = None
    wth.wdata.columns = wth.cnames
    wth.z = float(weather_data.get('elevation')) # Get the elevation from the weather data in meters
    wth.lat = lat 
    wth.wndht = 10 # This is true for gridMET data but in case of Agrimet data, we need to define this dynamically based on the data source.
    #print(wth.wdata.head())

    irr = fao.Irrigation() # Create an instance of the Irrigation class from pyfao56


    if irri_data['Irrigation_type'] == 'manual' or irri_data['Irrigation_type'] == 'upload':
        for ir_event in irri_data.get('Irri_data', []):
            ir_year, ir_doy = pd.to_datetime(ir_event.get('Date', None)).strftime('%Y-%j').split('-')
            irr.addevent(int(ir_year), int(ir_doy), 
                        float(ir_event.get('Amount', 0)), 
                        float(ir_event.get('Fraction', 1)))
            
    # This is still need to work around auto irrigation and potentially we will not utilize manual or upload irrigation data in grower centric application.    
    # there are many other possibilties with auto irrigation and we can discuss this in detail.

    elif irri_data['Irrigation_type'] == 'auto':
        auto_data = irri_data.get('Irri_data', {})
        auto_start = auto_data.get('start_date')
        auto_end = auto_data.get('end_date')
        trigger = auto_data.get('trigger')
        frac = float(auto_data.get('auto_fraction', 0.6))
        auto_start = pd.to_datetime(auto_start).strftime('%Y-%j')
        auto_end = pd.to_datetime(auto_end).strftime('%Y-%j')
        
        if trigger == 'root_depletion':
            dp_th = float(auto_data.get('depletion_threshold', 0.5))
            dp_up = float(auto_data.get('depletion_upper', 95))
            dp_up = max(0, 1 - dp_up/100)
            airr = fao.AutoIrrigate()
            airr.addset(auto_start,auto_end,mad=dp_th,itfdr=dp_up,fpday=0,fw=frac)

        elif trigger == 'et_replacement':
            et_days = int(auto_data.get('et_days', 3))
            et_type = auto_data.get('et_type', 'ETc')
            print(pd.to_numeric(auto_data.get('et_upper', 0.0), errors='coerce'))
            et_up = float(pd.to_numeric(auto_data.get('et_upper', 0.0), errors='coerce'))
            #et_up = float('NaN')
            airr = fao.AutoIrrigate() # Create an instance of the AutoIrrigate class from pyfao56
            airr.addset(auto_start, auto_end, dsli=et_days, ietrd=et_days, ettyp=et_type, fpday=0, imax=et_up,fw=frac)
        else:
            return "Invalid irrigation trigger", 400
        
    # This is to adjust the crop stage length based on the planting date and maturity date. For instance, if user defined planting and maturity dates whose total crop span is different compared to the default stage lengths
    # then we need to adjust the stage lengths accordingly. This is explained in pyfao56_mod.py file.
    if plant_properties.get('stage_length_adjust') == 'on':
        par.Lini,par.Ldev,par.Lmid,par.Lend = crop_stage(start,end,par.Lini,par.Ldev,par.Lmid,par.Lend)
        
    # This is to adjust the crop coefficient based on the weather data. For instance, if user wants to adjust the crop coefficient based on the weather data then we need to adjust the crop coefficient accordingly.
    # This is explained in pyfao56_mod.py file. Here, we need rmin for adjustments which is not available in Agrimet daily data but in hourly data and we need to find a way to get this.
    # if plant_properties.get('kcb_adjust') == 'on':
        # par.Kcbmid,par.Kcbend = Kcb_adj(w_data,start,end,par.Kcbmid,par.Kcbend,
        #                                 par.Lini,par.Ldev,par.Lmid,par.Lend,wth.wndht,par.hmax) #02/18/2025 no longer needed with pyfao56 1.4.0 as we included in the update
        
    #Boolean to adjust Kcb
    K_adj = plant_properties.get('kcb_adjust', 'off') == 'on'

    # Boolean to simulate the surface runoff.   
    roff = plant_properties.get('roff_adjust', 'on') == 'on'

    # Boolean to conserve the p value.
    cons_p = not plant_properties.get('p_value_adjust', 'off') == 'on'

    if irri_data['Irrigation_type'] == 'manual' or irri_data['Irrigation_type'] == 'upload':
        mdl = fao.Model(start,end, par, wth, irr, sol=sol, roff=roff, cons_p= cons_p, K_adj=K_adj)
    else:
        mdl = fao.Model(start,end, par, wth, sol=sol,roff=roff, autoirr = airr, cons_p= cons_p, K_adj=K_adj)

    mdl.run()
    #print(mdl.odata.iloc[:,:5].head(5))
    return mdl.odata, mdl.swbdata

