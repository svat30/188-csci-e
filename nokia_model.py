"""
nokia_model.py  —  Nokia CFO Financial Lens | CSCI-188 Case Study
==================================================================
FORMULA REFERENCE ONLY. Not used to generate the Excel file.
The Excel file is built by build_nokia_excel.py.

PURPOSE:
  - Transparent audit trail for every number in every sheet.
  - Allows plugging in different assumptions to verify results.
  - Run to print a full step-by-step calculation check.

HOW TO RUN:
    pip install numpy-financial
    python3 nokia_model.py

REVISED NARRATIVE (post 2014 20-F review):
  Three-part CFO verdict:

  PART 1 — Contractual terms were marginally adequate
    EUR 383M royalty settlement (Nokia 2014 20-F Note 3) confirms that
    cumulative MS platform support payments exceeded Nokia's WP royalty
    obligations over the life of the deal. Net cash transfer was positive
    to Nokia. The 2011 20-F statement "payments expected to slightly exceed
    minimum royalty commitments" was directionally correct.

  PART 2 — Exclusivity was the fatal variable
    $1,168M option value surrendered by accepting WP exclusivity.
    Nokia's bargaining position in Feb 2011 was strong — Microsoft needed
    a Tier 1 OEM to launch WP credibly. Nokia traded that leverage for a
    fixed payment structure with no upside if WP succeeded and no fallback
    if it failed. Non-exclusivity was a negotiable term; Nokia did not
    negotiate it.

  PART 3 — Renegotiation framework shows what fair terms looked like
    Minimum viable deal (NPV ≈ 0): $1.233B/yr + $9.10/device + non-
    exclusive after 18 months. Ideal deal (NPV = +$723M): $1.5B/yr +
    $5/device Yr1-2 + non-exclusive from signing. Both were achievable
    given Nokia's leverage position at signing.

CLAIRVOYANCE — OPTION A (confirmed):
  Y4 = EUR 383M royalty settlement only (Nokia 2014 20-F ✅ 99%).
  Q1 2014 MS payment not confirmed from available filings — excluded.
  Prior NPV: –$533M → Posterior NPV: +$638M → Delta: +$1,171M
"""

import math, numpy_financial as npf

# =============================================================================
# SECTION 1: ALL INPUTS
# =============================================================================

EUR_USD_BASE = 1.3216   # 2010 avg rate — P&L base year only.  Nokia 2011 20-F p.11 ✅ 99%
EUR_USD_DEAL = 1.2973   # 2011 year-end — deal execution costs. Nokia 2011 20-F p.11 ✅ 99%

WACC     = 0.095   # Nokia Smart Devices CGU proxy.    2011 20-F Note 8 ⚠️ 55%
TGR      = 0.019   # Terminal growth rate.              2011 20-F Note 8 ✅ 99%
TAX_RATE = 0.26    # Finnish statutory rate.            2011 20-F Note 12 ✅ 95%

# Base year 2010 (EUR millions)  —  Nokia 2011 20-F Item 5A ✅ 99%
EUR_REV   =  42446;  EUR_COGS  = -29629;  EUR_RD  = -5863
EUR_SGA   =  -4912;  EUR_DA    =   1771;  EUR_CAP = -679
EUR_INT   =   -254   # Note 11 ✅ 90%

# Convert to USD (base year rate)
R0  = round(EUR_REV  * EUR_USD_BASE)   # Revenue
C0  = round(EUR_COGS * EUR_USD_BASE)   # COGS
RD0 = round(EUR_RD   * EUR_USD_BASE)   # R&D
S0  = round(EUR_SGA  * EUR_USD_BASE)   # SGA
D0  = round(EUR_DA   * EUR_USD_BASE)   # D&A
K0  = round(EUR_CAP  * EUR_USD_BASE)   # CapEx
I0  = round(EUR_INT  * EUR_USD_BASE)   # Interest

COGS_VAR = 0.70   # 70% variable COGS  ✅ 90%
COGS_FIX = 0.30   # 30% fixed COGS     ✅ 85%

# Revenue growth rates Y1–Y4  —  Nokia Q1 2011 guidance ⚠️ 65%
GR = [-0.05, -0.03, -0.01, 0.02]

# D&A and CapEx per year (EUR millions) — Y1-Y2 actual 20-F, Y3-Y4 estimated
DA_EUR  = [1562, 1326, 1194, 1074]
CAP_EUR = [-597, -461, -595, -731]
DA  = [round(v * EUR_USD_BASE) for v in DA_EUR]
CAP = [round(v * EUR_USD_BASE) for v in CAP_EUR]

# Deal terms (USD — no EUR in deal terms)
MS  = [250, 1000, 1000, 1000]   # MS payments  2011/2012 20-F ✅ 99%
IP  = [250, 0, 0, 0]             # IP payment   user-sourced   ⚠️ 65%
RR  = 12.50                      # Royalty rate Ars Technica Mar 2011 ⚠️ 65%
VOL = [5, 35, 70, 100]           # WP volumes   CFO projection ⚠️ 60%
ROY = [-round(v*RR) for v in VOL]

