"""
US Tax Calculator (2025)
========================
Estimates total tax burden based on:
  - Income
  - Marital status
  - State of residence

Includes:
  - Federal income tax (progressive brackets)
  - FICA (Social Security + Medicare)
  - State income tax (all 50 states + DC, with brackets where applicable)

Usage:
  result = calculate_taxes(75000, "single", "California")
  print(result)

  # Or apply to a pandas DataFrame:
  df['tax_info'] = df.apply(lambda row: calculate_taxes(
      row['income'], row['marital_status'], row['state']
  ), axis=1)
"""

# ─────────────────────────────────────────────
# 2025 FEDERAL BRACKETS
# ─────────────────────────────────────────────
# Each entry: (upper_limit, marginal_rate)
# The last bracket has float('inf') as the upper limit

FEDERAL_BRACKETS = {
    "single": [
        (11600,       0.10),
        (47150,       0.12),
        (100525,      0.22),
        (191950,      0.24),
        (243725,      0.32),
        (609350,      0.35),
        (float('inf'), 0.37),
    ],
    "married": [
        (23200,       0.10),
        (94300,       0.12),
        (201050,      0.22),
        (383900,      0.24),
        (487450,      0.32),
        (731200,      0.35),
        (float('inf'), 0.37),
    ],
}

# ─────────────────────────────────────────────
# 2025 STANDARD DEDUCTIONS
# ─────────────────────────────────────────────
STANDARD_DEDUCTION = {
    "single":  14600,
    "married": 29200,
}

# ─────────────────────────────────────────────
# FICA
# ─────────────────────────────────────────────
FICA_RATE            = 0.0765   # Employee share: 6.2% SS + 1.45% Medicare
SS_WAGE_BASE         = 168600   # Social Security wage base cap (2024)
ADDITIONAL_MEDICARE  = 0.009    # Extra 0.9% on wages above threshold
ADDITIONAL_MEDICARE_THRESHOLD = {
    "single":  125000,
    "married": 250000,
}

# ─────────────────────────────────────────────
# 2025 STATE TAX BRACKETS
# ─────────────────────────────────────────────
# Format: { "State": { "single": [(limit, rate), ...], "married": [...] } }
# - States with NO income tax → empty list (0% applied)
# - Flat-rate states → single bracket with (inf, rate)
# - Graduated states → full bracket table
# - Limits are taxable income thresholds (before state standard deduction)
#
# Note: State standard deductions vary widely; for simplicity this calculator
# applies brackets to gross income minus the STATE standard deduction where
# known, otherwise to gross income directly. See STATE_STD_DEDUCTION below.

