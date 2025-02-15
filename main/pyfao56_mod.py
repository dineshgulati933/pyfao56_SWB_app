from datetime import datetime
import math


# Note: Most of the docstrings and comments are generated using the AI-based tool and may not be accurate. 
# Although, I skimmmed through them to make sure they are relevant to the functions.

def gdd(df=None, start=None, end=None, T_base=None, T_cutoff=None, cgdd=None, mthd='corn'):
    """
    Calculate Growing Degree Days (GDD) from temperature data.

    This function computes cumulative GDD for a given time range and returns the cumulative 
    GDD dataframe along with the end date when the cumulative GDD target is reached.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing temperature columns ('tmmx' for maximum and 'tmmn' for minimum).
    start : str
        Start date in the format '%Y-%j' (e.g., '2024-100' for the 100th day of 2024).
    end : str
        End date in the format '%Y-%j'. Used as an upper limit for calculation.
    T_base : float
        Base temperature (°C) below which crop growth is minimal.
    T_cutoff : float
        Cutoff temperature (°C) above which crop growth is limited.
    cgdd : float
        Target cumulative GDD to reach.
    mthd : str, optional
        Method for GDD calculation, either 'corn' or 'other'.
        - 'corn': Uses the modified high-low method recommended for corn.
        - 'other': Uses the simple average method for other crops in Idaho.
        Default is 'corn'.

    Returns
    -------
    df_gdd : pandas.DataFrame
        DataFrame containing daily GDD values and cumulative GDD from the start date to 
        the end date or the date when cumulative GDD exceeds the target (`cgdd`).
    end_final : str
        Final end date (in '%Y-%j' format) when the cumulative GDD target is reached or 
        the provided end date, whichever comes first.

    Notes
    -----
    - For 'corn' method: 
      GDD = ((max(min(Tmax, T_cutoff), T_base) + max(min(Tmin, T_cutoff), T_base)) / 2) - T_base
      Reference: Allen and Robison, 2007, Evapotranspiration for Idaho (p. 117, eq. 3.1).
    
    - For 'other' method:
      GDD = max(((Tmax + Tmin) / 2) - T_base, 0)
      Reference: Allen and Robison, 2007, Evapotranspiration for Idaho (p. 117, eq. 3.1).

    Example
    -------
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> data = {'tmmx': [30, 32, 31], 'tmmn': [20, 21, 19]}
    >>> df = pd.DataFrame(data, index=pd.date_range('2024-05-01', periods=3))
    >>> df.index = df.index.strftime('%Y-%j')
    >>> gdd_df, end_date = gdd(df=df, start='2024-121', end='2024-150', 
    ...                        T_base=10, T_cutoff=30, cgdd=50, mthd='corn')
    >>> print(gdd_df)
    >>> print(end_date)
    """

    df_gdd = df.loc[start:][['tmmx','tmmn']]
    end = datetime.strptime(end,'%Y-%j')
    
    if mthd == 'corn': #this method is recommended for corn (eq. 3.1, p-117 ,Allen and Robison 2007 Evapotranspiration for Idaho)
        df_gdd['gdd'] = df_gdd.apply(lambda row: (max(min(row['tmmx'],T_cutoff),T_base) + (max(min(row['tmmn'],T_cutoff),T_base)))/2 - T_base, axis=1)
        #gdd = (max(min(tmmx,T_cutoff),T_base) + (max(min(tmmn,T_cutoff),T_base)))/2 - T_base
    elif mthd == 'other': #this method is recommended for other crops in ID (eq. 3.1, p-117 ,Allen and Robison 2007 Evapotranspiration for Idaho)
        df_gdd['gdd'] = df_gdd.apply(lambda row: max(((row['tmmx']+row['tmmn'])/2) - T_base, 0), axis=1)
        #gdd = max(((tmmx+tmmn)/2) - T_base, 0)
    df_gdd['gdd'] = df_gdd['gdd'].cumsum()
    #end_gdd = df_gdd.loc[df_gdd['gdd'] <= cgdd].index[-1]
    end_gdd = df_gdd.loc[df_gdd['gdd'] >= cgdd].index[0] #this will result in one more day when gdd completed
    end_gdd = datetime.strptime(end_gdd, '%Y-%j') if isinstance(end_gdd, str) else end_gdd
    if end is not None:
        end_final = end if end_gdd > end else end_gdd
        end_final = datetime.strftime(end_final, '%Y-%j')
    df_gdd = df_gdd[start:end_final]
    return df_gdd,end_final