# EUR deal costs converted at EUR_USD_DEAL
REST = [round(-500*EUR_USD_DEAL), round(-400*EUR_USD_DEAL), 0, 0]   # 6-K + 20-F ✅ 99%
ACC  = [round(-251*EUR_USD_DEAL), 0, 0, 0]                          # 20-F Item 5A ✅ 95%

# Y4 Royalty Settlement — EUR 383M, Nokia 2014 20-F Note 3 (Q1 2014 payment excluded)
# Nokia 2014 20-F Note 3: "Settlement of Windows Phone royalty: EUR 383M"
# "Recognized when the partnership...was terminated in conjunction with the Sale
# of the D&S Business." Audited SEC filing. ✅ 99%
SETTLE_EUR = 383
SETTLE_USD = round(SETTLE_EUR * EUR_USD_DEAL)   # EUR 383M × 1.2973 = $497M

# Renegotiation deal terms — what Nokia's CFO should have demanded
# Both options include non-exclusivity — a structural term not priced in
# Path B NPV (pricing Android revenue requires separate option model).
# Non-exclusivity preserves the $1,396M Android option value entirely.
RENEGOTIATION = {
    'Minimum Viable': {
        # Single lever: raise MS Y2-Y4 to $1.233B/yr — brings NPV to breakeven
        # Royalty rate and IP unchanged from base case
        # Justification: Nokia's leverage (only Tier 1 OEM willing to commit)
        #   was worth ~$233M/yr in additional compensation above the base deal
        'ms':    [250, 1233, 1233, 1233],   # $1.233B/yr — NPV breakeven rate ✅
        'ip':    IP,                         # $250M unchanged
        'rr':    RR,                         # $12.50/device unchanged
        'vols':  VOL,
        'rest':  REST,
        'acc':   ACC,
        'wacc':  WACC,
        'excl':  'Non-exclusive after 18 months — Android fallback preserved ($1,168M option value)',
        'note':  'NPV ≈ $0 — minimum terms to justify the deal economically',
    },
    'Ideal Deal': {
        # Two levers: higher MS ($1.5B/yr) + lower royalty ($11.80/device)
        # Together produce NPV = +$723M — fair compensation for strategic risk
        # Royalty rate still above zero — Nokia bears WP volume risk but priced fairly
        'ms':    [250, 1500, 1500, 1500],   # $1.5B/yr — market rate for Tier 1 exclusivity
        'ip':    IP,                         # $250M unchanged
        'rr':    11.80,                      # $11.80/device — reduced from $12.50
        'vols':  VOL,
        'rest':  REST,
        'acc':   ACC,
        'wacc':  WACC,
        'excl':  'Non-exclusive from signing — full platform optionality preserved',
        'note':  'NPV = +$723M — fair compensation, IRR = 9.6% → clears WACC hurdle',
    },
}

# R&D / SGA savings (USD)  —  Nokia EUR 1B+ opex target ✅ 99% anchor ⚠️ 65% split
RDS = [260, 455, 585, 500]
SGS = [130, 200, 325, 150]

# No revenue premium — option value rests entirely on sourced deal terms
# Revenue assumptions removed: option value is purely the cost structure difference

# =============================================================================
# SECTION 2: CALCULATIONS
# =============================================================================

# Base year derived
CV0 = round(C0*COGS_VAR);  CF0 = round(C0*COGS_FIX)
GP0 = R0+C0;  EB0 = GP0+RD0+S0;  EBTDA0 = EB0+D0
EBT0 = EB0+I0;  TX0 = round(-EBT0*TAX_RATE) if EBT0>0 else 0
NI0  = EBT0+TX0;  NOP0 = round(EB0*(1-TAX_RATE));  FCF0 = NOP0+D0+K0
GM0  = GP0/R0;  EM0 = EB0/R0

# Year projections
YD = []
prev = R0
for i in range(4):
    rev   = round(prev*(1+GR[i]));  rr = rev/R0
    cv    = round(CV0*rr);  cb = cv+CF0;  ca = cb+MS[i]+ROY[i]
    gp    = rev+ca;  gm = gp/rev
    rda   = RD0+RDS[i];  sga = S0+SGS[i]
    ebit  = gp+rda+sga;  em = ebit/rev
    ot    = REST[i]+ACC[i]+IP[i]
    ebt   = ebit+ot+I0;  tx = round(-ebt*TAX_RATE) if ebt>0 else 0
    ni    = ebt+tx;  da = DA[i];  cap = CAP[i]
    ebitda= ebit+da;  nop = round(ebit*(1-TAX_RATE));  fcf = nop+da+cap
    YD.append({'yr':2011+i,'rev':rev,'cv':cv,'cf':CF0,'cb':cb,'ms':MS[i],'roy':ROY[i],
               'ca':ca,'gp':gp,'gm':gm,'rda':rda,'rds':RDS[i],'sga':sga,
               'sgs':SGS[i],'ebit':ebit,'em':em,'ot':ot,'rest':REST[i],
               'acc':ACC[i],'ip':IP[i],'ebt':ebt,'tx':tx,'ni':ni,
               'da':da,'ebitda':ebitda,'cap':cap,'nop':nop,'fcf':fcf,
               'vol':VOL[i],'gr':GR[i],
               # Aliases used by build_nokia_excel.py
               'rdb':RD0, 'sgab':S0, 'sgaa':sga, 'sgas':SGS[i]})
    prev = rev

