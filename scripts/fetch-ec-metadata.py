import os
import gspread
import pandas as pd
from config import credentials

# Define the base directory for metadata files
base_directory = "H:/tire-toxin/data/Discharge/Manual_salt/metadata/"

# List all existing metadata files 
existing_files = []
for root, dirs, files in os.walk(base_directory):
    existing_files.extend(files)

# Connect to Google Sheets
gc = gspread.service_account_from_dict(credentials)

# Open the Google Sheet by URL
sheet_url = "https://docs.google.com/spreadsheets/d/1JLbDJq4qAfAyzEpOuxYYjhfXd4FxvotUc8JaBCsSdKE/edit?gid=748389405"
sh = gc.open_by_url(sheet_url)

# Loop through all worksheets
for ws in sh.worksheets():
    # Read worksheet into DataFrame
    df_ws = pd.DataFrame(ws.get_all_records())
    
    # Loop through unique 'submissionid' in df_ws
    for submissionid in df_ws['submissionid'].unique():

        # Check if submissioncontains salt dilution
        if not (df_ws.loc[df_ws['submissionid'] == submissionid, 'Salt_Dilution'].str.lower() == 'yes').any():
            print(f"Submission {submissionid} has no salt dilution. Skipping.")
            continue  # Skip this submission

        # Check if a metadata file for this submissionid already exists
        if any(str(submissionid) in file for file in existing_files):
            print(f"Metadata for submissionid {submissionid} already exists. Skipping.")
            continue  # Skip this submission if the file exists

        # Filter the DataFrame by the current 'submissionid'
        df_submission = df_ws[df_ws['submissionid'] == submissionid]

        # Extract the necessary variables (Assumption: values are the same across all rows for a submissionid)
        site = df_submission['Site_Name'].iloc[0]
        time = df_submission['Arrival_Time_to_Site'].iloc[0]
        weather = df_submission['Weather_Context'].iloc[0]
        visit_notes = df_submission['Notes'].iloc[0]

        # Extract sensor serials for each location
        baseline_sensor = ', '.join(df_submission[df_submission['Sensor_Setup.Sensor_Locations'] == 'Baseline']['Sensor_Setup.Sensor_Serial'].unique())
        rl_sensor = ', '.join(df_submission[df_submission['Sensor_Setup.Sensor_Locations'] == 'RL']['Sensor_Setup.Sensor_Serial'].unique())
        rr_sensor = ', '.join(df_submission[df_submission['Sensor_Setup.Sensor_Locations'] == 'RR']['Sensor_Setup.Sensor_Serial'].unique())
        rm_sensor = ', '.join(df_submission[df_submission['Sensor_Setup.Sensor_Locations'] == 'RM']['Sensor_Setup.Sensor_Serial'].unique())

        # Handle 'Other' location (extract sensor serials for non-empty 'Other_Location')
        other_sensor_rows = df_submission[df_submission['Sensor_Setup.Other_Location'].str.strip() != '']
        other_sensor = ', '.join(other_sensor_rows['Sensor_Setup.Sensor_Serial'].unique())
        other_sensor = other_sensor if other_sensor else None

        # Filter rows where 'Salt_Dump.Dump_Number' is numeric
        df_salt_dump = df_submission[pd.to_numeric(df_submission['Salt_Dump.Dump_Number'], errors='coerce').notna()]

        # Select specific columns for salt dump data
        salt_dump_columns = [
            'Salt_Dump.Dump_Number', 
            'Salt_Dump.Time_of_Salt_Dump', 
            'Salt_Dump.Quantity_of_Salt_Dumped', 
            'Salt_Dump.Staff_Gauge_Reading', 
            'Salt_Dump.Water_Level__Pressure_Sensor_', 
            'Salt_Dump.Dump_Notes'
        ]
        
        # Keep columns for writing to metadata file
        df_salt_dump = df_salt_dump[salt_dump_columns]

        # Rename columns for writing to file
        df_salt_dump.columns = [
            'Dump Number', 'Dump Time', 'Salt Mass (g)', 
            'Staff Gauge', 'PT Sensor', 'Dump Notes'
        ]

        # Extract all 'Photo_X' columns and concatenate URLs into one variable
        photo_links = []
        photo_cols = [col for col in df_submission.columns if col.startswith('Photo_')]  # Identify 'Photo_X' columns
        # Check 'Photos_of_Site' column for photo URLs
        if 'Photos_of_Site' in df_submission.columns:
            photo_cols.append('Photos_of_Site')

        for col in photo_cols:
            # Get the unique photo URL(s) for the current column
            photo_urls = df_submission[col].unique()
            # Assuming one URL per photo column, you can just add it to the list
            if len(photo_urls) == 1 and photo_urls[0] != '':
                photo_links.append(photo_urls[0])

        # Prepare output file path
        output_directory = f"H:/tire-toxin/data/Discharge/Manual_salt/metadata/{site}"
        os.makedirs(output_directory, exist_ok=True)
        date_str = pd.to_datetime(time, errors='coerce').strftime('%Y%m%d')
        file_name = f"{site}_{date_str}_metadata_{submissionid}.xlsx"
        output_file = os.path.join(output_directory, file_name)
        
        # Write all this information into an Excel file
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Write 'submissionid' to A1 and the actual submissionid to B1
            metadata = pd.DataFrame({
                'A': ['submissionid:', 'Date:', 'Location:', 'Weather:', 'Visit Notes:', 'Photo Links:'],
                'B': [str(submissionid), time, site, weather, visit_notes, None]  # Leave Photo Links row empty for now
            })
            metadata.to_excel(writer, sheet_name='Metadata', startrow=0, index=False, header=False)

            # Write sensor location data (Baseline, RL, RM, RR, Other) starting from row 6
            sensor_data = pd.DataFrame({
                'A': ['Baseline Sensors:', 'RL Sensors:', 'RM Sensors:', 'RR Sensors:', 'Other Sensors:'],
                'B': [baseline_sensor, rl_sensor, rm_sensor, rr_sensor, other_sensor]
            })
            sensor_data.to_excel(writer, sheet_name='Metadata', startrow=7, index=False, header=False)


            # Drop duplicate and write the salt dump data to metadata file
            df_salt_dump = df_salt_dump.drop_duplicates()
            df_salt_dump = df_salt_dump.astype(str)  # Convert all columns to strings
            df_salt_dump.to_excel(writer, sheet_name='Metadata', startrow=13, index=False)

            # Write photo links to separate columns in the same row as "Photo Links:"
            worksheet = writer.sheets['Metadata']
            photo_start_col = 1  # Start writing photo links from column C (Excel column index = 2)
            for col_num, link in enumerate(photo_links, start=photo_start_col):
                worksheet.write_url(5, col_num, link, string=f'Photo {col_num - photo_start_col + 1}')  # Row 5 is "Photo Links:"

            # Access the worksheet to set column widths
            worksheet.set_column('A:F', max(df_ws['Site_Name'].apply(lambda x: len(str(x))).max(), 20))  # Automatically set column width

        print(f"Metadata for submissionid {submissionid} in worksheet '{ws.title}' has been written to {output_file}.")
