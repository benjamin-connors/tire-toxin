import os
import gspread
import pandas as pd
from config import credentials

# Define the base directory for metadata files
base_directory = "H:/tire-toxin/data/Discharge/Flowtracker/metadata/"

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

        # Check if submissioncontains flowtracker
        if not (df_ws.loc[df_ws['submissionid'] == submissionid, 'Flow_Tracker'].str.lower() == 'yes').any():
            print(f"Submission {submissionid} has no flowtracker. Skipping.")
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

        # Filter for flowtracker rows
        df_salt_dump = df_submission[pd.to_numeric(df_submission['Salt_Dump.Dump_Number'], errors='coerce').notna()]

        # Select specific columns for salt dump data
        ft_columns = [
            'Flow_Tracker_Details.Start_Time',
            'Flow_Tracker_Details.End_Time',
            'Flow_Tracker_Details.Initial_Stage__Staff_Gauge_',
            'Flow_Tracker_Details.End_Stage__Staff_Gauge_',
            'Flow_Tracker_Details.Initial_Stage__Pressure_Transducer_',
            'Flow_Tracker_Details.End_Stage__Pressure_Transducer_',
            'Flow_Tracker_Details.Initial_Point__Right_Bank_Tie_Point_',
            'Flow_Tracker_Details.Initial_Point__Right_Bank_Tape_Reading_',
            'Flow_Tracker_Details.Initial_Point__Right_Bank_Tie_Point__Photo',
            'Flow_Tracker_Details.End_Point__Left_Bank__Tape_Reading',
            'Flow_Tracker_Details.Other'
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