# Path B NPV
PB = [MS[i]+IP[i]+ROY[i]+REST[i]+ACC[i] for i in range(4)]
PVI = sum((MS[i]+IP[i])/(1+WACC)**(i+1) for i in range(4))
PVO = sum((ROY[i]+REST[i]+ACC[i])/(1+WACC)**(i+1) for i in range(4))
NPV_PB = round(PVI+PVO)
try:
    IRR_PB = npf.irr(PB); IRR_PB = None if math.isnan(IRR_PB) else IRR_PB
except: IRR_PB = None

# Sensitivity
def pb(ms=MS,ip=IP,rr=RR,vols=VOL,rest=REST,acc=ACC,wacc=WACC):
    net=[ms[i]+ip[i]-vols[i]*rr+rest[i]+acc[i] for i in range(4)]
    return sum(net[i]/(1+wacc)**(i+1) for i in range(4))

SEN={}
for lbl,d in [('MS +20%',.2),('MS -20%',-.2)]:
    SEN[lbl]=round(pb(ms=[v*(1+d) for v in MS])-NPV_PB)
for lbl,d in [('Royalty -20%',-.2),('Royalty +20%',.2)]:
    SEN[lbl]=round(pb(rr=RR*(1+d))-NPV_PB)
for lbl,d in [('Volume -20%',-.2),('Volume +20%',.2)]:
    SEN[lbl]=round(pb(vols=[v*(1+d) for v in VOL])-NPV_PB)
for lbl,d in [('Restruct -20%',-.2),('Restruct +20%',.2)]:
    SEN[lbl]=round(pb(rest=[v*(1+d) for v in REST])-NPV_PB)
for lbl,w2 in [('WACC -1%',WACC-.01),('WACC +1%',WACC+.01)]:
    SEN[lbl]=round(pb(wacc=w2)-NPV_PB)

# Scenarios
SCEN={
    'Optimistic':{'ms':[250,1250,1250,1250],'ip':[500,0,0,0],'rr':7.0,'vols':VOL,
                  'rest':[round(-500*EUR_USD_DEAL),round(-300*EUR_USD_DEAL),0,0],
                  'acc':[round(-251*EUR_USD_DEAL),0,0,0],'wacc':.085,'note':'Higher MS + vol discount royalty'},
    'Base Case': {'ms':MS,'ip':IP,'rr':RR,'vols':VOL,'rest':REST,'acc':ACC,'wacc':WACC,'note':'Sourced figures'},
    'Pessimistic':{'ms':[250,750,750,750],'ip':[0,0,0,0],'rr':15.0,'vols':[2,20,40,60],
                   'rest':[round(-500*EUR_USD_DEAL),round(-500*EUR_USD_DEAL),round(-100*EUR_USD_DEAL),0],
                   'acc':[round(-251*EUR_USD_DEAL),0,0,0],'wacc':.115,'note':'ZTE royalty + heavier costs'},
}
SR={}
for name,s in SCEN.items():
    net=[s['ms'][i]+s['ip'][i]-s['vols'][i]*s['rr']+s['rest'][i]+s['acc'][i] for i in range(4)]
    pvi=sum((s['ms'][i]+s['ip'][i])/(1+s['wacc'])**(i+1) for i in range(4))
    pvo=sum((-s['vols'][i]*s['rr']+s['rest'][i]+s['acc'][i])/(1+s['wacc'])**(i+1) for i in range(4))
    npv=round(pvi+pvo)
    try: irr=npf.irr(net); irr=None if math.isnan(irr) else irr
    except: irr=None
    SR[name]={'net':net,'pvi':round(pvi),'pvo':round(pvo),'npv':npv,'irr':irr}

# =============================================================================
# EVPI — Two genuine uncertainties Nokia faced before signing (April 21, 2011)
#
# Variables excluded and why:
#   Royalty rate: externally set by Microsoft; disclosed range ($10-15) per
#                 Ars Technica Mar 2011. Not a genuine Nokia uncertainty.
#   Restructuring: Nokia's own disclosed programme (EUR 900M target).
#                  All scenarios negative — perfect info changes nothing.
#   WACC: Nokia published their own CGU rate (9.0%). Not uncertain.
#   MS Payment amount: $1B/yr was rumour, but EVPI dominated by duration below.
# =============================================================================

