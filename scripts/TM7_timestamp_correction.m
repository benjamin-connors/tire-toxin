% Scratchpad for correcting timestamps on TM7 EC Sensors

%%
% data = readtable('northfield_TM7.537_20241104_2.csv', 'VariableNames', {'Datetime', 'EC', 'T', 'ECT'});
% Read the table, skipping the initial rows
% Read the table, skipping three rows to account for metadata and spacer row

fname = 'QQM_CH0_20241104_1229_baseline_uncorrected.xlsx';

opts = detectImportOptions(fname, 'NumHeaderLines', 3);
opts.SelectedVariableNames = {'DateTime', 'EC_uS_cm_', 'Temp_oC_', 'EC_T_uS_cm_'};
data = readtable(fname, opts);

%%
% timestep difference
dt = diff(data.DateTime);

%% create forced timegrid

tgrid = data.DateTime(1):seconds(5):data.DateTime(end);

% tgrid has 6 less timestamps than datafile, and final timestamp is 3
% seconds before final timestamp on datafile

%% simple fix: remove n linspaced values from timeseries (n = number of extra datapoints in file) and map onto manual timegrid
ix = true(height(data), 1);
rows2remove = round(linspace(1, height(data), height(data)-length(tgrid)));
ix(rows2remove) = false;

data_subset = data(ix, :);
data_subset.DateTime = tgrid';

figure; hold on
plot(data.DateTime, data.EC_T_uS_cm_, '-k', 'DisplayName', 'raw')
plot(data_subset.DateTime, data_subset.EC_T_uS_cm_, '-r', 'DisplayName', 'simple fix')
legend


writetable(data_subset, 'corrected_file.csv')