STATE_BRACKETS = {
    # ── No income tax ──────────────────────────────────────────────────────
    "Alaska":        {"single": [], "married": []},
    "Florida":       {"single": [], "married": []},
    "Nevada":        {"single": [], "married": []},
    "New Hampshire": {"single": [], "married": []},
    "South Dakota":  {"single": [], "married": []},
    "Tennessee":     {"single": [], "married": []},
    "Texas":         {"single": [], "married": []},
    "Wyoming":       {"single": [], "married": []},

    # ── Flat-rate states ───────────────────────────────────────────────────
    "Arizona":       {"single": [(float('inf'), 0.025)],  "married": [(float('inf'), 0.025)]},
    "Colorado":      {"single": [(float('inf'), 0.044)],  "married": [(float('inf'), 0.044)]},
    "Georgia":       {"single": [(float('inf'), 0.0539)], "married": [(float('inf'), 0.0539)]},
    "Idaho":         {"single": [(float('inf'), 0.05695)],"married": [(float('inf'), 0.05695)]},
    "Illinois":      {"single": [(float('inf'), 0.0495)], "married": [(float('inf'), 0.0495)]},
    "Indiana":       {"single": [(float('inf'), 0.03)],   "married": [(float('inf'), 0.03)]},
    "Iowa":          {"single": [(float('inf'), 0.038)],  "married": [(float('inf'), 0.038)]},
    "Kentucky":      {"single": [(float('inf'), 0.04)],   "married": [(float('inf'), 0.04)]},
    "Louisiana":     {"single": [(float('inf'), 0.03)],   "married": [(float('inf'), 0.03)]},
    "Michigan":      {"single": [(float('inf'), 0.0425)], "married": [(float('inf'), 0.0425)]},
    "Mississippi":   {"single": [(10000, 0.0), (float('inf'), 0.044)], "married": [(10000, 0.0), (float('inf'), 0.044)]},
    "North Carolina":{"single": [(float('inf'), 0.0425)], "married": [(float('inf'), 0.0425)]},
    "Pennsylvania":  {"single": [(float('inf'), 0.0307)], "married": [(float('inf'), 0.0307)]},
    "Utah":          {"single": [(float('inf'), 0.0455)], "married": [(float('inf'), 0.0455)]},

    # ── Graduated-rate states ──────────────────────────────────────────────
    "Alabama": {
        "single":  [(500, 0.02), (3000, 0.04), (float('inf'), 0.05)],
        "married": [(1000, 0.02), (6000, 0.04), (float('inf'), 0.05)],
    },
    "Arkansas": {
        "single":  [(4500, 0.02), (float('inf'), 0.039)],
        "married": [(4500, 0.02), (float('inf'), 0.039)],
    },
    "California": {
        "single": [
            (10756, 0.01), (25499, 0.02), (40245, 0.04), (55866, 0.06),
            (70606, 0.08), (360659, 0.093), (432787, 0.103),
            (721314, 0.113), (1000000, 0.123), (float('inf'), 0.133),
        ],
        "married": [
            (21512, 0.01), (50998, 0.02), (80490, 0.04), (111732, 0.06),
            (141732, 0.08), (721318, 0.093), (865574, 0.103),
            (1000000, 0.113), (1442628, 0.123), (float('inf'), 0.133),
        ],
    },
    "Connecticut": {
        "single": [
            (10000, 0.02), (50000, 0.045), (100000, 0.055),
            (200000, 0.06), (250000, 0.065), (500000, 0.069),
            (float('inf'), 0.0699),
        ],
        "married": [
            (20000, 0.02), (100000, 0.045), (200000, 0.055),
            (400000, 0.06), (500000, 0.065), (1000000, 0.069),
            (float('inf'), 0.0699),
        ],
    },
    "Delaware": {
        "single": [
            (2000, 0.0), (5000, 0.022), (10000, 0.039),
            (20000, 0.048), (25000, 0.052), (60000, 0.0555),
            (float('inf'), 0.066),
        ],
        "married": [
            (2000, 0.0), (5000, 0.022), (10000, 0.039),
            (20000, 0.048), (25000, 0.052), (60000, 0.0555),
            (float('inf'), 0.066),
        ],
    },
    "Hawaii": {
        "single": [
            (9600, 0.014), (14400, 0.032), (19200, 0.055),
            (24000, 0.064), (36000, 0.068), (48000, 0.072),
            (125000, 0.076), (175000, 0.079), (225000, 0.0825),
            (275000, 0.09), (325000, 0.10), (float('inf'), 0.11),
        ],
        "married": [
            (19200, 0.014), (28800, 0.032), (38400, 0.055),
            (48000, 0.064), (72000, 0.068), (96000, 0.072),
            (250000, 0.076), (350000, 0.079), (450000, 0.0825),
            (550000, 0.09), (650000, 0.10), (float('inf'), 0.11),
        ],
    },
    "Kansas": {
        "single":  [(23000, 0.052), (float('inf'), 0.0558)],
        "married": [(46000, 0.052), (float('inf'), 0.0558)],
    },
    "Maine": {
        "single":  [(26800, 0.058), (63450, 0.0675), (float('inf'), 0.0715)],
        "married": [(53600, 0.058), (126900, 0.0675), (float('inf'), 0.0715)],
    },
    "Maryland": {
        "single": [
            (1000, 0.02), (2000, 0.03), (3000, 0.04), (100000, 0.0475),
            (125000, 0.05), (150000, 0.0525), (250000, 0.055),
            (float('inf'), 0.0575),
        ],
        "married": [
            (1000, 0.02), (2000, 0.03), (3000, 0.04), (150000, 0.0475),
            (175000, 0.05), (225000, 0.0525), (300000, 0.055),
            (float('inf'), 0.0575),
        ],
    },
    "Massachusetts": {
        "single":  [(1083150, 0.05), (float('inf'), 0.09)],
        "married": [(1083150, 0.05), (float('inf'), 0.09)],
    },
    "Minnesota": {
        "single": [
            (32570, 0.0535), (106990, 0.068),
            (198630, 0.0785), (float('inf'), 0.0985),
        ],
        "married": [
            (47620, 0.0535), (189180, 0.068),
            (330410, 0.0785), (float('inf'), 0.0985),
        ],
    },
    "Missouri": {
        "single": [
            (1313, 0.0), (2626, 0.02), (3939, 0.025), (5252, 0.03),
            (6565, 0.035), (7878, 0.04), (9191, 0.045), (float('inf'), 0.047),
        ],
        "married": [
            (1313, 0.0), (2626, 0.02), (3939, 0.025), (5252, 0.03),
            (6565, 0.035), (7878, 0.04), (9191, 0.045), (float('inf'), 0.047),
        ],
    },
    "Montana": {
        "single":  [(21100, 0.047), (float('inf'), 0.059)],
        "married": [(42200, 0.047), (float('inf'), 0.059)],
    },
    "Nebraska": {
        "single": [
            (4030, 0.0246), (24120, 0.0351),
            (38870, 0.0501), (float('inf'), 0.052),
        ],
        "married": [
            (8040, 0.0246), (48250, 0.0351),
            (77730, 0.0501), (float('inf'), 0.052),
        ],
    },
    "New Jersey": {
        "single": [
            (20000, 0.014), (35000, 0.0175), (40000, 0.035),
            (75000, 0.05525), (500000, 0.0637), (1000000, 0.0897),
            (float('inf'), 0.1075),
        ],
        "married": [
            (20000, 0.014), (50000, 0.0175), (70000, 0.035),
            (80000, 0.05525), (150000, 0.0637), (500000, 0.0897),
            (1000000, 0.0897), (float('inf'), 0.1075),
        ],
    },
    "New Mexico": {
        "single": [
            (5500, 0.015), (16500, 0.032), (33500, 0.043),
            (66500, 0.047), (210000, 0.049), (float('inf'), 0.059),
        ],
        "married": [
            (8000, 0.015), (25000, 0.032), (50000, 0.043),
            (100000, 0.047), (315000, 0.049), (float('inf'), 0.059),
        ],
    },
    "New York": {
        "single": [
            (8500, 0.04), (11700, 0.045), (13900, 0.0525),
            (80650, 0.055), (215400, 0.06), (1077550, 0.0685),
            (5000000, 0.0965), (25000000, 0.103), (float('inf'), 0.109),
        ],
        "married": [
            (17150, 0.04), (23600, 0.045), (27900, 0.0525),
            (161550, 0.055), (323200, 0.06), (2155350, 0.0685),
            (5000000, 0.0965), (25000000, 0.103), (float('inf'), 0.109),
        ],
    },
    "North Dakota": {
        "single":  [(48475, 0.0), (244825, 0.0195), (float('inf'), 0.025)],
        "married": [(80975, 0.0), (298075, 0.0195), (float('inf'), 0.025)],
    },
    "Ohio": {
        "single":  [(26050, 0.0), (100000, 0.02750), (float('inf'), 0.035)],
        "married": [(26050, 0.0), (100000, 0.02750), (float('inf'), 0.035)],
    },
    "Oklahoma": {
        "single": [
            (1000, 0.0025), (2500, 0.0075), (3750, 0.0175),
            (4900, 0.0275), (7200, 0.0375), (float('inf'), 0.0475),
        ],
        "married": [
            (2000, 0.0025), (5000, 0.0075), (7500, 0.0175),
            (9800, 0.0275), (14400, 0.0375), (float('inf'), 0.0475),
        ],
    },
    "Oregon": {
        "single": [
            (4400, 0.0475), (11050, 0.0675),
            (125000, 0.0875), (float('inf'), 0.099),
        ],
        "married": [
            (8800, 0.0475), (22100, 0.0675),
            (250000, 0.0875), (float('inf'), 0.099),
        ],
    },
    "Rhode Island": {
        "single":  [(79900, 0.0375), (181650, 0.0475), (float('inf'), 0.0599)],
        "married": [(79900, 0.0375), (181650, 0.0475), (float('inf'), 0.0599)],
    },
    "South Carolina": {
        "single":  [(3560, 0.0), (17830, 0.03), (float('inf'), 0.062)],
        "married": [(3560, 0.0), (17830, 0.03), (float('inf'), 0.062)],
    },
    "Vermont": {
        "single": [
            (47900, 0.0335), (116000, 0.066),
            (242000, 0.076), (float('inf'), 0.0875),
        ],
        "married": [
            (79950, 0.0335), (193300, 0.066),
            (294600, 0.076), (float('inf'), 0.0875),
        ],
    },
    "Virginia": {
        "single": [
            (3000, 0.02), (5000, 0.03), (17000, 0.05),
            (float('inf'), 0.0575),
        ],
        "married": [
            (3000, 0.02), (5000, 0.03), (17000, 0.05),
            (float('inf'), 0.0575),
        ],
    },
    "Washington": {"single": [], "married": []},  # Only capital gains (ignored here)
    "West Virginia": {
        "single": [
            (10000, 0.0222), (25000, 0.0296), (40000, 0.0333),
            (60000, 0.0444), (float('inf'), 0.0482),
        ],
        "married": [
            (10000, 0.0222), (25000, 0.0296), (40000, 0.0333),
            (60000, 0.0444), (float('inf'), 0.0482),
        ],
    },
    "Wisconsin": {
        "single": [
            (14680, 0.035), (29370, 0.044),
            (323290, 0.053), (float('inf'), 0.0765),
        ],
        "married": [
            (19580, 0.035), (39150, 0.044),
            (431060, 0.053), (float('inf'), 0.0765),
        ],
    },
    "Washington DC": {
        "single": [
            (10000, 0.04), (40000, 0.06), (60000, 0.065),
            (250000, 0.085), (500000, 0.0925), (1000000, 0.0975),
            (float('inf'), 0.1075),
        ],
        "married": [
            (10000, 0.04), (40000, 0.06), (60000, 0.065),
            (250000, 0.085), (500000, 0.0925), (1000000, 0.0975),
            (float('inf'), 0.1075),
        ],
    },
}