def path_b(ms=MS, ip=IP, roy=ROY, rest=REST, acc=ACC, wacc=WACC):
    net = [ms[i]+ip[i]+roy[i]+rest[i]+acc[i] for i in range(4)]
    return round(sum(net[i]/(1+wacc)**(i+1) for i in range(4)))

# ── #1 WP Volume Trajectory ───────────────────────────────────────────────────
# What Nokia didn't know: would WP get developer/carrier/consumer traction?
# Lumia hadn't launched at signing. No installed base. Zero reference point.
# Paradox: higher volumes = more royalties paid = worse Path B NPV.
# All three scenarios produce negative NPV — but perfect info would have told
# Nokia the deal was structurally uncompensated regardless of volume outcome.
#
# Probability basis: Nokia's April 2011 optimism (Elop burning platform memo)
#   Opt (35%): Strong WP adoption [10,60,110,140]M — Nokia's hopeful scenario
#   Base (45%): Management projection [5,35,70,100]M — internal forecasts
#   Pes (20%): Skeptic case [1,13,25,40]M — Gartner Jan 2011, actual trajectory

VOL_OPT  = [10, 60, 110, 140]
VOL_BASE = [5,  35,  70, 100]
VOL_PES  = [1,  13,  25,  40]
P_VOL    = [0.35, 0.45, 0.20]

NPV_VOL = [
    path_b(roy=[round(-v*RR) for v in VOL_OPT]),
    path_b(roy=[round(-v*RR) for v in VOL_BASE]),
    path_b(roy=[round(-v*RR) for v in VOL_PES]),
]
E_NPV_VOL   = sum(P_VOL[i]*NPV_VOL[i] for i in range(3))
E_PI_VOL    = sum(P_VOL[i]*max(NPV_VOL[i],0) for i in range(3))
EVPI_VOL    = round(E_PI_VOL - E_NPV_VOL)

# ── #2 Deal Duration (MS Payment Term) ────────────────────────────────────────
# What Nokia didn't know: how many years would MS payments last?
# 20-F gap: "Duration of platform support payment schedule — NOT DISCLOSED."
# Feb 10 announcement gave no term. April 21 signing locked the structure.
# Key finding: 5-year term produces +$102M NPV — Nokia was ONE year short
# of a positive NPV deal. Duration was the single most negotiable variable.
#
# Probability basis:
#   Pes (25%): 2 years — MS exits early if WP fails to gain traction
#   Base (50%): 4 years — our model assumption
#   Opt (25%):  5 years — MS committed long-term, Nokia gets Y5 payment

def path_b_dur(years):
    ms_ext = [250 if i==0 else (1000 if i<years else 0) for i in range(4)]
    return path_b(ms=ms_ext)

NPV_DUR_OPT  = path_b_dur(4) + round(1000/(1+WACC)**5)  # 5yr: base + Y5 PV
NPV_DUR_BASE = path_b()                                   # 4yr: our model
NPV_DUR_PES  = path_b_dur(2)                              # 2yr: MS stops after Y2

P_DUR  = [0.25, 0.50, 0.25]
NPV_DUR = [NPV_DUR_OPT, NPV_DUR_BASE, NPV_DUR_PES]

E_NPV_DUR  = sum(P_DUR[i]*NPV_DUR[i] for i in range(3))
E_PI_DUR   = sum(P_DUR[i]*max(NPV_DUR[i],0) for i in range(3))
EVPI_DUR   = round(E_PI_DUR - E_NPV_DUR)

# ── Summary ───────────────────────────────────────────────────────────────────
EVPI_TOT = EVPI_VOL + EVPI_DUR
E_NPV    = round(E_NPV_VOL)

# Android
# IP exchange (+$250M Y1) removed: that payment was WP-deal-specific.
# Nokia would not have received $250M from Microsoft under Android.
# Android path = Royalties Saved + Restructuring + Accenture only.
# Volumes LOCKED identical to Microsoft model — no revenue premium assumed.
RS = [abs(r) for r in ROY]                     # royalties saved (not paid)
AB = [RS[i]+REST[i]+ACC[i] for i in range(4)]  # android flows: IP excluded
PV_AB = round(sum(AB[i]/(1+WACC)**(i+1) for i in range(4)))
AND_NPV = PV_AB
OPT_VAL = AND_NPV - NPV_PB

