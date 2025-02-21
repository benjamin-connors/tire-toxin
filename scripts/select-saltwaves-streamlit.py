import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font
from project_utils import get_salt_dump_times


# Title of the app
st.title("CHRL Saltwave Selection")

# File upload widget
uploaded_file = st.file_uploader("Upload your Excel file", type="xlsx")

# Processing the file if uploaded
if uploaded_file is not None:
    # First try reading just the headers to detect file format
    df_preview = pd.read_excel(uploaded_file, nrows=0)

    if 'EC.T' in df_preview.columns:
        # File Type 1: Headers in the first row
        uploaded_file.seek(0)  # Reset file pointer
        df = pd.read_excel(uploaded_file)

        # Column Mapping for File Type 1
        df.rename(columns={
            'DT': 'Datetime',        # Rename DT to Datetime
            'EC': 'EC',              # Rename EC to EC
            'RTCTmp': 'Temp',        # Rename RTCTmp to Temp
            'EC.T': 'EC.T'           # Keep EC.T as EC.T
        }, inplace=True)
        
        # Auto-detect sensor name from file path (File Type 1)
        if 'AT' in uploaded_file.name:
            start_idx = uploaded_file.name.find('AT')
            sensor_name = uploaded_file.name[start_idx:start_idx + 5]
        else:
            sensor_name = None  # User will specify later if not detected

    elif 'EC.T(uS/cm)' in df_preview.columns:
        # File Type 2 (headers removed before upload)
        uploaded_file.seek(0)  # Reset file pointer
        df = pd.read_excel(uploaded_file)

        # Column Mapping for File Type 2 (headers removed before upload)
        df.rename(columns={
            'DateTime': 'Datetime',              # Rename DateTime to Datetime
            'EC(uS/cm)': 'EC',                  # Rename EC(uS/cm) to EC
            'Temp(oC)': 'Temp',                 # Rename Temp(oC) to Temp
            'EC.T(uS/cm)': 'EC.T'               # Rename EC.T(uS/cm) to EC.T
        }, inplace=True)

    else:
        # Try File Type 2: Headers in row 4
        uploaded_file.seek(0)  # Reset file pointer
        df_preview = pd.read_excel(uploaded_file, header=3, nrows=0)

        if 'EC.T(uS/cm)' in df_preview.columns:
            uploaded_file.seek(0)  # Reset file pointer
            df = pd.read_excel(uploaded_file, header=3)

            # Column Mapping for File Type 2
            df.rename(columns={
                'DateTime': 'Datetime',              # Rename DateTime to Datetime
                'EC(uS/cm)': 'EC',                  # Rename EC(uS/cm) to EC
                'Temp(oC)': 'Temp',                 # Rename Temp(oC) to Temp
                'EC.T(uS/cm)': 'EC.T'               # Rename EC.T(uS/cm) to EC.T
            }, inplace=True)

            # Auto-detect sensor name from A2 cell (File Type 2)
            df_meta = pd.read_excel(uploaded_file, header=None, nrows=2)
            sensor_name = df_meta.iloc[1, 0]  # Cell A2 value
        else:
            st.error("The uploaded file doesn't match any expected format. Please ensure it contains either 'EC.T' or 'EC.T(uS/cm)' columns.")
            st.stop()

    # remove unwanted columns amd arrange in desired order
    df = df[['Datetime', 'EC.T', 'EC', 'Temp']]
    # Define the datetime column (dt_col)
    dt_col = 'Datetime'  # Now it's 'Datetime' after renaming
    df[dt_col] = pd.to_datetime(df['Datetime'], errors='coerce')

    # Extract the first timestamp as a date string for file naming
    first_timestamp = df[dt_col].iloc[0]
    date_str = first_timestamp.strftime('%Y%m%d')

    # Detect duplicated timestamps
    duplicated_timestamps = df[df.duplicated('Datetime', keep=False)]

    if not duplicated_timestamps.empty:
        st.warning("Duplicated timestamps detected. Would you like to apply a correction?")
        proceed_with_correction = st.radio("Apply correction?", ['Yes', 'No'])

        if proceed_with_correction == 'Yes':
            # Correction routine based on your provided script
            df_original = df.copy()
            df_corrected = df.copy()

            for i in range(len(duplicated_timestamps)):
                stacked_start_index = duplicated_timestamps.index[i]
                gap_start = df_original['Datetime'].iloc[stacked_start_index - 1]
                gap_end = df_original['Datetime'].iloc[stacked_start_index]
                time_grid = pd.date_range(gap_start + pd.Timedelta(seconds=5), gap_end, freq='5s')

                # Unstack the duplicated data
                for column in ['EC', 'Temp', 'EC.T']:
                    stacked_data = df_original.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, column].values
                    df_corrected.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, 'Datetime'] = time_grid
                    df_corrected.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, column] = stacked_data

            # Display correction applied
            st.success("Correction applied. Please review the result in the figure below.")

            # Plot the original vs corrected data
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df_original['Datetime'], df_original['EC.T'], label="Original EC.T(uS/cm)", color='red', linestyle='--')
            ax.plot(df_corrected['Datetime'], df_corrected['EC.T'], label="Corrected EC.T(uS/cm)", color='blue')
            ax.set_xlabel('Time')
            ax.set_ylabel('Electrical Conductivity (EC.T(uS/cm))')
            ax.set_title('Original vs Corrected EC Time Series')
            ax.legend()
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)

            proceed_with_corrected_data = st.radio("Are you happy with the correction?", ['Yes', 'No'])
            if proceed_with_corrected_data == 'Yes':
                st.success("Proceeding with the corrected data.")
                # Proceed with the corrected data to the next part of the app
                df = df_corrected
            elif proceed_with_corrected_data == 'No':
                st.warning("Correction aborted. Proceeding with the original data.")
                df = df_original
        else:
            st.warning("Correction not applied. Proceeding with the original data.")

    else:
        st.success("No duplicated timestamps found. Proceeding with the original data.")

    # Dynamic Inputs Section (appears after file upload)
    st.subheader("User Inputs")
    
    # Station Name
    stn = st.selectbox("Enter station name", ['chase_bridge', 'northfield', 'cat_beacons', 'Other'], index=None)
    if stn == "Other":
        stn = st.text_input("Please specify the station name")

    # Sensor Location
    sensor_loc = st.selectbox("Enter sensor location", ['baseline', 'RL', 'RR', 'RM', 'RMrock', 'Other'], index=None)
    if sensor_loc == "Other":
        sensor_loc = st.text_input("Please specify the sensor location")

    # Sensor Name (auto-detected or user input)
    if sensor_name:
        sensor_name_label = f"Enter sensor name (auto-detected: {sensor_name} ✅)"
        sensor_name = st.selectbox(
            sensor_name_label,
            [sensor_name] + ["AT200", "AT201", "AT202", "AT203", "TM7.537", "TM7.538"]
        )
    else:
        sensor_name = st.selectbox("Enter sensor name", ["AT200", "AT201", "AT202", "AT203", "TM7.537", "TM7.538", "Other"], index=None)
        if sensor_name == "Other":
            sensor_name = st.text_input("Please specify the sensor name")
           
            
    # Get the min and max datetime values from the dataframe
    min_time = df[dt_col].min()
    max_time = df[dt_col].max()
    
    # get times  of salt dumps from metadat
    if stn and stn != "Other":
        salt_dump_times = get_salt_dump_times(stn)
        filtered_salt_dump_times = [sdt for sdt in salt_dump_times if min_time <= sdt <= max_time]
    else:
        filtered_salt_dump_times = []
       
    # Plot the data
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the time series (using the detected EC column)
    ec_col = 'EC.T'
    ax.plot(df[dt_col], df[ec_col], label=f"{ec_col} vs Time")
    ax.set_xlabel('Time')
    ax.set_ylabel(ec_col)
    ax.grid(True)

    # Plot vertical lines for each salt dump time within the selected range
    for sdt in filtered_salt_dump_times:
        ax.axvline(x=sdt, color='red', linestyle='--', label="Salt Dump")

    # Use select_slider with human-readable labels
    start_time, end_time = st.select_slider(
        "Select time range",
        options=df[dt_col],
        value=(min_time, max_time),
        format_func=lambda x: x.strftime('%Y-%m-%d %H:%M:%S')
    )

    # Highlight the selected range on the plot
    ax.axvspan(start_time, end_time, color='orange', alpha=0.3, label="Selected Range")
    ax.legend()

    # Show plot in Streamlit
    st.pyplot(fig)

    # Editable current dump counter
    current_dump = st.text_input("Current dump counter", value=None)

    # Filter data based on selected time range
    filtered_df = df[(df[dt_col] >= start_time) & (df[dt_col] <= end_time)]

    # User-defined output directory
    output_directory = st.text_input('\Hydrology_Shared Output Directory', value=f"H:\\tire-toxin\\data\\Discharge\\Manual_salt\\EC\\processed\\{stn}\\{date_str}")

    # Generating the filename with dynamic elements
    if sensor_loc != 'baseline':
        filename = f"{stn}_{date_str}_dump{current_dump}_{sensor_loc}_{sensor_name}.xlsx"
    else:
        filename = f"{stn}_{date_str}_{sensor_loc}_{sensor_name}.xlsx"
    output_file = os.path.join(output_directory, filename)

    # Option to save the subset as a new Excel file
    if st.button(f"Save {filename} to \Hydrology_Shared"):
        os.makedirs(output_directory, exist_ok=True)
        filtered_df.to_excel(output_file, index=False)
        st.success(f"Subset saved to {output_file}")