# ─────────────────────────────────────────────
# STATE STANDARD DEDUCTIONS (2025)
# ─────────────────────────────────────────────
# Applied before state bracket calculation where known.
# 0 = no state standard deduction (brackets applied to gross income).

STATE_STD_DEDUCTION = {
    "Alabama":        {"single": 3000,  "married": 8500},
    "Alaska":         {"single": 0,     "married": 0},
    "Arizona":        {"single": 15000, "married": 30000},
    "Arkansas":       {"single": 2410,  "married": 4820},
    "California":     {"single": 5540,  "married": 11080},
    "Colorado":       {"single": 15000, "married": 30000},
    "Connecticut":    {"single": 0,     "married": 0},
    "Delaware":       {"single": 3250,  "married": 6500},
    "Florida":        {"single": 0,     "married": 0},
    "Georgia":        {"single": 12000, "married": 24000},
    "Hawaii":         {"single": 4400,  "married": 8800},
    "Idaho":          {"single": 15000, "married": 30000},
    "Illinois":       {"single": 0,     "married": 0},
    "Indiana":        {"single": 0,     "married": 0},
    "Iowa":           {"single": 0,     "married": 0},
    "Kansas":         {"single": 3605,  "married": 8240},
    "Kentucky":       {"single": 3270,  "married": 6540},
    "Louisiana":      {"single": 12500, "married": 25000},
    "Maine":          {"single": 15000, "married": 30000},
    "Maryland":       {"single": 2700,  "married": 5450},
    "Massachusetts":  {"single": 0,     "married": 0},
    "Michigan":       {"single": 0,     "married": 0},
    "Minnesota":      {"single": 14950, "married": 29900},
    "Mississippi":    {"single": 2300,  "married": 4600},
    "Missouri":       {"single": 15000, "married": 30000},
    "Montana":        {"single": 15000, "married": 30000},
    "Nebraska":       {"single": 8600,  "married": 17200},
    "Nevada":         {"single": 0,     "married": 0},
    "New Hampshire":  {"single": 0,     "married": 0},
    "New Jersey":     {"single": 0,     "married": 0},
    "New Mexico":     {"single": 15000, "married": 30000},
    "New York":       {"single": 8000,  "married": 16050},
    "North Carolina": {"single": 12750, "married": 25500},
    "North Dakota":   {"single": 15000, "married": 30000},
    "Ohio":           {"single": 0,     "married": 0},
    "Oklahoma":       {"single": 6350,  "married": 12700},
    "Oregon":         {"single": 2800,  "married": 5600},
    "Pennsylvania":   {"single": 0,     "married": 0},
    "Rhode Island":   {"single": 10900, "married": 21800},
    "South Carolina": {"single": 15000, "married": 30000},
    "South Dakota":   {"single": 0,     "married": 0},
    "Tennessee":      {"single": 0,     "married": 0},
    "Texas":          {"single": 0,     "married": 0},
    "Utah":           {"single": 0,     "married": 0},
    "Vermont":        {"single": 7400,  "married": 14850},
    "Virginia":       {"single": 8500,  "married": 17000},
    "Washington":     {"single": 0,     "married": 0},
    "Washington DC":  {"single": 15000, "married": 30000},
    "West Virginia":  {"single": 0,     "married": 0},
    "Wisconsin":      {"single": 13560, "married": 25110},
    "Wyoming":        {"single": 0,     "married": 0},
}