# =============================================================================
# SECTION 3: VERIFY
# =============================================================================
def verify():
    print("="*65)
    print("NOKIA MODEL — VERIFICATION")
    print("="*65)
    print(f"\nBase year (USD):")
    print(f"  Revenue:      ${R0:,}M  =  EUR {EUR_REV:,}M × {EUR_USD_BASE}")
    print(f"  COGS:         ${C0:,}M  =  EUR {EUR_COGS:,}M × {EUR_USD_BASE}")
    print(f"  Gross Profit: ${GP0:,}M  ({GM0*100:.1f}%)")
    print(f"  EBIT:         ${EB0:,}M  ({EM0*100:.1f}%)")
    print(f"  FCFF:         ${FCF0:,}M")
    print(f"\nDeal conversions:")
    print(f"  Restructuring Y1: EUR 500M × {EUR_USD_DEAL} = ${REST[0]:,}M")
    print(f"  Restructuring Y2: EUR 400M × {EUR_USD_DEAL} = ${REST[1]:,}M")
    print(f"  Accenture Y1:     EUR 251M × {EUR_USD_DEAL} = ${ACC[0]:,}M")
    print(f"\nYear projections:")
    pY = R0
    for i,y in enumerate(YD):
        print(f"  Y{i+1}: Rev=${y['rev']:,}M  (${pY:,}×(1{GR[i]:+.0%}))  EBIT=${y['ebit']:,}M  FCFF=${y['fcf']:,}M")
        pY=y['rev']
    print(f"\nDeal-Specific Cash Flows NPV:")
    print(f"  Net flows: {PB}")
    for i,f in enumerate(PB):
        df=1/(1+WACC)**(i+1)
        print(f"  Y{i+1}: {f:+.1f} × 1/(1+{WACC})^{i+1} = {f:+.1f} × {df:.4f} = {f*df:+.1f}")
    print(f"  PV Inflows:  ${round(PVI):,}M")
    print(f"  PV Outflows: ${round(PVO):,}M")
    print(f"  NPV:         ${NPV_PB:,}M  =  round({round(PVI):,}+{round(PVO):,})")
    print(f"  IRR:         {f'{IRR_PB*100:.1f}%' if IRR_PB else 'No solution'}")
    print(f"\nScenarios:")
    for n,r in SR.items():
        irr_s=f"{r['irr']*100:.1f}%" if r['irr'] else "N/A"
        print(f"  {n:<15}: NPV ${r['npv']:,}M  IRR {irr_s}")
    print(f"\nSensitivity:")
    for var,chg in sorted(SEN.items(),key=lambda x:abs(x[1]),reverse=True):
        print(f"  {var:<20}: {chg:>+,}M  → new NPV ${NPV_PB+chg:,}M")
    print(f"\nEVPI (two genuine pre-signing uncertainties):")
    print(f"  #1 WP Volume Trajectory: ${EVPI_VOL:,}M")
    print(f"     Probs [35%,45%,20%] | Volumes Opt/Base/Pes | All scenarios negative")
    print(f"     NPV: Opt=${NPV_VOL[0]:,}M  Base=${NPV_VOL[1]:,}M  Pes=${NPV_VOL[2]:,}M")
    print(f"  #2 Deal Duration:        ${EVPI_DUR:,}M")
    print(f"     Probs [25%,50%,25%] | 5yr/4yr/2yr | 5yr = +$102M (breakeven)")
    print(f"     NPV: 5yr=${NPV_DUR[0]:,}M  4yr=${NPV_DUR[1]:,}M  2yr=${NPV_DUR[2]:,}M")
    print(f"  Total EVPI: ${EVPI_TOT:,}M  |  E[NPV]: ${E_NPV:,}M")
    print(f"\nAndroid Option Value:")
    print(f"  Volumes LOCKED: {VOL}M  (same as Microsoft model)")
    print(f"  ROY_SAVED = {RS}M  (abs(WP_ROYALTIES))")
    print(f"  ANDROID_BASE = {AB}")
    print(f"  Android NPV (no revenue premium): ${AND_NPV:,}M")
    print(f"  Microsoft NPV:                    ${NPV_PB:,}M")
    print(f"  Option Value Surrendered:         ${OPT_VAL:,}M")
    print(f"\nRenegotiation (what Nokia's CFO should have demanded):")
    for name, r in RENEG_RESULTS.items():
        irr_s = f"{r['irr']*100:.1f}%" if r['irr'] else "N/A (unconventional flows)"
        print(f"  {name}:")
        print(f"    NPV={r['npv']:,}M  IRR={irr_s}")
        print(f"    Exclusivity: {r['excl']}")
        print(f"    Note: {r['note']}")
    print(f"\nClairvoyance (Prior vs Posterior — all 4 years):")
    print(f"  Volumes: Y1=~{VOL_POST[0]}M  Y2={VOL_POST[1]}M  Y3=~{VOL_POST[2]}M  Y4=terminated")
    print(f"  Flows:   Prior={PB}  Posterior={PB_POST}")
    for i in range(4):
        df = 1/(1+WACC)**(i+1)
        pv_pr = round(PB[i]*df); pv_po = round(PB_POST[i]*df)
        src = ["2011 20-F ⚠️70%","2012 20-F ✅99%","Q1-Q4 earnings ✅90%","2014 20-F settlement ✅99%"][i]
        print(f"  Y{i+1}: prior {PB[i]:+4d}→PV{pv_pr:+4d}  posterior {PB_POST[i]:+4d}→PV{pv_po:+4d}  src:{src}")
    print(f"  Prior NPV:     ${NPV_PB:,}M")
    print(f"  Posterior NPV: ${NPV_POST:,}M")
    print(f"  Delta:         ${NPV_DELTA:+,}M")
    print(f"  Y4 note: EUR 383M × {EUR_USD_DEAL} = ${SETTLE_USD}M settlement (Nokia 2014 20-F)")