def crop_stage(start,end,Lini,Ldev,Lmid,Lend):
    """
    Calculate the adjusted crop growth stage lengths based on the total growing period.

    This function adjusts the lengths of crop growth stages (`Lini`, `Ldev`, `Lmid`, `Lend`)
    proportionally based on the actual duration between the provided start and end dates.

    Parameters
    ----------
    start : str
        Start date of the crop growth period in '%Y-%j' format 
        (e.g., '2024-121' for the 121st day of 2024).
    end : str
        End date of the crop growth period in '%Y-%j' format.
    Lini : int
        Initial growth stage length (in days) as defined in FAO-56.
    Ldev : int
        Development stage length (in days) as defined in FAO-56.
    Lmid : int
        Mid-season growth stage length (in days) as defined in FAO-56.
    Lend : int
        Late-season growth stage length (in days) as defined in FAO-56.

    Returns
    -------
    tuple of int
        Adjusted lengths for each crop growth stage `(Lini, Ldev, Lmid, Lend)`,
        ensuring that the total duration matches the actual number of days 
        between the provided start and end dates.

    Notes
    -----
    - The function first calculates the total crop growth period from `start` to `end`.
    - It then proportionally adjusts each stage length based on their fraction 
      of the total FAO-56 crop growth length (`Lini + Ldev + Lmid + Lend`).
    - The adjusted stage lengths sum exactly to the total actual growing days.

    Example
    -------
    >>> crop_stage('2024-121', '2024-240', 20, 30, 40, 30)
    (24, 35, 47, 44)

    Explanation for Example:
    - The total growing period from the 121st day to the 240th day is 120 days.
    - Each growth stage (`Lini`, `Ldev`, `Lmid`, `Lend`) is adjusted proportionally 
      based on their ratio in the original FAO-56 crop stages.

    """
    start = datetime.strptime(start, '%Y-%j')
    end = datetime.strptime(end, '%Y-%j')
    crop_span = (end-start).days+1
    crop_fao = Lini+Ldev+Lmid+Lend
    Lini = int((Lini/crop_fao)*crop_span)
    Ldev = int((Ldev/crop_fao)*crop_span)
    Lmid = int((Lmid/crop_fao)*crop_span)
    Lend = crop_span-Lini-Ldev-Lmid
    return Lini,Ldev,Lmid,Lend



