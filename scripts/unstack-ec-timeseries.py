import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# REAL DATA
filename = 'test_data/unstack-ec-timeseries/QQM_CH0_20241217_1051.xlsx'
df_original = pd.read_excel(filename, skiprows=3)

# Only keep the relevant columns
df_original = df_original[['DateTime', 'EC(uS/cm)',	'Temp(oC)',	'EC.T(uS/cm)']]
df_original['DateTime'] = pd.to_datetime(df_original['DateTime'])

# Identify duplicated timestamps (stacked data points)
duplicated_timestamps = df_original[df_original.duplicated('DateTime', keep=False)]

if duplicated_timestamps.empty:
    print('No duplicated timestamps detected.')
else:
    # Initialize the corrected DataFrame as a copy of the original
    df_corrected = df_original.copy()

    # Iterate through each duplicated timestamp range
    for i in range(len(duplicated_timestamps)):
        stacked_start_index = duplicated_timestamps.index[i]

        # Find the first duplicated timestamp and the preceding timestamp
        gap_start = df_original['DateTime'].iloc[stacked_start_index - 1]
        gap_end = df_original['DateTime'].iloc[stacked_start_index]
        gap_duration = (gap_end - gap_start).total_seconds()

        # Print gap details
        print(f"\nGap Start: {gap_start}")
        print(f"Gap End: {gap_end}")
        print(f"Gap Duration (seconds): {gap_duration}")

        # Create a 5-second time grid across the gap
        time_grid = pd.date_range(gap_start + pd.Timedelta(seconds=5), gap_end, freq='5S')

        # Unstack the stacked data for all columns
        for column in ['EC(uS/cm)',	'Temp(oC)',	'EC.T(uS/cm)']:
            stacked_data = df_original.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, column].values
            # Update the corrected DataFrame with the unstacked data
            df_corrected.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, "DateTime"] = time_grid
            df_corrected.loc[stacked_start_index:stacked_start_index + len(time_grid) - 1, column] = stacked_data

    # Plot the original and corrected time series with x-axis in minutes:seconds for 'EC.T(uS/cm)'
    plt.figure(figsize=(10, 6))
    plt.plot(df_original['DateTime'], df_original['EC.T(uS/cm)'], label="Original EC.T(uS/cm)", color='red', linestyle='--')
    plt.plot(df_corrected['DateTime'], df_corrected['EC.T(uS/cm)'], label="Corrected EC.T(uS/cm)", color='blue')

    # Format x-axis to display time as minutes:seconds
    # plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%M:%S'))

    plt.xlabel('Time')
    plt.ylabel('Electrical Conductivity (EC.T(uS/cm))')
    plt.title('Original vs Corrected EC Time Series')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
    plt.show()

    # Create a DataFrame to hold both uncorrected and corrected data for all variables
    df_comparison = pd.DataFrame({
        "Uncorrected Time": df_original['DateTime'],
        "Uncorrected EC.T(uS/cm)": df_original['EC.T(uS/cm)'],
        "Corrected Time": df_corrected['DateTime'],
        "Corrected EC.T(uS/cm)": df_corrected['EC.T(uS/cm)'],
        "Uncorrected Temp_oC_": df_original['Temp_oC_'],
        "Corrected Temp_oC_": df_corrected['Temp_oC_'],
        "Uncorrected EC_T_uS_cm_": df_original['EC_T_uS_cm_'],
        "Corrected EC_T_uS_cm_": df_corrected['EC_T_uS_cm_']
    })

    # Save the comparison table to an Excel file
    output_filename = "comparison_table_multiple_gaps_real_data.xlsx"
    df_comparison.to_excel(output_filename, index=False)

    # Print the comparison table
    print("\nComparison Table (Uncorrected vs Corrected Data):")
    print(df_comparison.head())  # Print first few rows for inspection