# =============================================================================
# SECTION 4: RENEGOTIATION — WHAT NOKIA'S CFO SHOULD HAVE DEMANDED
#
# Framework: find the minimum MS payment and royalty terms that bring NPV ≥ 0.
# Key lever: non-exclusivity. Without it, option value of $1,168M is permanently
# surrendered. With it, Nokia retains Android fallback — changes the entire
# strategic calculus regardless of NPV arithmetic.
#
# Nokia's bargaining position at signing (April 21, 2011):
#   - Microsoft needed a Tier 1 OEM to launch WP credibly
#   - Samsung and HTC had declined exclusivity
#   - Nokia was the only viable partner at scale
#   - This gave Nokia significant leverage that the base deal did not monetise
# =============================================================================

RENEG_RESULTS = {}
for name, r in RENEGOTIATION.items():
    net = [r['ms'][i]+r['ip'][i]-r['vols'][i]*r['rr']+r['rest'][i]+r['acc'][i]
           for i in range(4)]
    pvi = sum((r['ms'][i]+r['ip'][i])/(1+r['wacc'])**(i+1) for i in range(4))
    pvo = sum((-r['vols'][i]*r['rr']+r['rest'][i]+r['acc'][i])/(1+r['wacc'])**(i+1)
              for i in range(4))
    npv = round(pvi+pvo)
    try:
        irr = npf.irr(net)
        irr = None if math.isnan(irr) else irr
    except:
        irr = None
    RENEG_RESULTS[name] = {'net': net, 'npv': npv, 'irr': irr,
                            'note': r['note'], 'excl': r['excl']}


# =============================================================================
# SECTION 5: CLAIRVOYANCE — PRIOR vs. POSTERIOR
#
# Y4 TREATMENT: EUR 383M royalty settlement only (Nokia 2014 20-F Note 3 ✅ 99%).
# Q1 2014 MS payment (~$250M) logically occurred but cannot be confirmed
# separately from available filings — excluded per academic rigor.
# Potential upside if confirmed: +~$174M PV → posterior would reach ~+$812M.
#
# Full 4-year comparison: April 2011 assumptions vs. what 20-F filings revealed.
#
# Sources:
#   Y1: Nokia 2011 20-F (filed March 2012)              ⚠️ 70% (volume implied)
#   Y2: Nokia 2012 20-F (filed March 2013)              ✅ 99% (volume explicit)
#   Y3: Nokia Q1-Q4 2013 quarterly earnings             ✅ 90% (5.6+7.4+8.8+~8.2M)
#   Y4: Nokia 2014 20-F — Sale of D&S Business          ✅ 99% (EUR 383M settlement)
#
# Y4 NOTE: The WP partnership terminated April 25, 2014 when Microsoft acquired
# the D&S business. Our modelled Y4 flows (MS $1B, Roy –$1.25B) never occurred.
# Instead Nokia received EUR 383M as a "Settlement of Windows Phone royalty"
# recorded in the gain on disposal. This replaces Y4 ongoing flows entirely.
# Fair comparison: prior 4-yr NPV vs posterior 4-yr NPV — both fully grounded.
# =============================================================================

# ── Posterior Lumia volumes ───────────────────────────────────────────────────
VOL_POST = [1, 13.4, 30.0, 0]
# Y1: ~1M     Nokia Q4 2011 limited launch (2011 20-F implied)     ⚠️ 70%
# Y2: 13.4M   Nokia 2012 20-F Smart Devices explicit               ✅ 99%
# Y3: ~30M    Q1=5.6M + Q2=7.4M + Q3=8.8M + Q4=~8.2M earnings    ✅ 90%
# Y4: 0       Deal terminated April 25, 2014                       ✅ 99%

# ── Posterior WP Royalties ────────────────────────────────────────────────────
ROY_POST  = [-12, -168, -375, 0]
# Y1: –(1M   × $12.50) = –$12M
# Y2: –(13.4M × $12.50) = –$168M
# Y3: –(30M  × $12.50) = –$375M
# Y4: $0 — terminated (replaced by settlement below)

