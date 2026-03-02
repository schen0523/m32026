%% step2_pc_regression.m
% Fits income regression using PC scores and shows regression diagrams.
% Loads outputs from step1_pca_only.m

clear; clc; close all;

load("pca_artifacts.mat");  % loads: score, y, pop, useWeights, PCAmeta, explained, etc.

fprintf("Loaded PCA artifacts. Rows=%d, PCs=%d\n", size(score,1), size(score,2));

%% 1) Choose number of PCs for regression
% Option A: fixed 5 PCs (what you asked earlier)
kModel = 6;

% Option B: use k90 from PCA (uncomment if you prefer)
% kModel = PCAmeta.k90;

kModel = min(kModel, size(score,2));
Z = score(:, 1:kModel);

%% 2) Fit regression: Income ~ PCs
if useWeights
    mdlPC = fitlm(Z, y, "Weights", pop);
else
    mdlPC = fitlm(Z, y);
end

disp("=== Income ~ PC Regression Model ===");
disp(mdlPC);

%% 3) Predictions + metrics
yhat = predict(mdlPC, Z);
R2  = 1 - sum((y - yhat).^2) / sum((y - mean(y)).^2);
MAE = mean(abs(y - yhat));
RMSE = sqrt(mean((y - yhat).^2));

fprintf("kModel=%d\n", kModel);
fprintf("Training R^2:  %.4f\n", R2);
fprintf("Training MAE: %.2f\n", MAE);
fprintf("Training RMSE: %.2f\n", RMSE);

%% 4) Graph 1 — Actual vs Predicted
figure("Color","w","Name","PC Regression: Actual vs Predicted");
scatter(y, yhat, 22, "filled");
grid on;
xlabel("Actual avg\_income");
ylabel("Predicted avg\_income");
title("PC Regression: Actual vs Predicted");
hold on;
minv = min([y; yhat]); maxv = max([y; yhat]);
plot([minv maxv],[minv maxv],"-","LineWidth",1.2);
hold off;

%% 5) Graph 2 — Residuals vs Predicted
resid = y - yhat;

figure("Color","w","Name","PC Regression: Residuals");
scatter(yhat, resid, 22, "filled");
grid on;
xlabel("Predicted avg\_income");
ylabel("Residual (Actual - Predicted)");
title("PC Regression: Residuals vs Predicted");
yline(0,"--");

%% 6) Graph 3 — PC weights (regression coefficients)
% Coefficient table includes intercept + PC terms.
coefTbl = mdlPC.Coefficients;

% Extract PC coefficients (exclude intercept)
pcRows = startsWith(string(coefTbl.Properties.RowNames), "x");
pcCoefs = coefTbl.Estimate(pcRows);
pcSE    = coefTbl.SE(pcRows);

figure("Color","w","Name","PC Regression: PC Weights");
bar(pcCoefs);
grid on;
title("PC Regression Weights (Coefficients on PCs)");
ylabel("Coefficient");
xticks(1:kModel);
xticklabels("PC"+string(1:kModel));

%% 7) (Optional) Add error bars to PC weights
figure("Color","w","Name","PC Regression: PC Weights w/ SE");
b = bar(pcCoefs); %#ok<NASGU>
grid on;
hold on;
er = errorbar(1:kModel, pcCoefs, pcSE, pcSE, ".");
er.LineWidth = 1.2;
hold off;
title("PC Regression Weights with Standard Errors");
ylabel("Coefficient");
xticks(1:kModel);
xticklabels("PC"+string(1:kModel));

%% 8) Save model
save("pc_income_model.mat", "mdlPC", "kModel", "R2", "MAE", "RMSE");
disp("Saved: pc_income_model.mat");

%% Convert PC regression back to original variable coefficients

% Get PC regression coefficients
coefTbl = mdlPC.Coefficients;

% Intercept
beta0 = coefTbl.Estimate(1);

% PC coefficients (exclude intercept)
betaPC = coefTbl.Estimate(2:end);

% Only using first kModel PCs
betaPC = betaPC(1:kModel);

% PCA loadings for those PCs
loadings = coeff(:,1:kModel);

% Compute gamma = coeff * betaPC
gamma = loadings * betaPC;

% Convert back to original-variable scale
alpha = gamma ./ sigX';   % divide by std dev

% Adjust intercept
alpha0 = beta0 - sum(gamma .* (muX' ./ sigX'));

%% Print final linear function
disp("=== Income as function of ORIGINAL variables ===")
fprintf("Income = %.4f", alpha0);

for i = 1:length(alpha)
    fprintf(" + (%.4f)*%s", alpha(i), PCAmeta.featNames(i));
end
fprintf("\n");