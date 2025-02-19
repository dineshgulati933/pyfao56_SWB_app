from flask import Blueprint, render_template, request, session, redirect, url_for, flash

soil_blueprint = Blueprint('soil', __name__, template_folder='../templates')

@soil_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        soil_type = request.form.get('soil_type')
        tew = float(request.form.get('tew_depth', 0.1))  # Default TEW = 0.1 m
        rew = float(request.form.get('rew', 8))   # Default REW = 8 mm

        num_layers = int(request.form.get('layers', 1))
        layers = []
        for i in range(1, num_layers + 1):
            layer = {
                'bottom_depth': float(request.form.get(f'bottom_depth_{i}', 0)),
                'field_capacity': float(request.form.get(f'field_capacity_{i}', 0)),
                'wilting_point': float(request.form.get(f'wilting_point_{i}', 0)),
                'initial_moisture': float(request.form.get(f'initial_moisture_{i}', 0))
            }
            layers.append(layer)

        bottom_depth = float([layer['bottom_depth'] for layer in layers][-1])
        zr_max = float(session['plant_data'].get('plant_properties').get('zr_max'))*100  # Convert to cm
        if bottom_depth < zr_max:
            flash(f'The bottom depth of the last layer ({bottom_depth} cm) should be greater or equal than the root depth ({zr_max} cm) !', 'danger')
            return render_template('soil.html')

        # Combine all soil data
        soil_data = {
            'soil_type': soil_type,
            'layers': layers,
            'tew_depth': tew,
            'rew': rew,
        }

        # Save to session
        session['soil_data'] = soil_data

        flash("Soil parameters saved successfully!", "success")
        return redirect(url_for('irrigation.index'))

    return render_template('soil.html')
