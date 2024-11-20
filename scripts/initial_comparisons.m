data = readtable('chase_upstreamBT_20241029_working.xlsx');

% outlier
ix = data.WaterLevel_m_ > 2 | data.WaterLevel_m_ < -2;
data = data(~ix, :);

data2 =readtable('chase_upstream_20241029_corr.csv');
ix = data2.SensorDepth_BTcorr_Meters_LGRS_N_21157236_ > 2 | data2.SensorDepth_BTcorr_Meters_LGRS_N_21157236_ < -2;
data2 = data2(~ix, :);
ix = isnan(data2.SensorDepth_BTcorr_Meters_LGRS_N_21157236_);
data2 = data2(~ix, :);
data2.DateTime_GMT_08_00.Year = 2024;

%%
close all
figure()
subplot(2,1,1); hold on

title('Water Level Comparison')

plot(data.Date_Time_PDT_, data.WaterLevel_m_, '-b', 'DisplayName', 'chase\_usBT\_HOBO\_BT\_builtin', 'LineWidth', 2)
plot(data.Date_Time_PDT_, data.d2, '--m', 'DisplayName', 'chase\_usBT\_MANUALcorr', 'LineWidth', 2)
plot(data.Date_Time_PDT_, data.d1, '-r', 'DisplayName', 'chase\_us\_MANUALcorr', 'LineWidth', 2)
plot(data2.DateTime_GMT_08_00, data2.SensorDepth_BTcorr_Meters_LGRS_N_21157236_, '--k', 'DisplayName', 'chase\_us\_HOBO\_baro\_corr\_tool', 'LineWidth', 2)

box on;grid on
ylim([0, 0.5])
ylabel('Water Level (m)')
legend

subplot(2,1,2); hold on
title('Differential Pressure Comparison')
plot(data.Date_Time_PDT_, data.DifferentialPressure_kPa_, '-b', 'DisplayName', 'chase\_usBT\_HOBO\_BT\_builtin', 'LineWidth', 2)
plot(data.Date_Time_PDT_, data.diffP2, '--m', 'DisplayName', 'chase\_usBT\_MANUALcorr', 'LineWidth', 2)
plot(data.Date_Time_PDT_, data.DiffP_BT_backcalc, '--c', 'DisplayName', 'chase\_usBT\_BACKCALC', 'LineWidth', 2)

box on; grid on
ylabel('(kPa)')
legend


%% check if it's reference
wl_diff = data.WaterLevel_m_ - data.d2;

figure
plot(data.Date_Time_PDT_, wl_diff, '-r')




