%% run_income_regression.m
% Multivariate regression for income estimation (NO PCA)
% Requires census_clean.csv with columns:
%   age_mid (numeric)
%   education_years (numeric)
%   race (text/categorical)
%   gender (text/categorical)
%   avg_income (numeric)
% Optional:
%   population_count (numeric) for weighted regression

clear; clc; close all;

%% 1) Load data
filename = "census_clean.csv";   % change to full path if needed
Traw = readtable(filename);

fprintf("Loaded %d rows and %d columns.\n", height(Traw), width(Traw));
disp("Columns:");
disp(string(Traw.Properties.VariableNames)');

%% 2) Check required columns
required = ["age_mid","education_years","race","gender","avg_income"];
missing = required(~ismember(required, string(Traw.Properties.VariableNames)));
if ~isempty(missing)
    error("Missing required column(s): %s", strjoin(cellstr(missing), ", "));
end

%% 3) Clean + keep only needed columns
T = Traw(:, intersect(Traw.Properties.VariableNames, ...
    ["age_mid","education_years","race","gender","avg_income","population_count"], "stable"));

% Response
y = T.avg_income;

% Optional weights
useWeights = ismember("population_count", string(T.Properties.VariableNames));
if useWeights
    w = T.population_count;
else
    w = [];
end

%% 4) Convert categoricals
if iscell(T.race) || isstring(T.race)
    T.race = categorical(T.race);
end
if iscell(T.gender) || isstring(T.gender)
    T.gender = categorical(T.gender);
end

raceCats = categories(T.race);
genCats  = categories(T.gender);

%% 5) Build design matrix table with dummies (drop reference levels)
% Dummy matrices
raceD = dummyvar(T.race);
genD  = dummyvar(T.gender);

% Drop first column of each group (reference category)
% Reference is the first category in alphabetical order
raceD = raceD(:,2:end);
genD  = genD(:,2:end);

% Build predictor table
X = table();
X.age_mid = T.age_mid;
X.education_years = T.education_years;

% Gender dummy columns
for j = 1:size(genD,2)
    X.("gender_" + string(genCats(j+1))) = genD(:,j);
end

% Race dummy columns
for i = 1:size(raceD,2)
    X.("race_" + string(raceCats(i+1))) = raceD(:,i);
end

% Add response for fitlm convenience
X.avg_income = y;

% Remove any rows with missing data
varsToCheck = X.Properties.VariableNames;
good = true(height(X),1);
for k = 1:numel(varsToCheck)
    v = X.(varsToCheck{k});
    if isnumeric(v)
        good = good & isfinite(v);
    end
end
X = X(good,:);
if useWeights, w = w(good); end

fprintf("After cleaning: %d rows remain.\n", height(X));

%% 6) Fit multivariate regression
% Build formula automatically (all predictors except avg_income)
predictorNames = setdiff(string(X.Properties.VariableNames), "avg_income");
formula = "avg_income ~ " + strjoin(predictorNames, " + ");

if useWeights
    mdl = fitlm(X, formula, "Weights", w);
else
    mdl = fitlm(X, formula);
end

disp("=== Regression Model Summary ===");
disp(mdl);

%% 7) Evaluate fit (training metrics)
yhat = predict(mdl, X(:, predictorNames));
ytrue = X.avg_income;

R2 = 1 - sum((ytrue - yhat).^2) / sum((ytrue - mean(ytrue)).^2);
MAE = mean(abs(ytrue - yhat));
RMSE = sqrt(mean((ytrue - yhat).^2));

fprintf("Training R^2:  %.4f\n", R2);
fprintf("Training MAE: %.2f\n", MAE);
fprintf("Training RMSE: %.2f\n", RMSE);

%% 8) Visual 1 — Actual vs Predicted
figure("Color","w");
scatter(ytrue, yhat, 22, "filled");
grid on;
xlabel("Actual avg_income");
ylabel("Predicted avg_income");
title("Actual vs Predicted Income (Training)");
hold on;
minv = min([ytrue; yhat]); maxv = max([ytrue; yhat]);
plot([minv maxv], [minv maxv], "-", "LineWidth", 1.2);
hold off;

%% 9) Visual 2 — Residuals vs Predicted
resid = ytrue - yhat;

figure("Color","w");
scatter(yhat, resid, 22, "filled");
grid on;
xlabel("Predicted avg_income");
ylabel("Residual (Actual - Predicted)");
title("Residuals vs Predicted");
yline(0, "--");

%% 10) Visual 3 — Coefficient plot (excluding intercept)
coefTbl = mdl.Coefficients;
coefTbl = coefTbl(~strcmp(coefTbl.Properties.RowNames, "(Intercept)"), :);

figure("Color","w");
bar(coefTbl.Estimate);
grid on;
title("Regression Coefficients (No Intercept)");
ylabel("Coefficient Value");
xticks(1:height(coefTbl));
xticklabels(string(coefTbl.Properties.RowNames));
xtickangle(45);

%% 11) Save model for reuse
meta = struct();
meta.raceCategories = raceCats;
meta.genderCategories = genCats;
meta.referenceRace = string(raceCats(1));
meta.referenceGender = string(genCats(1));
meta.predictorNames = predictorNames;

save("income_regression_model.mat", "mdl", "meta");
disp("Saved: income_regression_model.mat");

%% 12) (Optional) Example prediction for a NEW demographic profile
% You MUST set the predictors consistent with X column names.

% Example: age_mid=29.5, education_years=16, gender=Male, race=Black
% (Adjust category strings to match YOUR categories exactly.)
new = array2table(zeros(1, numel(predictorNames)), "VariableNames", cellstr(predictorNames));
new.age_mid = 29.5;
new.education_years = 16;

% Set gender dummy (if Male is not the reference)
% Example assumes categories include "Male" and "Female"
if any(predictorNames == "gender_Male")
    new.gender_Male = 1;  % otherwise leave all gender_* as 0 = reference gender
end

% Set race dummy (if Black is not the reference)
if any(predictorNames == "race_Black")
    new.race_Black = 1;
end

predIncome = predict(mdl, new);
fprintf("Example predicted income: %.2f\n", predIncome);