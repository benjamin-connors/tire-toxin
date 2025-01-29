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