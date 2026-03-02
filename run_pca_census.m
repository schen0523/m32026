%% run_pca_census.m
% PCA + visuals for census_clean.csv
% Uses: age_mid, education_years, race, gender, avg_income

clear; clc; close all;

%% 1) Load data
filename = "census_clean.csv";
T = readtable(filename);

fprintf("Loaded %d rows.\n", height(T));
disp("Columns:");
disp(string(T.Properties.VariableNames)');

%% 2) Check required columns
required = ["age_mid","education_years","race","gender","avg_income"];
missing = required(~ismember(required, string(T.Properties.VariableNames)));
if ~isempty(missing)
    error("Missing required column(s): %s", strjoin(cellstr(missing), ", "));
end

%% 3) Target + optional weights
y = T.avg_income;

useWeights = ismember("population_count", string(T.Properties.VariableNames));
if useWeights
    w = T.population_count;
else
    w = [];
end

%% 4) Convert race + gender to categorical if needed
if iscell(T.race) || isstring(T.race)
    T.race = categorical(T.race);
end

if iscell(T.gender) || isstring(T.gender)
    T.gender = categorical(T.gender);
end

raceCats   = categories(T.race);
genderCats = categories(T.gender);

%% 5) One-hot encode (drop reference category)
raceD = dummyvar(T.race);
genD  = dummyvar(T.gender);

% Drop first category of each to avoid multicollinearity
raceD = raceD(:,2:end);
genD  = genD(:,2:end);

% Feature names for labeling plots
featNames = [
    "age_mid"
    "education_years"
    "race_" + string(raceCats(2:end))
    "gender_" + string(genderCats(2:end))
];

%% 6) Build numeric feature matrix
X = [T.age_mid, T.education_years, raceD, genD];

% Remove any bad rows
good = all(isfinite(X),2) & isfinite(y);
X = X(good,:);
y = y(good);

if useWeights
    w = w(good);
end

fprintf("After cleaning: %d rows remain.\n", size(X,1));

%% 7) Standardize
muX = mean(X,1);
sigX = std(X,0,1);
sigX(sigX == 0) = 1;
Xz = (X - muX) ./ sigX;

%% Correlation Heatmap of Input Variables

% Compute correlation matrix
R = corr(X);

figure("Color","w");
imagesc(R);
colorbar;
caxis([-1 1]);   % correlation range
title("Correlation Matrix of Demographic Variables");

% Label axes
xticks(1:numel(featNames));
yticks(1:numel(featNames));
xticklabels(featNames);
yticklabels(featNames);
xtickangle(45);

% Make it cleaner visually
colormap(parula);

%% 8) Run PCA
[coeff, score, latent, ~, explained] = pca(Xz);
cumExplained = cumsum(explained);

k90 = find(cumExplained >= 90, 1, "first");
k95 = find(cumExplained >= 95, 1, "first");

fprintf("Components for 90%% variance: %d\n", k90);
fprintf("Components for 95%% variance: %d\n", k95);

%% 9) Scree plot
figure("Color","w");
pareto(explained);
title("Scree Plot");
xlabel("Principal Component");
ylabel("Percent Variance Explained");

%% 10) Cumulative variance
figure("Color","w");
plot(1:numel(cumExplained), cumExplained, "-o","LineWidth",1.2);
grid on;
yline(90,"--","90%");
yline(95,"--","95%");
title("Cumulative Explained Variance");
xlabel("Number of Components");
ylabel("Cumulative Percent Explained");

%% 11) PC1 vs PC2 colored by income
figure("Color","w");
scatter(score(:,1), score(:,2), 25, y, "filled");
colorbar;
grid on;
title("PC1 vs PC2 (Colored by avg_income)");
xlabel("PC1");
ylabel("PC2");

%% 12) Loadings heatmap
Kshow = min(10, size(coeff,2));
figure("Color","w");
imagesc(coeff(:,1:Kshow));
colorbar;
title("PCA Loadings Heatmap");
xlabel("Principal Component");
ylabel("Feature");
yticks(1:numel(featNames));
yticklabels(featNames);
xticks(1:Kshow);
xticklabels("PC"+string(1:Kshow));

%% 13) Regression: Predict income from PCs
kModel = k90;
Z = score(:,1:kModel);

if useWeights
    mdl = fitlm(Z, y, "Weights", w);
else
    mdl = fitlm(Z, y);
end

disp(mdl);

yhat = predict(mdl, Z);
R2 = 1 - sum((y - yhat).^2) / sum((y - mean(y)).^2);
MAE = mean(abs(y - yhat));

fprintf("Training R^2: %.4f\n", R2);
fprintf("Training MAE: %.2f\n", MAE);

%% 14) Save model
save("pca_income_model.mat", ...
    "featNames","muX","sigX","coeff","explained","kModel","mdl");

disp("Saved pca_income_model.mat");