# ─────────────────────────────────────────────
# HELPER: Apply progressive brackets
# ─────────────────────────────────────────────

def apply_brackets(taxable_income, brackets):
    """Calculate tax using progressive bracket table."""
    if not brackets or taxable_income <= 0:
        return 0.0
    tax = 0.0
    prev_limit = 0
    for limit, rate in brackets:
        if taxable_income <= prev_limit:
            break
        taxable_at_rate = min(taxable_income, limit) - prev_limit
        tax += taxable_at_rate * rate
        prev_limit = limit
    return tax

# ─────────────────────────────────────────────
# MAIN CALCULATOR
# ─────────────────────────────────────────────

def calculate_taxes(gross_income, marital_status, state):
    """
    Calculate estimated US tax burden for a W-2 employee.

    Parameters
    ----------
    gross_income   : float  — Annual gross wages
    marital_status : str    — "single" or "married"
    state          : str    — Full state name, e.g. "California" or "Washington DC"

    Returns
    -------
    dict with keys:
        gross_income, federal_tax, fica, state_tax, total_tax,
        effective_rate_pct, take_home
    """
    status = marital_status.lower().strip()
    if status not in ("single", "married"):
        raise ValueError("marital_status must be 'single' or 'married'")
    if gross_income < 0:
        raise ValueError("gross_income must be non-negative")

    # ── Federal income tax ─────────────────────────────────────────────────
    fed_std_ded     = STANDARD_DEDUCTION[status]
    fed_taxable     = max(0, gross_income - fed_std_ded)
    federal_tax     = apply_brackets(fed_taxable, FEDERAL_BRACKETS[status])

    # ── FICA ───────────────────────────────────────────────────────────────
    ss_wages        = min(gross_income, SS_WAGE_BASE)
    fica            = ss_wages * 0.062 + gross_income * 0.0145   # SS + Medicare

    # Additional Medicare surtax (0.9%) on high earners
    add_med_thresh  = ADDITIONAL_MEDICARE_THRESHOLD[status]
    if gross_income > add_med_thresh:
        fica += (gross_income - add_med_thresh) * ADDITIONAL_MEDICARE

    # ── State income tax ───────────────────────────────────────────────────
    state_brackets  = STATE_BRACKETS.get(state, {}).get(status, [])
    state_std_ded   = STATE_STD_DEDUCTION.get(state, {}).get(status, 0)
    state_taxable   = max(0, gross_income - state_std_ded)
    state_tax       = apply_brackets(state_taxable, state_brackets)

    # ── Totals ─────────────────────────────────────────────────────────────
    total_tax       = federal_tax + fica + state_tax
    effective_rate  = (total_tax / gross_income * 100) if gross_income > 0 else 0
    take_home       = gross_income - total_tax

    return {
        "gross_income":       round(gross_income, 2),
        #"federal_tax":        round(federal_tax, 2),
        #"fica":               round(fica, 2),
        #"state_tax":          round(state_tax, 2),
        "total_tax":          round(total_tax, 2),
        #"effective_rate_pct": round(effective_rate, 2),
        "take_home":          round(take_home, 2),
    }

    #return total_tax

