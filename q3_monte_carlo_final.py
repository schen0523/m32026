import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.interpolate import interp1d

# ============================================================
# Q3 Monte Carlo Simulation — Age-Varying Parameters
# Simulates gambling outcomes from age 21 to 65 (44 years)
# Each age bracket has its own mu and sigma from Q2
# ============================================================

# --- Q2 INPUT VALUES BY AGE BRACKET ---
# (bracket_midpoint_age, annual_mu, annual_sigma, risk_score)
bracket_data = [
    (21,  -3407.545693927385,  36.45561989211967,  0.609979633116247),
    (30,  -1931.6121299999998, 33.47140623577085,  0.42),
    (40,  -2448.6877799999997, 37.68605726790745,  0.42),
    (50,  -2758.707303093945,  38.93576059869752,  0.45046962695213455),
    (60,  -3304.599460653723,  42.61429072959933,  0.45046962695213455),
    (73,  -5853.690224062478,  52.94958744622252,  0.5210442125549619),
]

P_GAMBLES     = 1.0
N_SIMULATIONS = 10_000
START_AGE     = 21
END_AGE       = 65
N_YEARS       = END_AGE - START_AGE
ages_sim      = np.arange(START_AGE, END_AGE)

# --- Interpolate mu and sigma across ages 21-64 ---
bracket_ages   = np.array([d[0] for d in bracket_data])
bracket_mus    = np.array([d[1] for d in bracket_data])
bracket_sigmas = np.array([d[2] for d in bracket_data])

mu_func    = interp1d(bracket_ages, bracket_mus,    kind='linear', fill_value='extrapolate')
sigma_func = interp1d(bracket_ages, bracket_sigmas, kind='linear', fill_value='extrapolate')

mu_by_age    = mu_func(ages_sim)
sigma_by_age = sigma_func(ages_sim)

# ============================================================
# Shifted Lognormal sampling
# Y = X - shift  where X ~ LogNormal
# E[Y] = mu (negative), SD[Y] = sigma, right skewed
# shift = 2 * |mu|
# ============================================================
def shifted_lognormal_sample(mu, sigma):
    abs_mean = abs(mu)
    ln_sigma = np.sqrt(np.log(1 + (sigma / abs_mean) ** 2))
    ln_mu    = np.log(abs_mean) - 0.5 * ln_sigma ** 2
    shift    = 2 * abs_mean
    x = np.random.lognormal(mean=ln_mu, sigma=ln_sigma)
    return x - shift

# ============================================================
# Run Simulation
# ============================================================
np.random.seed(42)

lifetime_losses = np.zeros(N_SIMULATIONS)
annual_outcomes = np.zeros((N_SIMULATIONS, N_YEARS))

for sim in range(N_SIMULATIONS):
    for year in range(N_YEARS):
        if np.random.random() > P_GAMBLES:
            annual_outcomes[sim, year] = 0
            continue
        annual_outcomes[sim, year] = shifted_lognormal_sample(
            mu_by_age[year], sigma_by_age[year]
        )
    lifetime_losses[sim] = annual_outcomes[sim].sum()

# ============================================================
# Print Summary Statistics
# ============================================================
print("=" * 55)
print("  Q3 Monte Carlo Results - Age 21 to 65")
print("=" * 55)
print(f"  Simulations:            {N_SIMULATIONS:,}")
print(f"  P(gambles):             {P_GAMBLES:.0%}")
print(f"  Parameters:             age-varying (interpolated)")
print()
print("  --- Lifetime Outcomes ---")
print(f"  Mean lifetime loss:     ${np.mean(lifetime_losses):,.2f}")
print(f"  Median lifetime loss:   ${np.median(lifetime_losses):,.2f}")
print(f"  Std deviation:          ${np.std(lifetime_losses):,.2f}")
print(f"  Best case (1st pct):    ${np.percentile(lifetime_losses,  1):,.2f}")
print(f"  10th percentile:        ${np.percentile(lifetime_losses, 10):,.2f}")
print(f"  90th percentile:        ${np.percentile(lifetime_losses, 90):,.2f}")
print(f"  Worst case (99th pct):  ${np.percentile(lifetime_losses, 99):,.2f}")
print()
print("  --- Risk Metrics ---")
print(f"  % who are net losers:       {np.mean(lifetime_losses < 0)*100:.1f}%")
print(f"  % who lose > $10,000:       {np.mean(lifetime_losses < -10_000)*100:.1f}%")
print(f"  % who lose > $50,000:       {np.mean(lifetime_losses < -50_000)*100:.1f}%")
print(f"  % who lose > $100,000:      {np.mean(lifetime_losses < -100_000)*100:.1f}%")
print(f"  % who come out ahead:       {np.mean(lifetime_losses > 0)*100:.1f}%")
print("=" * 55)