def Kcb_adj(df, start, end, Kcbmid, Kcbend, Lini, Ldev, Lmid, Lend, wndht, hmax):
    """
    Adjust mid-season (Kcbmid) and end-season (Kcbend) crop basal coefficients 
    based on average minimum relative humidity (RHmin) and wind speed 
    following FAO-56 Equation 70 (page 136).

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing weather data with columns 'rmin' (minimum relative humidity) 
        and 'vs' (wind speed).
    start : str
        Start date (in '%Y-%j' format) for the crop growing period.
    end : str
        End date (in '%Y-%j' format) for the crop growing period.
    Kcbmid : float
        Mid-season crop coefficient (Kcb).
    Kcbend : float
        End-season crop coefficient (Kcb).
    Lini : int
        Length of the initial crop growth stage (in days).
    Ldev : int
        Length of the crop development stage (in days).
    Lmid : int
        Length of the mid-season crop growth stage (in days).
    Lend : int
        Length of the late-season crop growth stage (in days).
    wndht : float
        Height at which wind speed is measured (in meters).
    hmax : float
        Maximum crop height (in meters).

    Returns:
    --------
    tuple
        A tuple containing adjusted Kcb values for mid-season (Kcbmid) and 
        end-season (Kcbend).

    Notes:
    ------
    - Adjustments to Kcbmid and Kcbend are based on:
      - Average minimum relative humidity (RHmin) during the mid and late season.
      - Average wind speed during the mid and late season.
    - Wind speed is corrected to a standard height of 2 meters using 
      the logarithmic wind profile equation.
    - The adjustments use the equation from FAO-56 (Equation 70, page 136).

    Example:
    --------
    >>> df = pd.DataFrame({'rmin': [45, 50, 55], 'vs': [3.0, 2.5, 2.0]})
    >>> Kcb_adj(df, '2024-120', '2024-150', 1.10, 0.85, 20, 30, 40, 30, 2.0, 1.2)
    (1.12, 0.87)
    """
    cor_df = df[start:end]

    # Mid-season average RHmin and wind speed correction
    cor_avg_RHmin_mid = cor_df[Lini+Ldev:Lini+Ldev+Lmid]['rmin'].mean()
    cor_avg_RHmin_mid = sorted([20.0, cor_avg_RHmin_mid, 80.0])[1]  # Clamp between 20% and 80%

    cor_avg_wind_mid = cor_df[Lini+Ldev:Lini+Ldev+Lmid]['vs']
    cor_avg_wind_mid = cor_avg_wind_mid.apply(lambda x: x * (4.87 / math.log(67.8 * wndht - 5.42))).mean()
    cor_avg_wind_mid = sorted([1.0, cor_avg_wind_mid, 6.0])[1]  # Clamp between 1.0 and 6.0 m/s

    # End-season average RHmin and wind speed correction
    cor_avg_RHmin_end = cor_df[Lini+Ldev+Lmid:]['rmin'].mean()
    cor_avg_RHmin_end = sorted([20.0, cor_avg_RHmin_end, 80.0])[1]

    cor_avg_wind_end = cor_df[Lini+Ldev+Lmid:]['vs']
    cor_avg_wind_end = cor_avg_wind_end.apply(lambda x: x * (4.87 / math.log(67.8 * wndht - 5.42))).mean()
    cor_avg_wind_end = sorted([1.0, cor_avg_wind_end, 6.0])[1]

    # Adjust mid-season Kcb if initial Kcb is >= 0.45
    if Kcbmid >= 0.45:
        Kcbmid = round(
            Kcbmid + (0.04 * (cor_avg_wind_mid - 2) - 0.004 * (cor_avg_RHmin_mid - 45)) * (hmax / 3) ** 0.3,
            2
        )

    # Adjust end-season Kcb if initial Kcb is >= 0.45
    if Kcbend >= 0.45:
        Kcbend = round(
            Kcbend + (0.04 * (cor_avg_wind_end - 2) - 0.004 * (cor_avg_RHmin_end - 45)) * (hmax / 3) ** 0.3,
            2
        )

    return Kcbmid, Kcbend



# def soil_carbon(t_co2_eq : float, bulk_d : float, depth : float = 30):
#     """
#     Calculate the percentage of carbon in the top soil layer based on CO2 equivalent emissions.

#     Parameters:
#     t_co2_eq (float): Tonnes of CO2 equivalent per acre per year.
#     bulk_d (float): Bulk density of the soil in g/cm³ (equivalent to t/m³).
#     depth (float): Depth of the soil layer in cm. Default is 30 cm.

#     Returns:
#     float: Percentage of carbon in the soil mass.
#     """
#     # Convert CO2 equivalent to carbon equivalent
#     t_c_eq = (12/44) * t_co2_eq
    
#     # Calculate the soil mass in tonnes
#     soil_mass = (4046.86 * depth/100) * bulk_d #acre (m2) * depth(m) * bulk density (tonnes/m3)
    
#     # Calculate the percentage of carbon in the soil
#     return 100 * t_c_eq / soil_mass



# def pedotransfer(sand=None, clay=None, soc = None, calc = False):
#     if calc == False:
#         thpwp = 7.222+0.296*clay-0.074*sand-0.309*soc+0.022*(sand*soc)+0.022*(clay*soc)
#         thfc = 37.217-0.140*clay-0.304*sand-0.222*soc+0.051*(sand*soc)+0.085*(clay*soc)+0.002*(clay*sand)
#     else:
#         thpwp = 7.907+0.236*clay-0.082*sand+0.441*soc+0.002*(clay*sand)
#         thfc = 33.351+0.020*clay-0.446*sand+1.398*soc+0.052*(sand*soc)-0.077*(clay*soc)+0.011*(clay*sand)
#     return thpwp/100,thfc/100