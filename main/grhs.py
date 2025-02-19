import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Note: This function to generate the water balance plot is provided as a reference for the final project and need to make adjustments as needed. 

def dr_plot(df):

    # This dr_plot function is used to calculate the soil depletion and adjust it based on rain and irrigation events. Native pyfao56 provide daily depletion values considering every influx and efflux.
    # We made adjustments to the depletion calculation to show the effect of rain and irrigation on the soil depletion and is actually at a lag of one day.
    df1 = df[['Dr','Rain','Irrig', "IrrLoss"]].copy().reset_index()

    # Create a new DataFrame for tracking multiple points on the same day
    plot_data = []

    # Initialize variables
    previous_row = None  # This will hold the previous day's row

    for _, row in df1.iterrows():
        day = row["index"]
        try:
            depletion = previous_row['Dr']  # Use the previously calculated depletion
        except:
            depletion = 0.

        # Base depletion point
        plot_data.append({"day": day, "value": depletion, "type": "depletion"})

        # Adjusted depletion for rain
        if row["Rain"] > 0:
            depletion_after_rain = max(depletion - row["Rain"], 0)
            plot_data.append({"day": day, "value": depletion_after_rain, "type": "hrain"})
            depletion = depletion_after_rain  # Update depletion after rain

        # Adjusted depletion for irrigation
        if row["Irrig"] > 0:
            depletion_after_irrigation = max(depletion - row["Irrig"] + row['IrrLoss'], 0)
            plot_data.append({"day": day, "value": depletion_after_irrigation, "type": "irrigation"})
            depletion = depletion_after_irrigation  # Update depletion after irrigation

        # Store the current row as the previous row for the next iteration
        previous_row = row

    # Convert to a DataFrame
    plot_df = pd.DataFrame(plot_data)

    # Sort by day and type to ensure correct plotting order
    #Although could simply define single depletion variable but this is to show the process of depletion calculation
    return plot_df.sort_values(by=["day", "type"])


def wb_plot_interactive(results, save_plot=False, plot_name="wb_plot.html"):
    """
    Creates an interactive Plotly plot for water balance components and optionally saves the plot as HTML.
    """
    dr_df = dr_plot(results)

    # Create subplots with secondary y-axes where needed
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,

        specs=[[{"secondary_y": True}],  # First subplot with secondary y-axis
               [{"secondary_y": True}],  # Second subplot with secondary y-axis
               [{"secondary_y": False}]]  # Third subplot without secondary y-axis
    )

    # --------------------------------------------
    # First subplot (Ks, ETc, and adjusted ETc)
    # --------------------------------------------
    fig.add_trace(go.Scatter(x=results.index, y=results['ETc'], mode='lines', name='ETc', line=dict(color='coral')),
                   row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=results.index, y=results['ETa'], mode='lines', name='ETc adj', line=dict(color='olive')),
                  row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=results.index, y=results['Ks'], mode='lines', name='Ks', line=dict(color='green', dash='dot')),
                  row=1, col=1, secondary_y=True)

    # --------------------------------------------
    # Second subplot (Rainfall, Irrigation, and Runoff)
    # --------------------------------------------
    fig.add_trace(go.Bar(x=results.index, y=results['Rain'], name='Rainfall', marker=dict(color='dodgerblue', opacity=0.6)),
                  row=2, col=1, secondary_y=False)
    fig.add_trace(go.Bar(x=results.index, y=results['Irrig'] - results['IrrLoss'], name='Irrigation',
                         marker=dict(color='green', opacity=0.6)),
                  row=2, col=1, secondary_y=False)
    fig.add_trace(go.Bar(x=results.index, y=results['Runoff'], name='Runoff', marker=dict(color='yellow')),
                  row=2, col=1, secondary_y=True)

    # --------------------------------------------
    # Third subplot (TAW, RAW, soil depletion, and percolation)
    # --------------------------------------------
    fig.add_trace(go.Scatter(x=results.index, y=results['TAW'], mode='lines', name='TAW', line=dict(color='blue')),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=results.index, y=results['RAW'], mode='lines', name='RAW', line=dict(color='darkslategrey')),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=dr_df['day'], y=dr_df['value'], mode='lines', name='Dr', line=dict(color='red'), opacity=0.7),
                  row=3, col=1)
    fig.add_trace(go.Bar(x=results.index, y=results['DP'], name='Percolation', marker=dict(color='goldenrod')),
                  row=3, col=1)

    # --------------------------------------------
    # Invert Y-axis for the third subplot
    # --------------------------------------------
    fig.update_yaxes(autorange="reversed", row=3, col=1)

    # --------------------------------------------
    # Layout adjustments
    # --------------------------------------------
    fig.update_layout(
        height=800,
        title_text="Water Balance Components",
        legend_title="Components",
        template="plotly_white",
    )

    # Set axis labels for this subplot
    tick_vals = results.index.to_list()
    #Note: This is a simple way to get the tick labels, but it may not be the best for all cases
    # tick_vals = list(range(int(results.index[0].split('-')[1]),
    #                        int(results.index[-1].split('-')[1])+1, 10))
    tick_labels = [day.split('-')[1] for day in results.index]

    fig.update_xaxes(tickvals=tick_vals, ticktext=tick_labels, 
                     title="Day of Year (DOY)", row=3, col=1)
    # Axis labels for primary y-axes
    fig.update_yaxes(title_text='ETc & ETc adj. (mm)', row=1, col=1)
    fig.update_yaxes(title_text='Rainfall & Irrigation (mm)', row=2, col=1)
    fig.update_yaxes(title_text='TAW, RAW, Dr & DP (mm)', row=3, col=1)
    # Axis labels for secondary y-axes
    fig.update_yaxes(title_text="Ks", secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="Runoff (mm)", secondary_y=True,  row=2, col=1)

    # Save the plot as HTML if required
    if save_plot:
        fig.write_html(plot_name)

    # Return raw HTML string for embedding
    return fig.to_html(full_html=False)