# ============================================================
# Plots
# ============================================================
cumulative = np.cumsum(annual_outcomes, axis=1)
mean_cum   = np.mean(cumulative, axis=0)
p1_cum     = np.percentile(cumulative,  1, axis=0)
p10_cum    = np.percentile(cumulative, 10, axis=0)
p25_cum    = np.percentile(cumulative, 25, axis=0)
p75_cum    = np.percentile(cumulative, 75, axis=0)
p90_cum    = np.percentile(cumulative, 90, axis=0)
p99_cum    = np.percentile(cumulative, 99, axis=0)

fig = plt.figure(figsize=(18, 10))
fig.patch.set_facecolor('#0f1117')
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

BLUE     = '#4C9BE8'
RED      = '#E84C4C'
ORANGE   = '#F5A623'
GREEN    = '#4CE8A0'
BG       = '#0f1117'
PANEL_BG = '#1a1d27'
TEXT     = '#E0E0E0'

def style_ax(ax, title):
    ax.set_facecolor(PANEL_BG)
    ax.set_title(title, color=TEXT, fontsize=10, fontweight='bold', pad=8)
    ax.tick_params(colors=TEXT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor('#333344')
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)

fig.suptitle(
    f'Q3 Monte Carlo - Age-Varying Parameters  |  P(gambles)={P_GAMBLES:.0%}  |  n={N_SIMULATIONS:,} simulations',
    color=TEXT, fontsize=12, fontweight='bold', y=0.98
)

# Plot 1: Lifetime loss histogram
ax1 = fig.add_subplot(gs[0, 0])
ax1.hist(lifetime_losses, bins=80, color=BLUE, edgecolor='none', alpha=0.85)
ax1.axvline(np.mean(lifetime_losses), color=RED, linestyle='--', linewidth=1.5,
            label=f'Mean: ${np.mean(lifetime_losses):,.0f}')
ax1.axvline(np.median(lifetime_losses), color=ORANGE, linestyle='--', linewidth=1.5,
            label=f'Median: ${np.median(lifetime_losses):,.0f}')
ax1.axvline(0, color='white', linestyle='-', linewidth=1, label='Break even')
ax1.set_xlabel('Lifetime Gain/Loss ($)')
ax1.set_ylabel('Count')
style_ax(ax1, 'Distribution of Lifetime Outcomes')
ax1.legend(fontsize=7, facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.8)

# Plot 2: Cumulative loss over time with bands
ax2 = fig.add_subplot(gs[0, 1])
ax2.fill_between(ages_sim, p1_cum,  p99_cum, alpha=0.10, color=BLUE, label='1-99th pct')
ax2.fill_between(ages_sim, p10_cum, p90_cum, alpha=0.20, color=BLUE, label='10-90th pct')
ax2.fill_between(ages_sim, p25_cum, p75_cum, alpha=0.35, color=BLUE, label='25-75th pct')
ax2.plot(ages_sim, mean_cum, color=RED, linewidth=2, label='Mean')
ax2.axhline(0, color='white', linestyle='--', linewidth=0.8)
ax2.set_xlabel('Age')
ax2.set_ylabel('Cumulative Gain/Loss ($)')
style_ax(ax2, 'Cumulative Loss Over Lifetime')
ax2.legend(fontsize=7, facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.8)

