# nokia_model.py — Nokia CFO Financial Model
### CSCI-188 Case Study: *Should Nokia Have Approved the Microsoft Deal in 2011?*

---

## Overview

`nokia_model.py` is the calculation engine for the Nokia CFO financial analysis. It contains every formula, assumption, and derivation used in the case study, with full source attribution. It does not produce files — that is the job of `build_nokia_excel.py`, which imports this script and uses it as its single source of truth.

The script answers one question from a CFO lens:

> *Did the terms of the Microsoft partnership adequately compensate Nokia for the revenue risk, margin compression, and loss of strategic flexibility created by exclusivity?*

**The answer the model produces: No — but not for the reason you might expect.** The contractual mechanics were marginally adequate (confirmed by the EUR 383M settlement in Nokia's 2014 20-F). The deal failed because exclusivity permanently surrendered $1,168M in Android option value with no upside protection if WP failed.

---

## Repository layout

```
nokia_model.py          ← This script. Calculation engine only.
build_nokia_excel.py    ← Excel builder. Imports get_model_data() from here.
Nokia_Financial_Model.xlsx  ← Output workbook (9 sheets). Never edit manually.
```

The separation of concerns is strict:

- **All calculations live here.** If a number looks wrong in the Excel, fix it in this script.
- **All layout and styling lives in `build_nokia_excel.py`.** It contains zero hardcoded numbers.

---

## Dependencies

```bash
pip install numpy-financial
```

`math` and `numpy_financial` are the only imports. `numpy_financial` is used exclusively for `npf.irr()`.

---

## How to run

```bash
python3 nokia_model.py
```

Running the script directly calls `verify()`, which prints a full step-by-step audit of every calculation — base year figures, deal conversions, projected cash flows, NPV derivation, sensitivity, EVPI, Android option value, renegotiation, and clairvoyance. Use this to confirm any number in the model before citing it.

To rebuild the Excel workbook after changing assumptions:

```bash
python3 build_nokia_excel.py
```

---

## Script structure

The script executes top-to-bottom when imported or run. There are no classes. All state is module-level. The sections are:

| Section | Lines | Purpose |
|---|---|---|
| **Section 1** | Inputs | All assumptions, exchange rates, deal terms |
| **Section 2** | Calculations | P&L projections, NPV, sensitivity, scenarios, EVPI, Android |
| **Section 3** | `verify()` | Audit print function |
| **Section 4** | Renegotiation | Calculated NPVs for alternative deal structures |
| **Section 5** | Clairvoyance | Prior vs posterior comparison using 20-F actuals |
| **Section 6** | `get_model_data()` | Data export interface for `build_nokia_excel.py` |

---

## Section 1 — Inputs

All inputs are defined as module-level constants with inline source citations. Every assumption carries a confidence marker: `✅` for sourced from SEC filings, `⚠️` for estimated or externally sourced.

### Exchange rates

Two rates are used. They are kept separate deliberately — mixing them would silently introduce errors.

```python
EUR_USD_BASE = 1.3216   # 2010 annual average. Used for base year P&L only.
EUR_USD_DEAL = 1.2973   # 2011 year-end rate. Used for deal execution costs.
```

Source: Nokia 2011 20-F, Item 3A exchange rate table. ✅ 99%

### Discount rates

```python
WACC     = 0.095   # 9.5% — Nokia Smart Devices CGU proxy
TGR      = 0.019   # Terminal growth rate
TAX_RATE = 0.26    # Finnish statutory corporate rate
```

WACC is the most uncertain assumption (⚠️ 55%). Nokia's own disclosed Smart Devices CGU discount rate was 9.0% (2011 20-F Note 8). The 9.5% reflects a modest premium for the specific deal risk profile.

### Base year (2010) P&L

Nokia's 2010 financials are the model anchor, sourced from Nokia 2011 20-F Item 5A. All figures start in EUR millions and are converted to USD at `EUR_USD_BASE`:

```python
EUR_REV  =  42446   →   R0  = round(42446 × 1.3216) = $56,097M
EUR_COGS = -29629   →   C0  = $-39,158M
EUR_RD   =  -5863   →   RD0 = $-7,749M
EUR_SGA  =  -4912   →   S0  = $-6,455M
EUR_DA   =   1771   →   D0  = $2,341M
EUR_CAP  =   -679   →   K0  = $-897M
EUR_INT  =   -254   →   I0  = $-336M
```

### Deal terms

All deal terms are denominated in USD. No EUR conversion is applied to deal cash flows.

```python
MS  = [250, 1000, 1000, 1000]   # Microsoft platform support payments ($M/yr)
IP  = [250,    0,    0,    0]   # One-time IP exchange payment ($M)
RR  = 12.50                      # WP royalty rate ($/device)
VOL = [5, 35, 70, 100]          # Projected WP volumes (M units/yr)
ROY = [-round(v * RR) for v in VOL]   # = [-62, -438, -875, -1250]
```

Restructuring and Accenture costs are EUR-denominated (Nokia's disclosed programmes) and converted at `EUR_USD_DEAL`:

```python
REST = [round(-500 × 1.2973), round(-400 × 1.2973), 0, 0]  # = [-649, -519, 0, 0]
ACC  = [round(-251 × 1.2973), 0, 0, 0]                      # = [-326, 0, 0, 0]
```

### COGS split

COGS is split into variable (scales with revenue) and fixed (stays flat) components. This matters for the year-by-year P&L projections:

```python
COGS_VAR = 0.70   # 70% of base COGS is variable
COGS_FIX = 0.30   # 30% is fixed overhead
```

---

## Section 2 — Calculations

### Base year derivations

Standard P&L and cash flow items are derived from the base inputs:

```
GP0   = R0 + C0                          # Gross profit
EB0   = GP0 + RD0 + S0                   # EBIT
NOP0  = round(EB0 × (1 - TAX_RATE))      # Net operating profit after tax
FCF0  = NOP0 + D0 + K0                   # Free cash flow to firm
```

### Year projections (2011–2014)

A 4-year forward P&L is built in a loop. Each year applies revenue growth to the prior year and adjusts variable COGS proportionally:

```python
rev  = round(prev × (1 + GR[i]))       # Revenue grows at GR[i]
rr   = rev / R0                         # Revenue ratio vs base year
cv   = round(CV0 × rr)                  # Variable COGS scales with revenue
cb   = cv + CF0                         # Total COGS = variable + fixed
ca   = cb + MS[i] + ROY[i]             # COGS adjusted for WP cashflows
gp   = rev + ca                         # Gross profit
ebit = gp + rda + sga                   # EBIT (R&D and SGA include savings)
nop  = round(ebit × (1 - TAX_RATE))    # NOPAT
fcf  = nop + da + cap                   # FCFF
```

Revenue growth rates `GR = [-0.05, -0.03, -0.01, +0.02]` are based on Nokia Q1 2011 management guidance (⚠️ 65%).

### Deal-Specific Cash Flows (NPV)

The core financial question is answered by isolating only the cash flows that are specific to the Microsoft deal:

```
PB[i] = MS[i] + IP[i] + ROY[i] + REST[i] + ACC[i]
```

These net flows for each year are then discounted:

```
NPV = Σ  PB[i] / (1 + WACC)^(i+1)   for i = 0..3
```

Calculated as two components for transparency:

```python
PVI = Σ (MS[i] + IP[i]) / (1+WACC)^(i+1)   # PV of inflows  = $2,748M
PVO = Σ (ROY[i] + REST[i] + ACC[i]) / (1+WACC)^(i+1)   # PV of outflows = –$3,281M
NPV_PB = round(PVI + PVO)   # = –$533M
```

**IRR note:** `npf.irr()` is called on the net flows. The base case returns `None` because the sign pattern `[–, +, +, –]` (negative in Y1 due to restructuring, positive in Y2–Y3, negative in Y4 due to royalties exceeding MS payments) is non-monotonic. The mathematical IRR function assumes a single sign change; multiple sign changes can produce no real solution or multiple solutions. This is why MIRR is the correct metric for this structure.

### Sensitivity analysis

A helper function `pb()` recomputes the deal NPV under perturbed inputs, holding all other assumptions constant. Each variable is shocked ±20%:

```python
def pb(ms, ip, rr, vols, rest, acc, wacc):
    net = [ms[i] + ip[i] - vols[i]*rr + rest[i] + acc[i] for i in range(4)]
    return Σ net[i] / (1+wacc)^(i+1)

SEN['MS +20%'] = round(pb(ms=[v*1.2 for v in MS]) - NPV_PB)   # = +$504M
```

Results show the NPV *delta* from base, ranked by magnitude. MS payments and royalty rate dominate (±$392–$504M). WACC is least sensitive (±$8M) — the 4-year horizon limits rate exposure.

### Three-scenario NPV

Three scenarios test the deal under different assumptions simultaneously:

| Scenario | MS/yr | Royalty | WACC | NPV | IRR |
|---|---|---|---|---|---|
| Optimistic | $1.25B | $7/device | 8.5% | +$1,276M | 241% |
| Base Case | $1.0B | $12.50/device | 9.5% | –$533M | No solution |
| Pessimistic | $0.75B | $15/device | 11.5% | –$920M | No solution |

The optimistic scenario is the only one with a positive NPV, requiring all three conditions to hold simultaneously with no contractual guarantee on any of them.

### EVPI — Value of Perfect Information

EVPI answers: *how much would a clairvoyant have paid to know the true value of an uncertain variable before signing?*

```
EVPI = E[NPV | Perfect Info] − E[NPV]
```

Where:
- `E[NPV]` = Σ P(s) × NPV(s) — weighted average across scenarios
- `E[NPV|PI]` = Σ P(s) × max(NPV(s), 0) — with perfect info, only sign if NPV > 0

Two variables are modelled. Variables excluded: royalty rate (externally set by Microsoft), restructuring (Nokia's own disclosed programme), WACC (Nokia published their own CGU rate).

**Variable 1 — WP Volume Trajectory ($793M)**

Three volume scenarios with assigned probabilities:

```python
VOL_OPT  = [10, 60, 110, 140]M   # P = 0.35 — Nokia's hopeful case
VOL_BASE = [ 5, 35,  70, 100]M   # P = 0.45 — management projection
VOL_PES  = [ 1, 13,  25,  40]M   # P = 0.20 — Gartner Jan 2011 trajectory
```

Note the volume paradox: higher volumes produce *worse* NPV (more royalties paid against fixed MS payments). All three scenarios are negative, so `E[NPV|PI]` captures only the pessimistic scenario's positive contribution.

**Variable 2 — Deal Duration ($764M)**

Three duration scenarios:

```python
P_DUR  = [0.25, 0.50, 0.25]   # Pes/Base/Opt
NPV_DUR = [path_b_dur(5),     # 5yr: base + PV of Y5 payment = +$102M
           path_b(),           # 4yr: base case = –$533M
           path_b_dur(2)]      # 2yr: MS stops after Y2 = –$1,990M
```

Key finding: a 5-year term would have produced +$102M NPV. Nokia was exactly one year short of breakeven. Duration was not disclosed at the February 10 announcement.

**Total EVPI: $793M + $764M = $1,557M**

### Android option value

The Android option value answers: *what is the value Nokia gave up by accepting WP exclusivity?*

The calculation holds Lumia volumes identical to the Microsoft model (no revenue premium assumed — conservative floor). The IP exchange payment (+$250M) is excluded because it was WP-deal-specific; Nokia would not have received it from Microsoft under Android.

```python
RS = [abs(r) for r in ROY]                       # Royalties saved (not paid)
AB = [RS[i] + REST[i] + ACC[i] for i in range(4)]  # Android flows
AND_NPV = round(Σ AB[i] / (1+WACC)^(i+1))         # = $635M
OPT_VAL = AND_NPV - NPV_PB                          # = $635M – (–$533M) = $1,168M
```

The $1,168M is not a revenue estimate — it is the pure cost-structure difference between the two platform paths, using Nokia's own disclosed deal terms.

---

## Section 3 — `verify()`

Running `python3 nokia_model.py` calls `verify()`, which prints a full audit trail:

```
NOKIA MODEL — VERIFICATION
================================================================

Base year (USD):
  Revenue:      $56,097M  =  EUR 42,446M × 1.3216
  Gross Profit: $16,939M  (30.2%)
  EBIT:         $2,735M   (4.9%)
  FCFF:         $3,468M

Deal conversions:
  Restructuring Y1: EUR 500M × 1.2973 = $–649M
  ...

Deal-Specific Cash Flows NPV:
  Net flows: [–537, 43, 125, –250]
  Y1: –537.0 × 1/(1+0.095)^1 = –537.0 × 0.9132 = –490.4
  ...
  NPV: –$533M
  IRR: No solution
...
```

Every number that appears in the Excel workbook or presentation can be traced to a line in this output.

---

## Section 4 — Renegotiation

The renegotiation section calculates NPV and IRR for two hypothetical deal structures, representing what Nokia's CFO should have negotiated. Both deal terms are defined in Section 1 under `RENEGOTIATION` and computed here:

```python
for name, r in RENEGOTIATION.items():
    net = [r['ms'][i] + r['ip'][i] - r['vols'][i]*r['rr'] + r['rest'][i] + r['acc'][i]
           for i in range(4)]
    npv = round(Σ (ms+ip flows) discounted - Σ (costs) discounted)
    irr = npf.irr(net)
```

| Deal | Key change | NPV | IRR |
|---|---|---|---|
| Minimum Viable | MS raised to $1.233B/yr | ≈ $0 | 9.6% |
| Ideal Deal | MS $1.5B/yr + royalty $11.80/device | +$722M | 89.6% |

**Derivation of minimum viable MS payment:**

The extra MS payment needed to close the –$533M gap, applied to Y2–Y4:
```
x × Σ 1/(1+WACC)^i  for i=2,3,4 = 533
x × 2.291 = 533
x ≈ $233M/yr  →  total = $1,000 + $233 = $1,233M/yr
```

Both deals include non-exclusivity as a structural term. Non-exclusivity is not priced into the Path B NPV — it preserves the $1,168M Android option value which requires a separate model.

---

## Section 5 — Clairvoyance

Clairvoyance compares the April 2011 prior assumptions against what Nokia's 20-F filings actually revealed — a full 4-year prior vs posterior analysis.

**Y4 treatment:** The WP partnership terminated April 25, 2014 when Microsoft acquired Nokia's D&S business. The modelled Y4 flows never occurred. Y4 is replaced by the EUR 383M royalty settlement confirmed in Nokia 2014 20-F Note 3:

```python
SETTLE_EUR = 383
SETTLE_USD = round(383 × 1.2973)   # = $497M
SETTLE     = [0, 0, 0, SETTLE_USD]
```

**Posterior flows** replace prior assumptions year by year with confirmed 20-F actuals:

| Year | Prior flow | Posterior flow | Source | Confidence |
|---|---|---|---|---|
| Y1 2011 | –$537M | –$487M | Nokia 2011 20-F | ⚠️ 70% |
| Y2 2012 | +$43M | +$313M | Nokia 2012 20-F | ✅ 99% |
| Y3 2013 | +$125M | +$625M | Q1–Q4 2013 earnings | ✅ 90% |
| Y4 2014 | –$250M | +$497M | Nokia 2014 20-F (EUR 383M) | ✅ 99% |

**Volume paradox confirmation:** Actual Lumia volumes (1M, 13.4M, ~30M) were far below model assumptions (5M, 35M, 70M) in every confirmed year. Because Nokia pays royalties per device against fixed MS payments, lower volumes *improved* Path B NPV. This is not good news — lower royalties means fewer phones sold means the platform was failing.

```
Prior NPV:     –$533M
Posterior NPV: +$638M
Delta:         +$1,171M
```

The posterior is positive because: (a) actual royalties were much lower than projected, and (b) the EUR 383M settlement replaced the modelled Y4 outflow of –$250M.

---

## Section 6 — `get_model_data()`

The public interface for `build_nokia_excel.py`. Returns a single structured dictionary containing all computed values.

```python
from nokia_model import get_model_data
D = get_model_data()
```

Top-level keys:

| Key | Type | Contents |
|---|---|---|
| `inputs` | dict | All raw parameters — WACC, rates, MS payments, volumes, etc. |
| `base` | dict | Base year 2010 derived figures (R0, C0, GP0, EBIT, FCFF, etc.) |
| `years` | list[dict] | 4-year P&L projections, one dict per year |
| `path_b` | dict | Deal-Specific Cash Flows: flows, PV in/out, NPV, IRR |
| `scenarios` | dict | Optimistic / Base Case / Pessimistic with NPV and IRR |
| `sensitivity` | dict | Variable label → NPV delta from base |
| `evpi` | dict | Volume and duration EVPI with full probability breakdown |
| `android` | dict | Option value: Android flows, NPV, royalties saved |
| `renegotiation` | dict | Minimum Viable and Ideal Deal terms and NPVs |
| `clairvoyance` | dict | Prior/posterior flows, NPVs, sources, EVPI validation |

The contract is stable: key names in `get_model_data()` do not change unless the corresponding calculation changes. `build_nokia_excel.py` references keys — it never accesses module variables directly.

---

## Modelling decisions and limitations

**COGS variable/fixed split** is estimated at 70/30. This affects the year-by-year gross margin but not the deal-specific NPV, which operates on deal cashflows only.

**No revenue premium for Android.** The Android option value calculation holds Lumia volumes identical between paths and assumes zero Android revenue uplift. This makes the $1,168M figure a conservative floor.

**IP exchange payment excluded from Android path.** The +$250M IP payment was specific to the Microsoft deal. Nokia would not have received this under Android.

**Q1 2014 MS payment excluded from clairvoyance.** Nokia almost certainly received one quarterly payment (~$250M) before the April 25, 2014 closing. However, this cannot be separately confirmed from the available 20-F filings — it is embedded in the EUR –1,054M operating cash outflow from discontinued operations. If confirmed, posterior NPV would increase by ~$174M (PV of $250M at Y4 discount factor 0.6956).

**Restructuring costs are Nokia's own disclosed figures**, not estimates. EUR 900M total programme (EUR 500M Y1 + EUR 400M Y2) sourced from Nokia Q3 2011 6-K and 2011 20-F. ✅ 99%

---

## Primary sources

| Source | File | Used for |
|---|---|---|
| Nokia 2010 20-F | https://www.nokia.com/system/files/files/form20-f-10-pdf.pdf | Base year 2010 P&L, deal terms, exchange rates |
| Nokia 2011 20-F | https://www.nokia.com/system/files/files/form20-f-11-pdf.pdf | Base year 2010 P&L, deal terms, exchange rates |
| Nokia 2012 20-F | https://www.nokia.com/system/files/files/form20-f-12-pdf.pdf | MS payment structure, Lumia Y2 volumes (13.4M) |
| Nokia 2013 20-F | https://www.nokia.com/system/files/files/2013_nokia_full_form_20-f_bmk.pdf | Continuing ops 2009–2013, D&S 2012–2013 |
| Nokia 2014 20-F | https://www.nokia.com/system/files/files/nokia_form_20-f_2014.pdf | EUR 383M WP royalty settlement (Note 3) |

All 20-F filings available on SEC Edgar under Nokia CIK `0000924613`:
`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000924613&type=20-F`
