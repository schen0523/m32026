import pandas as pd
import math

#variables
education_years = 18 #8, 11, 12, 13, 14, 16, 17, 18, 22
age_mid = 73 #21, 30, 40, 50, 60, 73
race_black = 0        
race_white = 1      
race_hispanic = 0     
gender_male = 1 #0 = female, 1 = male
marital_status = "married"
state = "California"

neuroticism       = 50
conscientiousness = 50
agreeableness     = 50
openness          = 50
extroversion      = 50

df = pd.read_csv("output.csv")

match = df[
    (df["education_years"] == education_years) &
    (df["age_mid"]         == age_mid)         &
    (df["race_black"]      == race_black)       &
    (df["race_white"]      == race_white)       &
    (df["race_hispanic"]   == race_hispanic)    &
    (df["gender_male"]     == gender_male)      &
    (df["marital_status"]  == marital_status)   &
    (df["state"]           == state)
]

if match.empty:
    print("No match.")
    exit()

row = match.iloc[0]
disposable_income = row["disposable_income"]

#demographic model

alpha = math.log(0.215 / 0.785)

beta_male = math.log(0.42 / 0.58) - math.log(0.215 / 0.785) 

age_betas = {
    21:  0.770, 
    30:  0.000, 
    40:  0.000,  
    50:  0.124, 
    60:  0.124, 
    73:  0.407, 
}
beta_age = age_betas.get(age_mid, 0.0)

beta_race = 0.0
if race_black:
    beta_race = 0.603
elif race_hispanic:
    beta_race = 0.454
elif not race_white:
    beta_race = 0.184  

income_bracket_betas = [
    (0,      15000,  -0.449),
    (15000,  25000,  -1.405),
    (25000,  75000,   0.000), 
    (75000,  150000, -1.489),
    (150000, float('inf'), 0.160),
]
beta_income = 0.0
for low, high, beta in income_bracket_betas:
    if low <= disposable_income < high:
        beta_income = beta
        break

zD = alpha + beta_male * gender_male + beta_age + beta_race + beta_income

#personality model
zn = (neuroticism - 50) / 10
zc = (conscientiousness - 50) / 10
za = (agreeableness - 50) / 10
zo = (openness - 50) / 10
ze = (extroversion - 50) / 10

zP = (0.273 * zn) + (-0.296 * zc) + (-0.163 * za) + (-0.219 * zo) + (-0.083 * ze)


z = zD + zP
risk = 1 / (1 + math.exp(-z))

print(f'risk: {risk} \n disposableincome: {disposable_income}')

house_edge = -0.15
mean = (disposable_income)*(risk)*(house_edge)

print(f'mean: {mean} )SD: {math.sqrt(abs(mean) * (1-risk))} risk: {risk}')