# Plot 3: % in net loss by age
ax3 = fig.add_subplot(gs[0, 2])
pct_loss = np.mean(cumulative < 0, axis=0) * 100
ax3.plot(ages_sim, pct_loss, color=RED, linewidth=2)
ax3.fill_between(ages_sim, pct_loss, alpha=0.2, color=RED)
ax3.axhline(50, color='white', linestyle='--', linewidth=0.8, label='50% line')
ax3.set_xlabel('Age')
ax3.set_ylabel('% of Simulations')
ax3.set_ylim(0, 100)
style_ax(ax3, '% of People with Net Loss by Age')
ax3.legend(fontsize=7, facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.8)

# Plot 4: Interpolated mu by age
ax4 = fig.add_subplot(gs[1, 0])
ax4.plot(ages_sim, mu_by_age, color=GREEN, linewidth=2, label='Interpolated mu')
mask = bracket_ages <= 65
ax4.scatter(bracket_ages[mask], bracket_mus[mask],
            color=ORANGE, zorder=5, s=60, label='Q2 bracket values')
ax4.axhline(0, color='white', linestyle='--', linewidth=0.8)
ax4.set_xlabel('Age')
ax4.set_ylabel('Expected Annual Loss ($)')
style_ax(ax4, 'Expected Annual Loss by Age (Interpolated)')
ax4.legend(fontsize=7, facecolor=PANEL_BG, labelcolor=TEXT, framealpha=0.8)

# Plot 5: Mean simulated annual outcome by age
ax5 = fig.add_subplot(gs[1, 1])
mean_annual = np.mean(annual_outcomes, axis=0)
ax5.plot(ages_sim, mean_annual, color=ORANGE, linewidth=2)
ax5.fill_between(ages_sim, mean_annual, alpha=0.2, color=ORANGE)
ax5.axhline(0, color='white', linestyle='--', linewidth=0.8)
ax5.set_xlabel('Age')
ax5.set_ylabel('Mean Simulated Annual Loss ($)')
style_ax(ax5, 'Mean Simulated Annual Loss by Age')

# Plot 6: Summary stats table
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis('off')
style_ax(ax6, 'Summary Statistics')
rows = [
    ['Mean lifetime loss',   f'${np.mean(lifetime_losses):,.0f}'],
    ['Median lifetime loss', f'${np.median(lifetime_losses):,.0f}'],
    ['Std deviation',        f'${np.std(lifetime_losses):,.0f}'],
    ['10th percentile',      f'${np.percentile(lifetime_losses, 10):,.0f}'],
    ['90th percentile',      f'${np.percentile(lifetime_losses, 90):,.0f}'],
    ['% net losers',         f'{np.mean(lifetime_losses < 0)*100:.1f}%'],
    ['% lose > $10k',        f'{np.mean(lifetime_losses < -10_000)*100:.1f}%'],
    ['% lose > $50k',        f'{np.mean(lifetime_losses < -50_000)*100:.1f}%'],
    ['% come out ahead',     f'{np.mean(lifetime_losses > 0)*100:.1f}%'],
]
table = ax6.table(cellText=rows, colLabels=['Metric', 'Value'],
                  cellLoc='center', loc='center', bbox=[0, 0.05, 1, 0.9])
table.auto_set_font_size(False)
table.set_fontsize(8.5)
for (row, col), cell in table.get_celld().items():
    cell.set_facecolor('#252836' if row % 2 == 0 else PANEL_BG)
    cell.set_text_props(color=TEXT)
    cell.set_edgecolor('#333344')
    if row == 0:
        cell.set_facecolor('#2e3250')
        cell.set_text_props(color=TEXT, fontweight='bold')

plt.savefig('q3_monte_carlo_final.png', dpi=150, bbox_inches='tight', facecolor=BG)
print('\nPlot saved as q3_monte_carlo_final.png')
plt.show()
