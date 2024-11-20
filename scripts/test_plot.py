import pandas as pd
import matplotlib.pyplot as plt

plt.ion()

df = pd.read_csv(
    'QQM_CH0_20241001_1442.csv',
    header=2,
    index_col=0,
    parse_dates=True,  # This will parse the index as datetime
    usecols=[0,1,2,3],
    names=['Datetime', 'EC', 'T', 'EC_T'],
    skiprows=0)

print(df)

plt.figure()
plt.plot(df.index, df['EC_T'], marker='o')
plt.ylabel('EC.T(uS/cm)')
plt.title('T-HRECS Radio Test Calibration')
plt.show()