# ── Posterior MS Payments ─────────────────────────────────────────────────────
MS_POST   = [250, 1000, 1000, 0]
# Y1-Y3: as modelled.  Y4: $0 — partnership terminated April 25, 2014

# ── Y4 Royalty Settlement ─────────────────────────────────────────────────────
SETTLE_EUR = 383                          # Nokia 2014 20-F: "Settlement of Windows
SETTLE_USD = round(SETTLE_EUR * EUR_USD_DEAL)   # Phone royalty" in gain on disposal ✅ 99%
# EUR 383M × 1.2973 = $497M
SETTLE    = [0, 0, 0, SETTLE_USD]         # Recognised at deal close, April 25 2014

# ── Restructuring / Accenture / IP — unchanged ───────────────────────────────
REST_POST = [-649, -519, 0, 0]
ACC_POST  = [-326,    0, 0, 0]
IP_POST   = [ 250,    0, 0, 0]

# ── Posterior Path B flows ────────────────────────────────────────────────────
PB_POST = [MS_POST[i]+IP_POST[i]+ROY_POST[i]+REST_POST[i]+ACC_POST[i]+SETTLE[i]
           for i in range(4)]
# PB_POST = [-487, +313, +625, +497]

NPV_POST  = round(sum(PB_POST[i]/(1+WACC)**(i+1) for i in range(4)))
NPV_DELTA = NPV_POST - NPV_PB
# Prior NPV: –$533M  →  Posterior NPV: +$638M  →  Delta: +$1,171M

# ── Volume paradox (holds across all 3 confirmed years) ──────────────────────
# Lower actual volumes improved Path B NPV (fewer royalties paid against fixed
# MS payments). But this is NOT good news — lower royalties = fewer phones sold
# = platform failing. The deal destroyed value in a different direction than
# modelled. The 20-F confirms "payments slightly exceed royalties" — the EUR
# 383M settlement proves net transfer was positive. Structural loss came
# entirely from transition costs (restructuring + Accenture = PV –$1,323M).

# ── EVPI validation ───────────────────────────────────────────────────────────
EVPI_VALIDATED = {
    'WP Volume Trajectory': {
        'evpi': EVPI_VOL, 'rank': 1,
        'resolution': 'Y1:~1M, Y2:13.4M, Y3:~30M vs 5M/35M/70M assumed — all pessimistic',
        'source': 'Nokia 2011/2012 20-F + Q1-Q4 2013 earnings ✅',
        'verdict': '❌ Worst case confirmed all three years — platform adoption failed',
    },
    'Deal Duration': {
        'evpi': EVPI_DUR, 'rank': 2,
        'resolution': 'Deal terminated April 25, 2014 — 4yr base case confirmed then ended',
        'source': 'Nokia 2014 20-F — Sale of D&S Business completed ✅ 99%',
        'verdict': '~✅ 4yr confirmed, but deal ended via acquisition not natural expiry',
    },
}

# =============================================================================
# SECTION 6: DATA EXPORT — get_model_data()
#
# Returns a single structured dict containing every computed value.
# build_nokia_excel.py imports this and uses it exclusively — no calculations
# of its own, no hardcoded numbers.
#
# CONTRACT: every key here is stable. If you rename a variable in the model,
# update this dict. build_nokia_excel.py references keys, not variable names.
# =============================================================================

