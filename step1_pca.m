%% step1_pca_only.m
% Runs PCA on demographic features, makes PCA diagrams, saves PCA artifacts + PC scores.
% Requires census_clean.csv with:
%   age_mid, education_years, race, gender, avg_income
% Optional: population_count

clear; clc; close all;

%% 1) Load
filename = "census_clean.csv";
T = readtable(filename);

required = ["age_mid","education_years","race","gender","avg_income"];
missing = required(~ismember(required, string(T.Properties.VariableNames)));
if ~isempty(missing)
    error("Missing required column(s): %s", strjoin(cellstr(missing), ", "));
end

y = T.avg_income;

useWeights = ismember("population_count", string(T.Properties.VariableNames));
if useWeights
    pop = T.population_count;
else
    pop = [];
end

%% 2) Convert categoricals
if iscell(T.race) || isstring(T.race),   T.race = categorical(T.race); end
if iscell(T.gender) || isstring(T.gender), T.gender = categorical(T.gender); end

raceCats = categories(T.race);
genCats  = categories(T.gender);

%% 3) Dummy encode (drop reference)
raceD = dummyvar(T.race);   raceD = raceD(:,2:end);
genD  = dummyvar(T.gender); genD  = genD(:,2:end);

featNames = [
    "age_mid"
    "education_years"
    "race_" + string(raceCats(2:end))
    "gender_" + string(genCats(2:end))
];

%% 4) Build X
X = [T.age_mid, T.education_years, raceD, genD];

% Clean rows
good = all(isfinite(X),2) & isfinite(y);
X = X(good,:);
y = y(good);
if useWeights, pop = pop(good); end

fprintf("PCA: Using %d rows and %d features.\n", size(X,1), size(X,2));

%% 5) Standardize (save scaling for later)
muX = mean(X,1);
sigX = std(X,0,1);
sigX(sigX==0) = 1;
Xz = (X - muX) ./ sigX;

%% Z-score standardization (mean 0, std 1)

muX = mean(X, 1);          % 1 x p
sigX = std(X, 0, 1);       % 1 x p
sigX(sigX == 0) = 1;       % avoid divide-by-zero

Xz = (X - muX) ./ sigX;    % standardized matrix

%% 6) PCA
[coeff, score, latent, ~, explained] = pca(Xz);
cumExplained = cumsum(explained);

k90 = find(cumExplained >= 90, 1, "first");
k95 = find(cumExplained >= 95, 1, "first");
if isempty(k90), k90 = numel(explained); end
if isempty(k95), k95 = numel(explained); end

fprintf("k90=%d, k95=%d\n", k90, k95);

%% 7) PCA plots
%% Scree Plot (Green Bars Only)

figure("Color","w","Name","Scree Plot - Bars Only");

bar(explained, ...
    "FaceColor", [0.2 0.7 0.2], ...   % green
    "EdgeColor", "none");

xlabel("Principal Component");
ylabel("Percent Variance Explained");
title("Scree Plot");
grid off;
box off;

%% Scree Plot — Darker Green Based on Variance %

figure("Color","w","Name","Scree Plot - Shaded Bars");

b = bar(explained, "FaceColor", "flat", "EdgeColor", "none");

% Normalize explained variance to [0,1] for shading
normVals = explained / max(explained);

% Create dark green shades
for i = 1:length(explained)
    % Base green color scaled by variance
    b.CData(i,:) = [0.0, 0.3 + 0.6*normVals(i), 0.0];
end

xlabel("Principal Component");
ylabel("Percent Variance Explained");
title("Scree Plot");

ylim([0 100]);    % Force y-axis 0 to 100
xlim([0.5 length(explained)+0.5]);

box off;
grid off;

%% Cumulative Variance Plot (Integer X + Labeled Points)

figure("Color","w","Name","Cumulative Variance");

xVals = 1:length(cumExplained);

plot(xVals, cumExplained, ...
     "-o", ...
     "LineWidth", 1.5, ...
     "MarkerSize", 6);

grid on;

xlabel("Number of Principal Components");
ylabel("Cumulative Percent Variance Explained");
title("Cumulative Explained Variance");

% Force x-axis to integers only
xticks(xVals);

% Optional: force y-axis 0–100 for consistency
ylim([0 100]);

% Add coordinate labels to each point
for i = 1:length(cumExplained)
    text(xVals(i), cumExplained(i), ...
         sprintf("(%d, %.1f%%)", xVals(i), cumExplained(i)), ...
         "VerticalAlignment", "bottom", ...
         "HorizontalAlignment", "center", ...
         "FontSize", 9);
end

set(gca, "FontSize", 12);

% PC1 vs PC2 colored by income
figure("Color","w","Name","PC1 vs PC2");
scatter(score(:,1), score(:,2), 22, y, "filled");
colorbar; grid on;
title("PC1 vs PC2 (colored by avg\_income)");
xlabel("PC1 score");
ylabel("PC2 score");

% Loadings heatmap
Kshow = min(10, size(coeff,2));
figure("Color","w","Name","Loadings Heatmap");
imagesc(coeff(:,1:Kshow));
colorbar;
title("PCA Loadings Heatmap");
xlabel("Principal Component");
ylabel("Feature");
yticks(1:numel(featNames));
yticklabels(featNames);
xticks(1:Kshow);
xticklabels("PC"+string(1:Kshow));

%% 8) Save everything needed for step 2
PCAmeta = struct();
PCAmeta.raceCategories = raceCats;
PCAmeta.genderCategories = genCats;
PCAmeta.referenceRace = string(raceCats(1));
PCAmeta.referenceGender = string(genCats(1));
PCAmeta.featNames = featNames;
PCAmeta.k90 = k90;
PCAmeta.k95 = k95;

save("pca_artifacts.mat", ...
    "X","muX","sigX","coeff","score","explained","cumExplained", ...
    "y","pop","useWeights","PCAmeta");

disp("Saved: pca_artifacts.mat");

disp("=== PCA Loading Matrix (coefficients) ===");
disp(coeff);

%% Display loadings as a labeled table

numPCs = size(coeff,2);
pcNames = "PC" + string(1:numPCs);

loadingTable = array2table(coeff, ...
    "VariableNames", pcNames, ...
    "RowNames", featNames);

disp("=== PCA Loadings Table ===");
disp(loadingTable);