# Note: The next version of pyfao56 1.4.0 will include all the crop parameters and constants in the package itself. However, will still missing the CN2 values required to simulate surface runoff.
# These values are crop and soil specific and may sill need to use the json or dictionary to store these values. 


CROP_COEFFICIENTS = {
    'broccoli': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.85},
    'cabbage': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.85},
    'carrots': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.85},
    'cauliflower': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.85},
    'celery': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.90},
    'lettuce': {'kcb_ini': 0.15, 'kcb_mid': 0.90, 'kcb_end': 0.90},
    'onions_dry': {'kcb_ini': 0.15, 'kcb_mid': 0.95, 'kcb_end': 0.65},
    'onions_green': {'kcb_ini': 0.15, 'kcb_mid': 0.90, 'kcb_end': 0.90},
    'tomato': {'kcb_ini': 0.15, 'kcb_mid': 1.10, 'kcb_end': 0.70},
    'potato': {'kcb_ini': 0.15, 'kcb_mid': 1.10, 'kcb_end': 0.65},
    'wheat': {'kcb_ini': 0.15, 'kcb_mid': 1.15, 'kcb_end': 0.70},
    'maize': {'kcb_ini': 0.20, 'kcb_mid': 1.20, 'kcb_end': 0.60},
    'rice': {'kcb_ini': 0.30, 'kcb_mid': 1.05, 'kcb_end': 0.90},
    'Other': {'kcb_ini': None, 'kcb_mid': None, 'kcb_end': None},
}

# Crop stage lengths in days
CROP_STAGE_LENGTHS = {
    'broccoli': {'l_ini': 35, 'l_dev': 45, 'l_mid': 40, 'l_end': 15},
    'cabbage': {'l_ini': 40, 'l_dev': 60, 'l_mid': 50, 'l_end': 15},
    'carrots': {'l_ini': 30, 'l_dev': 40, 'l_mid': 60, 'l_end': 20},
    'cauliflower': {'l_ini': 35, 'l_dev': 50, 'l_mid': 40, 'l_end': 15},
    'celery': {'l_ini': 30, 'l_dev': 55, 'l_mid': 105, 'l_end': 20},
    'lettuce': {'l_ini': 30, 'l_dev': 40, 'l_mid': 25, 'l_end': 10},
    'onions_dry': {'l_ini': 20, 'l_dev': 35, 'l_mid': 110, 'l_end': 45},
    'onions_green': {'l_ini': 25, 'l_dev': 30, 'l_mid': 10, 'l_end': 5},
    'tomato': {'l_ini': 35, 'l_dev': 40, 'l_mid': 50, 'l_end': 30},
    'potato': {'l_ini': 30, 'l_dev': 35, 'l_mid': 50, 'l_end': 30},
    'wheat': {'l_ini': 35, 'l_dev': 45, 'l_mid': 60, 'l_end': 30},
    'maize': {'l_ini': 30, 'l_dev': 40, 'l_mid': 50, 'l_end': 40},
    'rice': {'l_ini': 20, 'l_dev': 30, 'l_mid': 80, 'l_end': 20},
    'Other': {'l_ini': None, 'l_dev': None, 'l_mid': None, 'l_end': None},
}

# Crop properties: height, root depth, depletion fraction
CROP_PROPERTIES = {
    'broccoli': {'h_ini': 0.01, 'h_max': 0.6, 'zr_ini': 0.30, 'zr_max': 0.60, 'p': 0.45},
    'cabbage': {'h_ini': 0.01, 'h_max': 0.8, 'zr_ini': 0.40, 'zr_max': 0.80, 'p': 0.45},
    'carrots': {'h_ini': 0.01, 'h_max': 1.0, 'zr_ini': 0.40, 'zr_max': 1.0, 'p': 0.35},
    'cauliflower': {'h_ini': 0.01, 'h_max': 0.7, 'zr_ini': 0.30, 'zr_max': 0.70, 'p': 0.45},
    'celery': {'h_ini': 0.01, 'h_max': 0.5, 'zr_ini': 0.30, 'zr_max': 0.50, 'p': 0.20},
    'lettuce': {'h_ini': 0.01, 'h_max': 0.5, 'zr_ini': 0.30, 'zr_max': 0.50, 'p': 0.30},
    'onions_dry': {'h_ini': 0.01, 'h_max': 0.6, 'zr_ini': 0.30, 'zr_max': 0.60, 'p': 0.30},
    'onions_green': {'h_ini': 0.01, 'h_max': 0.6, 'zr_ini': 0.30, 'zr_max': 0.60, 'p': 0.30},
    'tomato': {'h_ini': 0.02, 'h_max': 1.5, 'zr_ini': 0.40, 'zr_max': 1.50, 'p': 0.40},
    'potato': {'h_ini': 0.02, 'h_max': 1.0, 'zr_ini': 0.40, 'zr_max': 1.00, 'p': 0.35},
    'wheat': {'h_ini': 0.01, 'h_max': 1.0, 'zr_ini': 0.10, 'zr_max': 1.20, 'p': 0.45},
    'maize': {'h_ini': 0.02, 'h_max': 2.0, 'zr_ini': 0.20, 'zr_max': 1.50, 'p': 0.50},
    'rice': {'h_ini': 0.01, 'h_max': 0.8, 'zr_ini': 0.10, 'zr_max': 0.80, 'p': 0.30},
    'Other': {'h_ini': None, 'h_max': None, 'zr_ini': None, 'zr_max': None, 'p': None},
}

# Curve Number for surface runoff
CN2 = {
    'broccoli': 76,
    'cabbage': 76,
    'carrots': 76,
    'cauliflower': 76,
    'celery': 76,
    'lettuce': 76,
    'onions_dry': 76,
    'onions_green': 76,
    'tomato': 76,
    'potato': 76,
    'wheat': 76,
    'maize': 76,
    'rice': 76,
    'Other': None,
}