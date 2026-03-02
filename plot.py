import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('output.csv')

# Drop duplicates since each person is repeated across state/marital combos
df_people = df.drop_duplicates(subset=['education_years', 'age_mid', 'race_black', 'race_white', 'race_hispanic', 'gender_male'])

# Determine race label
def get_race(row):
    if row['race_white'] == 1:
        return 'White'
    elif row['race_black'] == 1:
        return 'Black'
    elif row['race_hispanic'] == 1:
        return 'Hispanic'
    else:
        return 'Asian'

df_people['race'] = df_people.apply(get_race, axis=1)

race_colors = {
    'White':    'steelblue',
    'Black':    'tomato',
    'Hispanic': 'mediumseagreen',
    'Asian':    'mediumpurple'
}

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

for race, group in df_people.groupby('race'):
    males   = group[group['gender_male'] == 1]
    females = group[group['gender_male'] == 0]

    # Males — filled markers
    ax.scatter(
        males['education_years'],
        males['age_mid'],
        males['gross_income'],
        c=race_colors[race],
        marker='o',
        s=40,
        label=f'{race} (M)',
        alpha=0.8,
        edgecolors=race_colors[race]
    )

    # Females — open markers
    ax.scatter(
        females['education_years'],
        females['age_mid'],
        females['gross_income'],
        c='none',
        marker='o',
        s=40,
        label=f'{race} (F)',
        alpha=0.8,
        edgecolors=race_colors[race]
    )

ax.set_xlabel('Education (Years)')
ax.set_ylabel('Age')
ax.set_zlabel('Gross Income ($)')
ax.set_title('Gross Income by Education, Age, Race, and Gender')

ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=8)

plt.tight_layout()
plt.savefig('income_3d.png', dpi=150, bbox_inches='tight')
plt.show()