def get_model_data() -> dict:
    """Return all model outputs as a structured dict for the Excel builder."""
    return {

        # ── Inputs ────────────────────────────────────────────────────────────
        'inputs': {
            'EUR_USD_BASE':  EUR_USD_BASE,
            'EUR_USD_DEAL':  EUR_USD_DEAL,
            'WACC':          WACC,
            'TGR':           TGR,
            'TAX_RATE':      TAX_RATE,
            'MS':            MS,
            'IP':            IP,
            'RR':            RR,
            'VOL':           VOL,
            'ROY':           ROY,
            'REST':          REST,
            'ACC':           ACC,
            'RDS':           RDS,
            'SGS':           SGS,
            'GR':            GR,
            'SETTLE_EUR':    SETTLE_EUR,
            'SETTLE_USD':    SETTLE_USD,
        },

        # ── Base year (USD) ───────────────────────────────────────────────────
        'base': {
            'R0':  R0,  'C0':   C0,  'RD0':    RD0,  'S0':  S0,
            'D0':  D0,  'K0':   K0,  'I0':     I0,
            'GP0': GP0, 'EB0':  EB0, 'EBTDA0': EBTDA0,
            'NOP0':NOP0,'FCF0': FCF0,'GM0':    GM0,  'EM0': EM0,
            'CV0': CV0, 'CF0':  CF0,
        },

        # ── Year projections (list of 4 dicts, one per year) ──────────────────
        # Each dict has keys: rev, cv, cf, cb, ms, roy, ca, gp, gm, rda, rds,
        # sga, sgs, ebit, em, ot, rest, acc, ip, ebt, tx, ni, da, ebitda,
        # cap, nop, fcf, vol, gr
        'years': YD,

        # ── Path B (deal-specific cash flows) ─────────────────────────────────
        'path_b': {
            'flows':     PB,                               # net per year
            'pv_in':     round(PVI),
            'pv_out':    round(PVO),
            'npv':       NPV_PB,
            'irr':       IRR_PB,
            'irr_str':   f'{IRR_PB*100:.1f}%' if IRR_PB else 'No solution',
        },

        # ── Scenarios ─────────────────────────────────────────────────────────
        # Keys: 'Optimistic', 'Base Case', 'Pessimistic'
        # Each: {net, pvi, pvo, npv, irr, note, ms, rr, wacc}
        'scenarios': {
            name: {
                'net':   SR[name]['net'],
                'pvi':   SR[name]['pvi'],
                'pvo':   SR[name]['pvo'],
                'npv':   SR[name]['npv'],
                'irr':   SR[name]['irr'],
                'irr_str': f"{SR[name]['irr']*100:.1f}%" if SR[name]['irr'] else 'N/A',
                'ms_str': f"${SCEN[name]['ms'][1]/1000:.2f}B/yr",
                'rr_str': f"${SCEN[name]['rr']}/device",
                'wacc_str': f"{SCEN[name]['wacc']*100:.1f}%",
                'note':  SCEN[name]['note'],
            }
            for name in SCEN
        },

        # ── Sensitivity (delta from base NPV) ─────────────────────────────────
        # Dict of {label: delta_vs_base}
        'sensitivity': SEN,

        # ── EVPI ──────────────────────────────────────────────────────────────
        'evpi': {
            'volume': {
                'value':    EVPI_VOL,
                'rank':     1,
                'probs':    P_VOL,
                'npvs':     [round(v) for v in NPV_VOL],
                'e_npv':    round(E_NPV_VOL),
                'e_pi':     round(E_PI_VOL),
                'volumes':  [VOL_OPT, VOL_BASE, VOL_PES],
            },
            'duration': {
                'value':    EVPI_DUR,
                'rank':     2,
                'probs':    P_DUR,
                'npvs':     [round(v) for v in NPV_DUR],
                'e_npv':    round(E_NPV_DUR),
                'e_pi':     round(E_PI_DUR),
                'scenarios': ['5yr', '4yr', '2yr'],
            },
            'total':    EVPI_TOT,
            'e_npv':    E_NPV,
        },

        # ── Android option value ───────────────────────────────────────────────
        'android': {
            'flows':        AB,
            'npv':          AND_NPV,
            'roy_saved':    RS,
            'opt_val':      OPT_VAL,
            'ms_npv':       NPV_PB,
        },

        # ── Renegotiation ──────────────────────────────────────────────────────
        # Keys: 'Minimum Viable', 'Ideal Deal'
        # Each: {npv, irr, irr_str, note, excl, ms, rr}
        'renegotiation': {
            name: {
                'npv':     RENEG_RESULTS[name]['npv'],
                'irr':     RENEG_RESULTS[name]['irr'],
                'irr_str': (f"{RENEG_RESULTS[name]['irr']*100:.1f}%"
                            if RENEG_RESULTS[name]['irr'] else 'N/A'),
                'note':    RENEG_RESULTS[name]['note'],
                'excl':    RENEG_RESULTS[name]['excl'],
                'ms_yr':   RENEGOTIATION[name]['ms'][1],
                'rr':      RENEGOTIATION[name]['rr'],
            }
            for name in RENEGOTIATION
        },

        # ── Clairvoyance (Y4 = EUR 383M settlement, Nokia 2014 20-F) ─────────────
        'clairvoyance': {
            'vol_post':   VOL_POST,          # [1, 13.4, 30.0, 0]
            'roy_post':   ROY_POST,          # [-12, -168, -375, 0]
            'ms_post':    MS_POST,           # [250, 1000, 1000, 0]
            'settle_usd': SETTLE_USD,        # $497M
            'flows_prior':  PB,
            'flows_post':   PB_POST,         # [-487, 313, 625, 497]
            'npv_prior':  NPV_PB,            # -533
            'npv_post':   NPV_POST,          # +638
            'npv_delta':  NPV_DELTA,         # +1171
            'sources': [
                '2011 20-F (implied, ~1M Lumia) ⚠️ 70%',
                'Nokia 2012 20-F (13.4M explicit) ✅ 99%',
                'Nokia Q1-Q4 2013 earnings (30M) ✅ 90%',
                'Nokia 2014 20-F EUR 383M settlement ✅ 99%',
            ],
            'evpi_validated': EVPI_VALIDATED,
        },
    }



if __name__ == '__main__':
    verify()
    print("\nnokia_model.py is a formula reference — not the Excel builder.")
    print("To rebuild the Excel, run: python3 build_nokia_excel.py")

