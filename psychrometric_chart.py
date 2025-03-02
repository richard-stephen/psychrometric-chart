# -*- coding: utf-8 -*-
import numpy as np
import plotly.graph_objects as go
import psychrolib as psy
import pandas as pd
import streamlit as st

# Set psychrolib to SI units
psy.SetUnitSystem(psy.SI)
# Function to calculate humidity ratio



def calc_humidity_ratio(T_db, RH, P):
    P_ws = psy.GetSatVapPres(T_db)  # Saturation vapor pressure
    P_w = RH * P_ws  # Partial pressure of water vapor
    W = 0.621945 * P_w / (P - P_w)  # Humidity ratio
    return W

# Function to generate the psychrometric chart
def generate_psychrometric_chart(df,show_design_zone):
    T_db_room = df['Temperature'].values  # Dry-bulb temperature (°C)
    RH_room = df['Humidity'].values / 100  # Convert % to decimal

    pressure = 101325  # Atmospheric pressure (Pa)
    T_db_min, T_db_max = 0, 50
    T_db = np.linspace(T_db_min, T_db_max, 100)

    # Saturation line (RH = 100%)
    W_sat = [calc_humidity_ratio(t, 1.0, pressure) * 1000 for t in T_db]  # g/kg

    # Room conditions
    W_room = [calc_humidity_ratio(t, rh, pressure) * 1000 for t, rh in zip(T_db_room, RH_room)]  # g/kg

    # Constant RH lines
    RH_levels = [0.2, 0.4, 0.6, 0.8]
    W_RH = {rh: [calc_humidity_ratio(t, rh, pressure) * 1000 for t in T_db] for rh in RH_levels}

    # Comfort zone
    T_comfort = np.array([14, 22])  # °C
    RH_comfort_low = 0.4  # 40% RH
    RH_comfort_high = 0.6  # 60% RH
    W_comfort_low = [calc_humidity_ratio(t, RH_comfort_low, pressure) * 1000 for t in T_comfort]
    W_comfort_high = [calc_humidity_ratio(t, RH_comfort_high, pressure) * 1000 for t in T_comfort]

    # RH labels at T = 35°C
    T_label = 35  # °C
    W_labels = {rh: calc_humidity_ratio(T_label, rh, pressure) * 1000 for rh in RH_levels}

    # Annotations for RH labels
    annotations = [
        dict(
            x=T_label,
            y=W_labels[rh],
            text=f"{int(rh * 100)}%",
            xref="x",
            yref="y",
            showarrow=False,
            font=dict(size=12, color="black"),
            xanchor="center",
            yanchor="bottom",
            yshift=5
        )
        for rh in RH_levels
    ]

    # Create the figure
    fig = go.Figure()

    # Saturation line
    fig.add_trace(go.Scatter(
        x=T_db,
        y=W_sat,
        mode='lines',
        name='100% RH (Saturation)',
        line=dict(color='blue'),
        hovertemplate='T_db: %{x:.1f} °C<br>W: %{y:.2f} g/kg'
    ))

    # Constant RH lines
    for rh, W in W_RH.items():
        fig.add_trace(go.Scatter(
            x=T_db,
            y=W,
            mode='lines',
            name=f'{int(rh*100)}% RH',
            line=dict(dash='dash'),
            hovertemplate='T_db: %{x:.1f} °C<br>W: %{y:.2f} g/kg',
            showlegend = False
        ))

    # Room conditions
    fig.add_trace(go.Scatter(
        x=T_db_room,
        y=W_room,
        mode='markers',
        name='Room Conditions',
        marker=dict(symbol = 'cross', color='red', size=2.0),
        hovertemplate='T_db: %{x:.1f} °C<br>W: %{y:.2f} g/kg'
    ))

    # Comfort zone
    if show_design_zone:
        fig.add_trace(go.Scatter(
            x=[14, 22, 22, 14, 14],
            y=[W_comfort_low[0], W_comfort_low[1], W_comfort_high[1], W_comfort_high[0], W_comfort_low[0]],
            mode='lines',
            name='Design Zone (14-22°C, 40-60% RH)',
            line=dict(color='black', dash='dash', width=2),
            fill = 'toself',
            fillcolor='rgba(10, 10, 240, 0.2)',
            hoverinfo='skip'
        ))

    # Update layout
    fig.update_layout(
        title=dict(text = 'Psychrometric Chart',
        x = 0.5,
        xanchor = 'center'),
        xaxis_title='Dry-Bulb Temperature (°C)',
        yaxis_title='Humidity Ratio (g/kg)',
        xaxis=dict(range=[T_db_min, T_db_max], showgrid=True, gridwidth=1, gridcolor='LightGray', dtick=5),
        yaxis=dict(range=[0, 45], side='right', showgrid=True, gridwidth=1, gridcolor='LightGray', dtick=5),
        legend=dict(
            x=0.01,  # Near the left edge
            y=0.99,  # Near the top edge
            xanchor='left',  # Anchor legend at its left side
            yanchor='top',   # Anchor legend at its top
            bgcolor='rgba(255, 255, 255, 0.8)',  # Optional: semi-transparent white background
            bordercolor='black',  # Optional: border for clarity
            borderwidth=1
        ),
        hovermode='closest',
        template='plotly_white',
        width=1400,  # Increased width for better aspect ratio
        height=800,  # Adjusted height for better aspect ratio
        margin=dict(l=50, r=50, t=100, b=50),
        plot_bgcolor='white',
        shapes=[dict(
            type='rect',
            xref='paper', yref='paper',
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color='black', width=1)
        )],
        annotations=annotations
    )

    return fig

def main():
    st.title("Psychrometric Chart Generator")
    # File uploader
    uploaded_file = st.file_uploader("Upload your Excel file (Temperature and Humidity data)", type=["xlsx"])
    if "show_design_zone" not in st.session_state:
        st.session_state.show_design_zone = False
    if uploaded_file is not None:
        # Read the uploaded file
        df = pd.read_excel(uploaded_file)
        # Check if required columns exist
        if 'Temperature' in df.columns and 'Humidity' in df.columns:
            # Generate and display the chart
            fig = generate_psychrometric_chart(df, st.session_state.show_design_zone)
            st.plotly_chart(fig, use_container_width=True)

            show_design_zone = st.toggle("Show Design Zone")

            # If toggle is changed, update session state and rerun script
            if show_design_zone != st.session_state.show_design_zone:
                st.session_state.show_design_zone = show_design_zone
                st.rerun()

            st.download_button(
                label="Download Chart as HTML",
                data=fig.to_html(),
                file_name="psychrometric_chart.html",
                mime="text/html"
            )
        else:
            st.error("The uploaded file must contain 'Temperature' and 'Humidity' columns.")

    else:
        st.info("Please upload an Excel file to generate the psychrometric chart.")

if __name__ == "__main__":
    main()