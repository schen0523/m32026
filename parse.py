import pandas as pd
from tax import calculate_taxes
from tax import expenditure
from itertools import product

df = pd.read_csv('census_clean.csv')

df.columns = df.columns.str.strip().str.lower()

race_col = df.columns[0]
gender_col = df.columns[1]

df['race_black'] = (df[race_col].str.strip().str.lower() == 'black').astype(int)
df['race_white'] = (df[race_col].str.strip().str.lower() == 'white').astype(int)
df['race_hispanic'] = (df[race_col].str.strip().str.lower() == 'hispanic').astype(int)

df['gender_male'] = (df[gender_col].str.strip().str.lower() == 'male').astype(int)

df = df.drop(columns=[race_col, gender_col,  'avg_income', 'population_count'])

df['gross_income'] = round((
    -113969.1915
    + 551.9021 * df['age_mid']
    + 10157.9867 * df['education_years']
    + -4739.0145 * df['race_black']
    + 100.9511 * df['race_hispanic']
    + 4638.0633 * df['race_white']
    + 26924.3719 * df['gender_male']
), 2)

marital_statuses = ['single', 'married']

states = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
    'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
    'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
    'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
    'West Virginia', 'Wisconsin', 'Wyoming'
]

combinations = list(product(marital_statuses, states))

df = df.loc[df.index.repeat(len(combinations))].reset_index(drop=True)

df['marital_status'] = [c[0] for c in combinations] * (len(df) // len(combinations))
df['state'] = [c[1] for c in combinations] * (len(df) // len(combinations))

#df['tax'] = calculate_taxes(df['gross_income'], df['marital_status'], df['state'])

df['tax'] = round(df.apply(
    lambda row: calculate_taxes(row['gross_income'], row['marital_status'], row['state']),
    axis=1
), 2)

df['expenditure'] = round(df.apply(
    lambda row: expenditure(row['age_mid']),
    axis=1
), 2)

df['disposable_income'] = round((df['gross_income'] - df['tax'] - df['expenditure']), 2)

df.to_csv('output.csv', index=False)
print("Done! Columns in output:", df.columns.tolist())

#df = pd.read_csv('output.csv')

#print((df['disposable_income'] < 0).sum())