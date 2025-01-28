import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os
from project_utils import (
    format_and_save_excel,
    determine_file_type_and_site
)

def main():
    st.title("CHRL Tire-Toxin Stage Data Processing")

    # File upload section
    uploaded_file = st.file_uploader("Upload your new data file (Excel format):", type=["xlsx"])

    # Dropdown menu for site name
    site_options = [
        "",  # Default empty option
        "cat_beacons", "chase_ds", "chase_us", "chase_usBT",
        "northfield_bridge", "northfield_bridgeBT", "northfield_poolBT", "Other"
    ]
    user_site_choice = st.selectbox("Select a site name (leave blank for auto-detection):", options=site_options)

    # Initialize user_site_name as None
    user_site_name = None

    # Allow text input for "Other"
    if user_site_choice == "Other":
        user_site_name = st.text_input("Enter a site name (leave blank for auto-detection):")
        if user_site_name.strip() == "":
            user_site_name = None
    elif user_site_choice != "":
        user_site_name = user_site_choice

    # Display the "Process File" button always (regardless of file upload)
    process_button_clicked = st.button("Process File")

    if uploaded_file is not None and process_button_clicked:
        # Save the uploaded file temporarily
        temp_file_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(uploaded_file.getbuffer())

        # Determine file type, site, and output file
        df_new, site_name, file_type, output_file, bt_file = determine_file_type_and_site(temp_file_path)

        # Use user-provided site name if given
        if user_site_name:
            site_name = user_site_name

        # Load existing master file or create a new one
        if output_file.exists():
            df_master = pd.read_excel(output_file, header=0, index_col=0, parse_dates=True)
            df_master.index.name = df_master.index.name or 'Datetime'
            df_unique = df_new[~df_new.index.isin(df_master.index)]
            df_combined = pd.concat([df_master, df_unique])
            st.success(f"{len(df_unique)} new data points added to the master file.")
        else:
            st.success(f"Creating a new master file for {site_name}.")
            df_combined = df_new

        # Ensure the combined dataset is sorted
        df_combined.sort_index(inplace=True)

        # Plot the Water Level time series with existing and new data
        st.write("### Water Level Time Series Plot")
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot Water Level data from the master file (existing data)
        if 'df_master' in locals():
            df_master['Water Level (m)'].plot(ax=ax, label="Existing Data", color='blue', alpha=0.7)

        # Plot Water Level data from the new uploaded file
        if 'df_unique' in locals() and not df_unique.empty:
            df_unique['Water Level (m)'].plot(ax=ax, label="New Data", color='red', alpha=0.9)

        # Add title and labels
        ax.set_title(f"Water Level Time Series for {site_name}")
        ax.set_xlabel("Datetime")
        ax.set_ylabel("Water Level (m)")
        ax.legend()

        # Show the plot in Streamlit
        st.pyplot(fig)

        # Hardcoded output file path
        formatted_date = pd.to_datetime('today').strftime("%Y%m%d")
        output_directory = f"H:/tire-toxin/data/Discharge/Stage/processed"
        os.makedirs(output_directory, exist_ok=True)  # Ensure the directory exists

        output_file = f"{output_directory}/{site_name}_{formatted_date}_stage_master.xlsx"

        if st.button("Save Combined Dataset"):
            try:
                # Save the combined dataset using the format_and_save_excel function
                format_and_save_excel(df_combined, Path(output_file))
                st.success(f"File saved successfully at: {output_file}")
            except Exception as e:
                st.error(f"Error saving file: {e}")

    elif uploaded_file is None and process_button_clicked:
        st.warning("Please upload a file before clicking the Process button.")

if __name__ == "__main__":
    main()
