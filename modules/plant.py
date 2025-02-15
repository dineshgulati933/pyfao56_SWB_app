from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from main.crop_data import CROP_COEFFICIENTS, CROP_STAGE_LENGTHS, CROP_PROPERTIES, CN2
import pandas as pd

plant_blueprint = Blueprint('plant', __name__, template_folder='../templates')

@plant_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        planting_date = request.form.get('planting_date')
        maturity_date = request.form.get('maturity_date')
        crop = request.form.get('crop')

        if pd.to_datetime(planting_date).strftime('%Y-%j') >= pd.to_datetime(maturity_date).strftime('%Y-%j'):
            flash(f'Maturity date ({maturity_date}) must be later than planting date ({planting_date})', 'danger' )
            return redirect(url_for('plant.index'))
        
        # Define all keys for coefficients and properties
        crop_keys = [
            # Crop Coefficients
            'kcb_ini', 'kcb_mid', 'kcb_end',
            
            # Crop Properties
            'h_ini', 'h_max', 'zr_ini', 'zr_max', 'p', 'CN2',
            
            # Stage Lengths
            'l_ini', 'l_dev', 'l_mid', 'l_end',
            
            # Optional Adjustments
            'kcb_adjust',  # Checkbox for Kcb adjustment
            'stage_length_adjust',  # Checkbox for stage length adjustment
            'p_value_adjust', #checkbox for p_value adjustment
            'roff_adjust', #surface runoff to include in simulation
        ]


        # Collect all values from the form
        plant_properties = {key: request.form.get(key) for key in crop_keys}

        # Save data to session
        session['plant_data'] = {
            'planting_date': planting_date,
            'maturity_date': maturity_date,
            'crop': crop,
            'plant_properties': plant_properties,
        }

        flash("Plant parameters saved successfully!", "success")
        return redirect(url_for('weather.index'))

    # Pass crop data to the template
    return render_template(
        'plant_parameters.html',
        crops=list(CROP_COEFFICIENTS.keys()),
        crop_coefficients=CROP_COEFFICIENTS,
        crop_lengths = CROP_STAGE_LENGTHS,
        crop_properties=CROP_PROPERTIES,
        cn2=CN2,  # Pass the entire dictionary
    )
