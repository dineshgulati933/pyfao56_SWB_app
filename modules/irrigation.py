from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import pandas as pd
from datetime import datetime

irrigation_blueprint = Blueprint('irrigation', __name__, template_folder='../templates')

@irrigation_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        irrigation_type = request.form.get('irrigation_type')

        # -----------------------------
        # 1️⃣ File Upload Method
        # -----------------------------
        if irrigation_type == 'upload':
            file = request.files.get('file')
            if not file:
                flash("No file uploaded. Please upload a valid file.", "danger")
                return redirect(url_for('irrigation.index'))
            
            try:
                # Read file based on extension
                if file.filename.endswith('.csv'):
                    irrigation_data = pd.read_csv(file)
                elif file.filename.endswith('.xlsx'):
                    irrigation_data = pd.read_excel(file)
                else:
                    flash("Unsupported file format. Use CSV or Excel.", "danger")
                    return redirect(url_for('irrigation.index'))

                # Validate columns
                required_columns = ['Date', 'Amount', 'Fraction']
                if not all(col in irrigation_data.columns for col in required_columns):
                    flash(f"File missing required columns: {required_columns}", "danger")
                    return redirect(url_for('irrigation.index'))

                # Save validated data to session
                irrigation_data = irrigation_data.dropna()
                session['irrigation_data'] = {
                    'Irrigation_type': irrigation_type,
                    'Irri_data': irrigation_data.to_dict(orient='records')
                }

                flash("Irrigation data uploaded successfully!", "success")
                return redirect(url_for('results.index'))
            
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "danger")
                return redirect(url_for('irrigation.index'))

        # -----------------------------
        # 2️⃣ Manual Irrigation Input
        # -----------------------------
        elif irrigation_type == 'manual':
            try:
                num_events = int(request.form.get('num_events', 0))
                manual_data = []
                for i in range(1, num_events + 1):
                    event = {
                        'Date': request.form.get(f'manual_date_{i}'),
                        'Amount': float(request.form.get(f'manual_amount_{i}', 0)),
                        'Fraction': float(request.form.get(f'manual_fraction_{i}', 0.6))  # Default fraction for furrow
                    }
                    manual_data.append(event)

                # Save manual data to session
                session['irrigation_data'] = {
                    'Irrigation_type': irrigation_type,
                    'Irri_data': manual_data
                }

                flash("Manual irrigation data saved successfully!", "success")
                return redirect(url_for('results.index'))
            
            except Exception as e:
                flash(f"Error processing manual input: {str(e)}", "danger")
                return redirect(url_for('irrigation.index'))

        # -----------------------------
        # 3️⃣ Auto-Irrigation Logic
        # -----------------------------
        elif irrigation_type == 'auto':
            try:
                auto_start = request.form.get('auto_start')
                auto_end = request.form.get('auto_end')
                trigger = request.form.get('trigger')
                auto_fraction = float(request.form.get('auto_fraction', 0.6))

                # Validate input dates
                if not auto_start or not auto_end:
                    flash("Start and end dates are required for auto-irrigation.", "danger")
                    return redirect(url_for('irrigation.index'))

                auto_start = datetime.strptime(auto_start, '%Y-%m-%d')
                auto_end = datetime.strptime(auto_end, '%Y-%m-%d')

                if auto_start >= auto_end:
                    flash("End date must be after the start date.", "danger")
                    return redirect(url_for('irrigation.index'))

                auto_irrigation_data = {
                    "start_date": auto_start.strftime('%Y-%m-%d'),
                    "end_date": auto_end.strftime('%Y-%m-%d'),
                    "trigger": trigger,
                    "auto_fraction": auto_fraction
                }

                # If Root Depletion is chosen
                if trigger == "root_depletion":
                    auto_irrigation_data["depletion_threshold"] = float(request.form.get('depletion_threshold', 0.4))
                    auto_irrigation_data["depletion_upper"] = float(request.form.get('depletion_upper', 95))

                # If ET Replacement is chosen
                elif trigger == "et_replacement":
                    auto_irrigation_data["et_days"] = int(request.form.get('et_days', 3))
                    auto_irrigation_data["et_type"] = request.form.get('et_type', 'ETc')
                    auto_irrigation_data["et_upper"] = request.form.get('et_upper',5)
                    # if auto_irrigation_data["et_upper"]:
                    #     auto_irrigation_data["et_upper"] = float(auto_irrigation_data["et_upper"])

                # Save to session
                session['irrigation_data'] = {
                    'Irrigation_type': irrigation_type,
                    'Irri_data':auto_irrigation_data
                }

                flash("Auto-irrigation settings saved successfully!", "success")
                return redirect(url_for('results.index'))

            except Exception as e:
                flash(f"Error processing auto-irrigation input: {str(e)}", "danger")
                return redirect(url_for('irrigation.index'))

    return render_template('irrigation.html')