# ─────────────────────────────────────────────
# APPLY TO A DATAFRAME
# ─────────────────────────────────────────────

def apply_to_dataframe(df,
                        income_col="income",
                        marital_col="marital_status",
                        state_col="state"):
    """
    Add tax columns to a pandas DataFrame.

    Expected columns: income, marital_status (single/married), state (full name)
    Returns the original df with additional columns appended.
    """
    import pandas as pd

    results = df.apply(
        lambda row: calculate_taxes(
            row[income_col],
            row[marital_col],
            row[state_col]
        ),
        axis=1
    )

    tax_df = pd.DataFrame(results.tolist())
    # Drop duplicate gross_income column if already in df
    tax_df = tax_df.drop(columns=["gross_income"], errors="ignore")
    return pd.concat([df.reset_index(drop=True), tax_df], axis=1)


# ─────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import pandas as pd

    # ── Single person examples ─────────────────────────────────────────────
    examples = [
        (40000,  "single",  "Texas"),
        (75000,  "single",  "California"),
        (75000,  "married", "California"),
        (120000, "single",  "New York"),
        (200000, "married", "Florida"),
        (50000,  "single",  "Oregon"),
    ]

    print("=" * 70)
    print(f"{'Income':>10} {'Status':>8} {'State':<15} {'Total Tax':>9} {'Take-Home':>11}")
    print("-" * 70)
    for income, status, state in examples:
        r = calculate_taxes(income, status, state)
        print(f"${r['gross_income']:>9,.0f} {status:>8} {state:<15} "
              f"${r['total_tax']:>8,.0f} ${r['take_home']:>10,.0f}")
    print("=" * 70)

    # ── DataFrame example ──────────────────────────────────────────────────
    # print("\nDataFrame example:")
    # sample_data = {
    #     "name":           ["Alice", "Bob", "Carol"],
    #     "income":         [60000, 95000, 150000],
    #     "marital_status": ["single", "married", "single"],
    #     "state":          ["Texas", "New York", "California"],
    #     "age":            [28, 45, 35],
    # }
    # df = pd.DataFrame(sample_data)
    # df_result = apply_to_dataframe(df)
    # print(df_result[["name", "income", "state", "total_tax",
    #                   "effective_rate_pct", "take_home"]].to_string(index=False))