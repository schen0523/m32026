import pandas as pd
import math

# ═══════════════════════════════════════════════════════════════════
#  SET YOUR VARIABLES HERE
# ═══════════════════════════════════════════════════════════════════

# ── Demographics ───────────────────────────────────────────────────
education_years = 16       # Options: 8, 11, 12, 13, 14, 16, 17, 18, 22
age_mid         = 30       # Options: 21, 30, 40, 50, 60, 73
race_black      = 0        # 0 or 1
race_white      = 1        # 0 or 1
race_hispanic   = 0        # 0 or 1
gender_male     = 1        # 0 = female, 1 = male
marital_status  = "single" # "single" or "married"
state           = "California"

# ── OCEAN Personality Scores (scale: 0–100, mean=50, std=10) ──────
neuroticism       = 50
conscientiousness = 50
agreeableness     = 50
openness          = 50
extroversion      = 50

# ═══════════════════════════════════════════════════════════════════
#  STEP 1: LOOK UP INCOME FROM CSV
# ═══════════════════════════════════════════════════════════════════

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
    print("❌ No match found for that combination of variables.")
    exit()

row           = match.iloc[0]
disposable_income  = row["disposable_income"]

# ═══════════════════════════════════════════════════════════════════
#  STEP 2: DEMOGRAPHIC MODEL  (zD)
# ═══════════════════════════════════════════════════════════════════

# ── Intercept (baseline = female) ─────────────────────────────────
alpha = math.log(0.215 / 0.785)   # = -1.296

# ── Gender ────────────────────────────────────────────────────────
beta_male = math.log(0.42 / 0.58) - math.log(0.215 / 0.785)  # 0.973

# ── Age (baseline: 30–49) ─────────────────────────────────────────
age_betas = {
    21:  0.770,   # 18–22 bracket (closest to age_mid=21)
    30:  0.000,   # baseline 30–49
    40:  0.000,   # baseline 30–49
    50:  0.124,   # 50–64
    60:  0.124,   # 50–64
    73:  0.407,   # 65+
}
beta_age = age_betas.get(age_mid, 0.0)

# ── Race (baseline: White) ────────────────────────────────────────
beta_race = 0.0
if race_black:
    beta_race = 0.603
elif race_hispanic:
    beta_race = 0.454
elif not race_white:
    beta_race = 0.184   # treat as Asian/Other

# ── Income bracket (baseline: $25k–$75k) ─────────────────────────
income_bracket_betas = [
    (0,      15000,  -0.449),
    (15000,  25000,  -1.405),
    (25000,  75000,   0.000),   # baseline
    (75000,  150000, -1.489),
    (150000, float('inf'), 0.160),
]
beta_income = 0.0
for low, high, beta in income_bracket_betas:
    if low <= disposable_income < high:
        beta_income = beta
        break

# ── Combine demographic z-score ───────────────────────────────────
zD = alpha + beta_male * gender_male + beta_age + beta_race + beta_income

# ═══════════════════════════════════════════════════════════════════
#  STEP 3: PERSONALITY MODEL  (zP)
# ═══════════════════════════════════════════════════════════════════

# Standardize each score: z = (score - 50) / 10
zn = (neuroticism       - 50) / 10
zc = (conscientiousness - 50) / 10
za = (agreeableness     - 50) / 10
zo = (openness          - 50) / 10
ze = (extroversion      - 50) / 10

# Weighted sum using meta-analysis correlations
zP = (0.273 * zn) + (-0.296 * zc) + (-0.163 * za) + (-0.219 * zo) + (-0.083 * ze)

# ═══════════════════════════════════════════════════════════════════
#  STEP 4: COMBINED MODEL
# ═══════════════════════════════════════════════════════════════════

z = zD + zP
risk = 1 / (1 + math.exp(-z))

# Individual probabilities for reference
# P_demographic  = 1 / (1 + math.exp(-zD))
# P_personality  = 1 / (1 + math.exp(-zP))

print(f'risk: {risk} \n disposableincome: {disposable_income}')

house_edge = -0.08
mean = (disposable_income)*(risk)*(house_edge)

print(f'mean: {mean} SD: {risk}')


# ═══════════════════════════════════════════════════════════════════
#  RESULTS
# # ═══════════════════════════════════════════════════════════════════

# print("=" * 52)
# print("  GAMBLING PROBABILITY CALCULATOR")
# print("=" * 52)

# print("\n── Income Lookup ──────────────────────────────")
# print(f"   Gross Income:       ${gross_income:>12,.2f}")
# print(f"   Tax:                ${row['tax']:>12,.2f}")
# print(f"   Disposable Income:  ${row['disposable_income']:>12,.2f}")

# print("\n── Demographic Model ──────────────────────────")
# print(f"   Intercept (α):      {alpha:>8.3f}")
# print(f"   Gender coefficient: {beta_male * gender_male:>8.3f}")
# print(f"   Age coefficient:    {beta_age:>8.3f}")
# print(f"   Race coefficient:   {beta_race:>8.3f}")
# print(f"   Income coefficient: {beta_income:>8.3f}")
# print(f"   zD:                 {zD:>8.3f}")
# print(f"   P(demographic):     {P_demographic:>8.1%}")

# print("\n── Personality Model ──────────────────────────")
# print(f"   Neuroticism       (score={neuroticism}): z={zn:+.2f}  weighted={0.273*zn:+.3f}")
# print(f"   Conscientiousness (score={conscientiousness}): z={zc:+.2f}  weighted={-0.296*zc:+.3f}")
# print(f"   Agreeableness     (score={agreeableness}): z={za:+.2f}  weighted={-0.163*za:+.3f}")
# print(f"   Openness          (score={openness}): z={zo:+.2f}  weighted={-0.219*zo:+.3f}")
# print(f"   Extroversion      (score={extroversion}): z={ze:+.2f}  weighted={-0.083*ze:+.3f}")
# print(f"   zP:                 {zP:>8.3f}")
# print(f"   P(personality):     {P_personality:>8.1%}")

# print("\n── Combined Result ────────────────────────────")
# print(f"   z  = zD + zP = {zD:.3f} + {zP:.3f} = {z:.3f}")
# print(f"   P  = 1 / (1 + e^-z)")
# print(f"\n   ✅ Overall P(gambling) = {P:.1%}")
# print("=" * 52)