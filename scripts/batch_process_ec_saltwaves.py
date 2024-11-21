import os
from select_saltwaves import select_saltwaves

# Specify the folder containing the .xlsx files to be processed
data_directory = r'H:\tire-toxin\data\EC\20241106\raw'  # Use raw string for Windows paths

# Determine the output directory as one level up from `raw`, renamed to `processed`
output_directory = os.path.join(os.path.dirname(data_directory), 'processed')
os.makedirs(output_directory, exist_ok=True)  # Ensure the output directory exists

# Get list of all .xlsx files in the target directory
files = [f for f in os.listdir(data_directory) if f.endswith('.xlsx')]

# Loop through all .xlsx files in the directory
for file in files:
    file_path = os.path.join(data_directory, file)
    
    # Prompt user whether to process the file
    process_file = input(f"Would you like to process the file {file}? (y/n): ").strip().lower()
    
    if process_file == 'y':  # Proceed with processing
        # Prompt for station name
        stn = input(f"Enter station name for {file}: ").strip()
        
        # Prompt for sensor location
        sensor_location = input(f"Enter sensor location for {file} (e.g., RR, RL, baseline): ").strip()
        
        if sensor_location.lower() == 'baseline':
            # Prompt for date, leave blank for automatic detection
            date = input(f"Enter date for {file} (leave blank for automatic detection): ").strip()
            
            # Prompt for sensor name, leave blank for automatic detection
            sensor_name = input(f"Enter sensor name for {file} (leave blank for automatic detection): ").strip()
            
            # Call the base function for baseline processing
            select_saltwaves(
                file_path, 
                stn, 
                sensor_location, 
                date=date, 
                sensor_name=sensor_name, 
                output_directory=output_directory
            )
            print(f"Baseline file {file} processed and saved.")
        
        else:
            # Prompt for initial dump number
            initial_dump_number = input(f"Enter initial dump number for {file} (default 1): ")
            initial_dump_number = int(initial_dump_number) if initial_dump_number else 1
            
            # Prompt for date, leave blank for automatic detection
            date = input(f"Enter date for {file} (leave blank for automatic detection): ").strip()
            
            # Prompt for sensor name, leave blank for automatic detection
            sensor_name = input(f"Enter sensor name for {file} (leave blank for automatic detection): ").strip()
            
            # Call the base function for interactive selection
            select_saltwaves(
                file_path, 
                stn, 
                sensor_location, 
                initial_dump_number=initial_dump_number, 
                date=date, 
                sensor_name=sensor_name, 
                output_directory=output_directory
            )
            print(f"File {file} processed and saved.")
    else:
        print(f"Skipping {file}.")
