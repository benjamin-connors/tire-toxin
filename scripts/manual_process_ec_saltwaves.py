from select_saltwaves import select_saltwaves

# User-defined variables for manual processing
file_path = r'H:\tire-toxin\data\EC\20241106\raw\QQM_CH0_20241106_1307.xlsx'  # Replace with your actual file path
stn = 'TEST'  # User-defined station name
sensor_location = 'RL'  # User-defined location
initial_dump_number = 1  # User-defined initial dump number

# Call the base function to process the file
select_saltwaves(file_path, stn, sensor_location, initial_dump_number)
