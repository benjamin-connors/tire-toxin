import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os
from project_utils import (
    read_stage_file,
    calculate_differential_pressure,
    calculate_water_level,
    save_formatted_stage_file,
    autodetect_stage_site,
    read_baro_file,
)

st.title("CHRL Tire-Toxin Stage Data Processing")

# File upload section
uploaded_file = st.file_uploader("Upload your new data file (Excel format):", type=["xlsx"])

# Define site options
site_options = [
    "",  # Default empty option (None)
    "cat_beacons", "chase_ds", "chase_us", "chase_usBT",
    "northfield_bridge", "northfield_bridgeBT", "northfield_poolBT", "Other"
]

# Initialize detected site
detected_site = None

# Only detect site if a file is uploaded
if uploaded_file is not None:
    detected_site = autodetect_stage_site(uploaded_file)

# Show selectbox only if a file is uploaded
if uploaded_file is not None:
    if detected_site:
        site_name_label = f"Enter site name (Auto-detected: {detected_site} ✅)"
        site_options = [detected_site] + [s for s in site_options if s != detected_site]  # Ensure no duplicates
        site_name = st.selectbox(site_name_label, site_options, index=0)
    else:
        site_name = st.selectbox("Enter site name:", site_options, index=None)

    # Allow manual entry when "Other" is selected
    if site_name == "Other":
        site_name = st.text_input("Please specify the site name:")

if 'process_clicked' not in st.session_state:
    st.session_state.process_clicked = False

def process_clicked():
    st.session_state.process_clicked = True
    
# Create a stats checkbox
stats_checkbox = st.checkbox("Do you want to use statistic data if available?")
if stats_checkbox:
    stats_flag = True
else:
    stats_flag = False

# Display the "Process File" button always
st.button("Process File", on_click=process_clicked)

if uploaded_file is not None and st.session_state.process_clicked:
    # Save the uploaded file temporarily
    temp_file_path = Path(f"temp_{uploaded_file.name}")
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getbuffer())

    # read file
    df_new = read_stage_file(temp_file_path, stats_flag=stats_flag)
    
    st.write(df_new)
    
    # # CORRECTION FOR NORTHFIELD WATER LEVEL (see project data notes)
    # if site_name == 'northfield_poolBT':
    #     correction_time = pd.to_datetime("2024-12-17 13:42:00")
    #     df_new.loc[df_new.index > correction_time, 'Water Level (m)'] += 0.5550484190348302

    # Generate the output file path
    output_directory = Path(r"H:\tire-toxin\data\Discharge\Stage\processed")
    output_filepath = output_directory / f"{site_name}_stage_master.xlsx"

    # Load existing master file or create a new one
    if output_filepath.exists():
        df_master = pd.read_excel(output_filepath, header=0, index_col=0, parse_dates=True)
        df_master.index.name = df_master.index.name or 'Datetime'
        df_master.index = pd.to_datetime(df_master.index, errors='coerce')
        df_unique = df_new[~df_new.index.isin(df_master.index)]
        # CORRECTION FOR NORTHFIELD WATER LEVEL (see project data notes)
        if site_name == 'northfield_poolBT':
            correction_time = pd.to_datetime("2024-12-17 13:42:00")
            df_unique.loc[df_unique.index > correction_time, 'Water Level (m)'] += df_master['Water Level (m)'].iloc[-1]
            st.write(rf'last in master = {df_master['Water Level (m)'].iloc[-1]}')
        df_master = pd.concat([df_master, df_unique])
        is_new_master_file = False
        

        
    else:
        df_master = df_new
        is_new_master_file = True
        st.warning('An existing master file was not found. A new one will be created upon saving.')

    if 'BT' not in site_name:
        # Load appropriate master file with baro data
        df_baro = read_baro_file(site_name)
        if df_baro is not None:
            # Apply barometric pressure correction
            st.write("Applying barometric pressure correction and calculating differential pressure...")
            df_master, corrected_baro_count, failed_baro_count = calculate_differential_pressure(df_master, df_baro)
            st.success(f"- Differential Pressure calculations made: {corrected_baro_count}")
            st.warning(f"- Failed calculations due to missing barometric data: {failed_baro_count}")
            
            # Calculate water level
            st.write("Calculating water level...")
            df_master, corrected_water_level_count = calculate_water_level(df_master)
            st.info(f"- Water Level calculations made: {corrected_water_level_count}")
        else:
            st.warning(f"No BT file with barometric data found for {site_name}, skipping barometric pressure correction.")

    # Handle duplicate timestamps
    len_preclean = len(df_master)
    df_master = df_master.groupby(df_master.index).mean()
    if len_preclean - len(df_master) > 0:
        st.warning(
            f"{len_preclean - len(df_master)} duplicate timestamps were averaged during processing."
        )
        
    # quick removal of fill values
    n_fill = (df_master['Water Level (m)'] < -200).sum() + (df_master['Water Level (m)'] > 10).sum()
    df_master.loc[df_master['Water Level (m)'] < -200, :] = pd.NA
    df_master.loc[df_master['Water Level (m)'] > 10, :] = pd.NA
    st.warning(f'{n_fill} fill values have been removed.')

    # Ensure the combined dataset is sorted
    df_master.sort_index(inplace=True)

    # Completion messages
    if df_unique.empty:
        st.warning('No new data detected!')
    else:
        st.warning(f'{len(df_unique)} new datapoints detected. Click button below to save to master file.')

    if 'Water Level (m)' in df_master.columns:
        st.write("### Water Level Time Series Plot")
        fig, ax = plt.subplots(figsize=(10, 6))

        # If it's new data (no preexisting master file), plot only the new data
        if is_new_master_file:
            df_master['Water Level (m)'].plot(ax=ax, label="Water Level (New)", color='red', alpha=0.7)
        else:
            # Plot preexisting data (blue)
            df_master.loc[~df_master.index.isin(df_unique.index), 'Water Level (m)'].plot(ax=ax, label="Water Level (Existing)", color='blue', alpha=0.7)

            # Plot new data (red) if there are any new data points
            if not df_unique.empty:
                df_master.loc[df_master.index.isin(df_unique.index), 'Water Level (m)'].plot(ax=ax, label="Water Level (New)", color='red', alpha=0.7)

        ax.set_title(f"Water Level Time Series for {site_name}")
        ax.set_xlabel("Datetime")
        ax.set_ylabel("Water Level (m)")
        ax.legend()

        st.pyplot(fig)

    if st.button(f"Save to {site_name} Master Stage File"):
        os.makedirs(output_directory, exist_ok=True)
        # save_formatted_excel(df_master, output_filepath)
        save_formatted_stage_file(df_master, output_filepath)
        st.success(f"Subset saved to {output_filepath}")
