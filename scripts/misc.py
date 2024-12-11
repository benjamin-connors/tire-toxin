import pandas as pd
import matplotlib.pyplot as plt

# Load data with index_col=0 and parse dates
df = pd.read_excel(r'H:\tire-toxin\data\Stage\processed\chase_us_stage_master.xlsx', index_col=0, parse_dates=True)
dfBT = pd.read_excel(r"H:\tire-toxin\data\Stage\processed\chase_us_stage_master.xlsx", index_col=0, parse_dates=True)

# Plotting
plt.figure(figsize=(10, 6))

# Plot Water Level from both dataframes
plt.plot(df.index, df['Water Level (m)'], color='red', label='Water Level (df)', linewidth=2)
plt.plot(dfBT.index, dfBT['Water Level (m)'], color='blue', label='Water Level (dfBT)', linewidth=2, linestyle='--')

# Adding labels and title
plt.xlabel('Date')
plt.ylabel('Water Level (m)')
plt.title('BT vs non-BT Water Level Comparison After Manual Baro-Correction and Water Level Calc (chase_us)')

plt.ylim((0, 1.5))

# Display legend
plt.legend()

# Show the plot
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.tight_layout()  # Adjust layout to avoid clipping
plt.show()
