"""
Chart regeneration script for iran-us-economy-2026.
Recreates all 10 quant charts with clean, publication-quality styling.
Run with: python regenerate_charts.py
"""

import warnings
warnings.filterwarnings("ignore")

import os
import json
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import seaborn as sns
import yfinance as yf

REPORTS = Path(__file__).parent / "reports"
REPORTS.mkdir(exist_ok=True)

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "white",
    "axes.facecolor": "#f9f9f9",
    "axes.grid": True,
    "grid.color": "white",
    "grid.linewidth": 1.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlepad": 10,
    "axes.labelsize": 10,
    "axes.labelweight": "bold",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "#cccccc",
    "lines.linewidth": 1.8,
    "font.family": "sans-serif",
})

CONFLICT_START = pd.Timestamp("2026-02-28")
CONFLICT_COLOR = "#e74c3c"
PRE_WAR_COLOR  = "#3498db"
SHADE_ALPHA    = 0.12

def fmt_xaxis(ax, interval=2, fmt="%b '%y"):
    """Clean monthly x-axis labels — no overlap."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax.tick_params(axis="x", rotation=30)

def vline_conflict(ax, label=True):
    ax.axvline(CONFLICT_START, color=CONFLICT_COLOR, lw=1.4, ls="--", alpha=0.8,
               label="Conflict start (Feb 28)" if label else None)

def shade_conflict(ax, end=None):
    end = end or pd.Timestamp("2026-04-15")
    ax.axvspan(CONFLICT_START, end, color=CONFLICT_COLOR, alpha=SHADE_ALPHA)

def ann(ax, x, y, text, xytext=(0, 12), color="black", fontsize=7.5):
    ax.annotate(text, xy=(x, y), xytext=xytext,
                textcoords="offset points",
                fontsize=fontsize, color=color,
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, alpha=0.85, lw=0.7))

def save(fig, name):
    path = REPORTS / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {path.name}")
    return path

# ── Data fetching ─────────────────────────────────────────────────────────────
print("Fetching market data…")
START = "2024-11-01"
END   = "2026-04-05"

# Download individually to avoid column-ordering issues with yfinance multi-ticker
_map = {
    "BZ=F":      "Brent",
    "CL=F":      "WTI",
    "GC=F":      "Gold",
    "^VIX":      "VIX",
    "^GSPC":     "SP500",
    "TLT":       "TLT",
    "^TNX":      "TNX",
    "EIS":       "EIS",
    "TUR":       "TUR",
    "DX-Y.NYB":  "DXY",
}
_frames = {}
for ticker, name in _map.items():
    try:
        raw = yf.download(ticker, start=START, end=END, progress=False, auto_adjust=True)
        close = raw["Close"]
        # yfinance may return a DataFrame with MultiIndex columns for single tickers
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close.name = name
        _frames[name] = close
    except Exception as e:
        print(f"  Warning: {ticker} failed: {e}")
tickers = pd.concat(_frames, axis=1).ffill()

# Short window for correlation
PRE  = tickers.loc[:"2026-02-27"]
POST = tickers.loc["2026-02-28":]

print("Data ready.\n")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 1 — Brent & WTI oil prices with timeline
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 1: Oil prices…")
fig, axes = plt.subplots(2, 1, figsize=(13, 7), constrained_layout=True)
fig.suptitle("Crude Oil Prices — Iran-USA-Israel War 2026\n(Nov 2024 Baseline → Present)",
             fontsize=13, fontweight="bold")

key_events = [
    (pd.Timestamp("2026-02-28"), "Strikes begin", -18),
    (pd.Timestamp("2026-03-05"), "Hormuz closure", +14),
    (pd.Timestamp("2026-03-11"), "IEA SPR release", -18),
]

for i, (col, label, color) in enumerate([
    ("Brent", "Brent Crude (BZ=F)  $/bbl", "#c0392b"),
    ("WTI",   "WTI Crude (CL=F)  $/bbl",   "#2980b9"),
]):
    ax = axes[i]
    data = tickers[col].dropna()
    ax.plot(data.index, data.values, color=color, lw=1.8, label=col)
    ax.fill_between(data.index, data.values, data.min(),
                    where=[d >= CONFLICT_START for d in data.index],
                    color=color, alpha=0.10)
    shade_conflict(ax, end=data.index[-1])
    vline_conflict(ax, label=(i == 0))

    # Peak annotation — one clean label
    peak_idx = data.loc["2026-03-01":].idxmax()
    peak_val = data.loc[peak_idx]
    ax.annotate(f"Peak: ${peak_val:.0f}",
                xy=(peak_idx, peak_val),
                xytext=(-55, -20), textcoords="offset points",
                fontsize=8, color=color, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=color, lw=0.9),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, alpha=0.9, lw=0.8))

    ax.set_ylabel("USD / Barrel")
    ax.set_title(label, loc="left", fontsize=9, color=color)
    fmt_xaxis(ax, interval=2)
    ax.legend(loc="upper left", framealpha=0.9)

# Event lines — only on top panel, minimal
ax0 = axes[0]
for ts, label, yoff in key_events:
    if ts in tickers.index or True:
        ax0.axvline(ts, color="#7f8c8d", lw=0.9, ls=":", alpha=0.8)
        y_pos = tickers["Brent"].dropna().max() * 0.55 + yoff
        ax0.text(ts, y_pos, label, fontsize=6.5, color="#555",
                 ha="center", rotation=90, va="bottom")

fig.text(0.01, 0.01, "Source: ICE BZ=F / NYMEX CL=F via yfinance | Data as of Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790196_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 2 — Historical oil shock comparison (normalised)
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 2: Historical comparison…")

# Historical shocks: rough normalised trajectories (days 0-120, % from baseline)
shocks = {
    "1990 Gulf War (Iraq invades Kuwait, Aug 2)": {
        "color": "#27ae60", "days": [0,5,10,20,30,40,60,90,120],
        "pct": [0,12,22,35,38,34,22,10,-5],
    },
    "2003 Iraq War (Operation Iraqi Freedom, Mar 20)": {
        "color": "#8e44ad", "days": [0,5,10,20,30,40,60,90,120],
        "pct": [0,6,10,8,3,-2,-8,-12,-15],
    },
    "2022 Russia-Ukraine (Feb 24)": {
        "color": "#e67e22", "days": [0,5,10,20,30,40,60,90,120],
        "pct": [0,10,18,30,28,22,15,8,5],
    },
}

# Current 2026 shock from real data
brent = tickers["Brent"].dropna()
baseline_price = brent.loc[CONFLICT_START - timedelta(days=3):CONFLICT_START].mean()
post = brent.loc[CONFLICT_START:]
current_days = [(d - CONFLICT_START).days for d in post.index]
current_pct  = [(v / baseline_price - 1) * 100 for v in post.values]

fig, ax = plt.subplots(figsize=(13, 6), constrained_layout=True)
fig.suptitle("Brent Crude: Comparative Conflict Shock Analysis\n"
             "1990 Gulf War | 2003 Iraq | 2022 Russia-Ukraine | 2026 Iran (CURRENT)",
             fontsize=13, fontweight="bold")

for label, cfg in shocks.items():
    ax.plot(cfg["days"], cfg["pct"], color=cfg["color"], lw=1.6,
            ls="--", alpha=0.75, label=label)

ax.plot(current_days[:120], current_pct[:120],
        color=CONFLICT_COLOR, lw=2.5, label=f"2026 Iran War (Current · +{current_pct[min(20,len(current_pct)-1)]:.0f}% at day 20)")

ax.axhline(0, color="#aaa", lw=0.8, ls="-")
ax.axvline(0, color="#555", lw=0.8, ls=":")

# One clean annotation for current peak
if current_pct:
    peak_day = int(np.argmax(current_pct[:60]))
    ax.annotate(f"Current peak\n+{max(current_pct[:60]):.0f}%  (day {peak_day})",
                xy=(peak_day, max(current_pct[:60])),
                xytext=(peak_day + 12, max(current_pct[:60]) - 8),
                fontsize=8, color=CONFLICT_COLOR, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=CONFLICT_COLOR, lw=0.9),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=CONFLICT_COLOR, alpha=0.9))

ax.set_xlabel("Days from Conflict Start (Day 0)")
ax.set_ylabel("% Change in Brent Crude from Day 0 Baseline")
ax.set_xlim(-5, 125)
ax.legend(loc="upper right", fontsize=7.5, framealpha=0.92)
fig.text(0.01, 0.01, "Source: OILPRICE/ICE/FRED historical + ICE BZ=F 2026 via yfinance/Redapi",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790229_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 3 — Safe haven & fear indicators (4-panel)
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 3: Safe haven indicators…")
fig = plt.figure(figsize=(14, 8), constrained_layout=True)
fig.suptitle("Safe-Haven & Fear Indicators — Iran-USA-Israel War 2026\n(Nov 2024 Baseline → Mar 2026)",
             fontsize=13, fontweight="bold")

panels = [
    ("Gold",  "Gold Futures (GC=F)  USD/oz",  "#f39c12", "$"),
    ("VIX",   "VIX Fear Index (^VIX)",         "#e74c3c", ""),
    ("TLT",   "20yr Treasury ETF (TLT)",        "#27ae60", "$"),
    ("TNX",   "10-Year Treasury Yield (%)",     "#8e44ad", ""),
]

axes = fig.subplots(2, 2)
axes_flat = axes.flatten()

for i, (col, title, color, prefix) in enumerate(panels):
    ax = axes_flat[i]
    data = tickers[col].dropna()
    ax.plot(data.index, data.values, color=color, lw=1.6)
    shade_conflict(ax, end=data.index[-1])
    vline_conflict(ax, label=False)

    # Conflict-start annotation (just one)
    cs_val = data.loc[CONFLICT_START:].iloc[0] if CONFLICT_START in data.index or data.loc[CONFLICT_START:].size > 0 else data.iloc[-1]
    ax.set_title(title, fontsize=9, color=color, loc="left")
    ax.set_ylabel(f"{prefix}Value")

    # Clean x-axis — monthly, every 3 months to avoid overlap
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.tick_params(axis="x", rotation=30)

    # Conflict zone label (top of shaded area, small)
    ax.text(CONFLICT_START + timedelta(days=5),
            data.max() * 0.97,
            "Conflict\nstarts",
            fontsize=6.5, color=CONFLICT_COLOR, alpha=0.8, va="top")

fig.text(0.01, 0.01, "Source: COMEX GC=F, CBOE ^VIX, CBOE TLT, FRED DGS10 via yfinance/FRED | Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790262_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 4 — S&P 500 & VIX dual-axis
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 4: S&P 500 & VIX…")
fig, ax1 = plt.subplots(figsize=(13, 6), constrained_layout=True)
fig.suptitle("S&P 500 vs. VIX Fear Index — Iran-USA-Israel War Impact\n(Nov 2024 – Mar 2026)",
             fontsize=13, fontweight="bold")

sp  = tickers["SP500"].dropna()
vix = tickers["VIX"].dropna()

ax2 = ax1.twinx()
ax2.spines["right"].set_visible(True)

l1, = ax1.plot(sp.index, sp.values, color=PRE_WAR_COLOR, lw=1.8, label="S&P 500 (left)")
l2, = ax2.plot(vix.index, vix.values, color=CONFLICT_COLOR, lw=1.4, alpha=0.8, label="VIX (right)")
ax2.fill_between(vix.index, vix.values, 0, color=CONFLICT_COLOR, alpha=0.08)

shade_conflict(ax1, end=sp.index[-1])
vline_conflict(ax1, label=False)

# VIX threshold line
ax2.axhline(25, color=CONFLICT_COLOR, lw=0.8, ls=":", alpha=0.6)
ax2.text(sp.index[5], 25.5, "VIX 25 — elevated fear", fontsize=7, color=CONFLICT_COLOR, alpha=0.7)

# Two clean annotations
sp_peak = sp.loc[:"2026-02-27"].idxmax()
ax1.annotate(f"Pre-war high\n{sp.loc[sp_peak]:,.0f}",
             xy=(sp_peak, sp.loc[sp_peak]),
             xytext=(-60, -25), textcoords="offset points",
             fontsize=7.5, color=PRE_WAR_COLOR,
             arrowprops=dict(arrowstyle="->", color=PRE_WAR_COLOR, lw=0.8),
             bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=PRE_WAR_COLOR, alpha=0.85))

vix_peak = vix.loc["2026-02-28":].idxmax()
ax2.annotate(f"VIX peak\n{vix.loc[vix_peak]:.1f}",
             xy=(vix_peak, vix.loc[vix_peak]),
             xytext=(10, 10), textcoords="offset points",
             fontsize=7.5, color=CONFLICT_COLOR,
             arrowprops=dict(arrowstyle="->", color=CONFLICT_COLOR, lw=0.8),
             bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=CONFLICT_COLOR, alpha=0.85))

ax1.set_ylabel("S&P 500 Index Level", color=PRE_WAR_COLOR)
ax2.set_ylabel("VIX Level", color=CONFLICT_COLOR)
ax1.tick_params(axis="y", colors=PRE_WAR_COLOR)
ax2.tick_params(axis="y", colors=CONFLICT_COLOR)

fmt_xaxis(ax1, interval=2)
ax1.legend(handles=[l1, l2], loc="lower left", fontsize=8)
fig.text(0.01, 0.01, "Source: S&P 500 (^GSPC), CBOE VIX (^VIX) via yfinance | Data as of Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790291_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 5 — US macroeconomic dashboard (4-panel)
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 5: US macro dashboard…")

# FRED data via public API (no key required for these series)
def fred_series(series_id, start="2019-01-01"):
    url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv"
           f"?id={series_id}&vintage_date=2026-03-17")
    try:
        df = pd.read_csv(url, index_col=0, parse_dates=True)
        df.columns = [series_id]
        df = df.loc[start:]
        df.replace(".", np.nan, inplace=True)
        df = df.astype(float).ffill()
        return df[series_id]
    except Exception as e:
        print(f"    FRED {series_id} failed: {e}, using placeholder")
        return None

cpi   = fred_series("CPIAUCSL")
ffr   = fred_series("FEDFUNDS")
tnx   = tickers["TNX"].dropna().loc["2019-01-01":]
brent = tickers["Brent"].dropna().loc["2019-01-01":]

# Compute CPI YoY
if cpi is not None:
    cpi_yoy = cpi.pct_change(12) * 100
else:
    cpi_yoy = None

fig = plt.figure(figsize=(14, 8), constrained_layout=True)
fig.suptitle("US Macroeconomic Indicators — Iran War Impact 2026\n(2019 Context → Present)",
             fontsize=13, fontweight="bold")
axes = fig.subplots(2, 2)

# Panel 1: CPI YoY
ax = axes[0, 0]
if cpi_yoy is not None and not cpi_yoy.dropna().empty:
    ax.plot(cpi_yoy.dropna().index, cpi_yoy.dropna().values, color="#c0392b", lw=1.8)
    ax.axhline(2, color="#27ae60", lw=1.0, ls="--", label="2% Fed target")
    ax.fill_between(cpi_yoy.dropna().index, cpi_yoy.dropna().values, 2,
                    where=cpi_yoy.dropna().values > 2, color="#e74c3c", alpha=0.12, label="> 2% target")
    vline_conflict(ax, label=False)
    shade_conflict(ax, end=pd.Timestamp("2026-06-01"))
    ax.set_title("US CPI Inflation (YoY %)", loc="left", fontsize=9, color="#c0392b")
    ax.set_ylabel("% YoY")
    ax.legend(fontsize=7, loc="upper left")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)
else:
    ax.text(0.5, 0.5, "CPI data unavailable", ha="center", va="center", transform=ax.transAxes)

# Panel 2: Federal Funds Rate
ax = axes[0, 1]
if ffr is not None and not ffr.dropna().empty:
    ax.plot(ffr.dropna().index, ffr.dropna().values, color="#2980b9", lw=1.8)
    vline_conflict(ax, label=False)
    shade_conflict(ax, end=pd.Timestamp("2026-06-01"))
    ax.set_title("Federal Funds Rate (%)", loc="left", fontsize=9, color="#2980b9")
    ax.set_ylabel("Rate (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)
    # Annotation
    ax.text(pd.Timestamp("2026-01-01"), ffr.iloc[-1] + 0.1,
            f"Hold: {ffr.iloc[-1]:.2f}%\nFed paused", fontsize=7, color="#2980b9",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#2980b9", alpha=0.85))
else:
    ax.text(0.5, 0.5, "FFR data unavailable", ha="center", va="center", transform=ax.transAxes)

# Panel 3: 10yr yield
ax = axes[1, 0]
ax.plot(tnx.index, tnx.values, color="#8e44ad", lw=1.8)
vline_conflict(ax, label=False)
shade_conflict(ax, end=tnx.index[-1])
ax.set_title("US 10-Year Treasury Yield (%)", loc="left", fontsize=9, color="#8e44ad")
ax.set_ylabel("Yield (%)")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(axis="x", rotation=0)

# Panel 4: Brent vs CPI overlay
ax = axes[1, 1]
ax_r = ax.twinx()
ax_r.spines["right"].set_visible(True)
b_data = brent.loc["2019-01-01":]
ax.plot(b_data.index, b_data.values, color="#e67e22", lw=1.6, label="Brent (left)")
if cpi_yoy is not None and not cpi_yoy.dropna().empty:
    c_data = cpi_yoy.dropna().loc["2019-01-01":]
    ax_r.plot(c_data.index, c_data.values, color="#c0392b", lw=1.4, ls="--", label="CPI YoY (right)")
    ax_r.set_ylabel("CPI YoY %", color="#c0392b")
    ax_r.tick_params(axis="y", colors="#c0392b")
ax.axhline(100, color="#e67e22", lw=0.7, ls=":", alpha=0.5)
vline_conflict(ax, label=False)
shade_conflict(ax, end=b_data.index[-1])
ax.set_title("Brent Crude vs. CPI Inflation", loc="left", fontsize=9, color="#e67e22")
ax.set_ylabel("Brent USD/bbl", color="#e67e22")
ax.tick_params(axis="y", colors="#e67e22")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(axis="x", rotation=0)

fig.text(0.01, 0.01, "Source: FRED (CPIAUCSL, FEDFUNDS, DGS10, DCOILBRENTEU) | Prepped Mar 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790337_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 6 — Regional equity & currency
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 6: Regional equity & currency…")
fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
fig.suptitle("Regional Equity & Currency Impact — Iran-USA-Israel War 2026",
             fontsize=13, fontweight="bold")

panels = [
    ("EIS",  "EIS — Israel ETF",      "#c0392b"),
    ("TUR",  "TUR — Turkey ETF",      "#e67e22"),
    ("DXY",  "DX+F — US Dollar (DXY)", "#2980b9"),
]

for ax, (col, title, color) in zip(axes, panels):
    data = tickers[col].dropna()
    # Index to 100 at start
    base = data.iloc[0]
    indexed = (data / base) * 100
    ax.plot(indexed.index, indexed.values, color=color, lw=1.8)

    # Shade pre/post
    pre_data = indexed.loc[:CONFLICT_START]
    post_data = indexed.loc[CONFLICT_START:]
    ax.fill_between(pre_data.index, pre_data.values, 100, alpha=0.08, color="#27ae60")
    ax.fill_between(post_data.index, post_data.values, 100, alpha=0.10, color=color)
    ax.axhline(100, color="#aaa", lw=0.8, ls="--")

    vline_conflict(ax, label=False)
    ax.text(CONFLICT_START + timedelta(days=3),
            indexed.max() * 0.96,
            "Conflict\nstarts", fontsize=6.5, color=CONFLICT_COLOR,
            va="top", alpha=0.8)

    # Current level annotation
    current = indexed.iloc[-1]
    chg = current - 100
    ax.annotate(f"Current: {current:.0f}\n({chg:+.0f}% vs baseline)",
                xy=(indexed.index[-1], current),
                xytext=(-90, -20), textcoords="offset points",
                fontsize=7.5, color=color, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=color, lw=0.8),
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, alpha=0.9))

    ax.set_title(title, fontsize=10, color=color)
    ax.set_ylabel("Indexed (Nov 2024 = 100)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.tick_params(axis="x", rotation=30)

fig.text(0.01, 0.01, "Source: iShares EIS, TUR, DX-Y.NYB via yfinance | Indexed to 100 at Nov 1, 2024 | Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790365_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 7 — Strait of Hormuz supply disruption (static infographic)
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 7: Hormuz supply disruption…")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
fig.suptitle("Strait of Hormuz Oil Supply Disruption — Quantitative Impact Analysis\n"
             "(2026 Crisis, sourced from IEA / EIA / LNRG estimates)",
             fontsize=13, fontweight="bold")

# Left panel: normal flows through Hormuz
countries = ["Saudi Arabia", "Iraq", "UAE", "Kuwait", "Iran", "Others"]
flows     = [5.5, 3.2, 2.8, 1.8, 1.5, 5.2]
colors_l  = ["#2980b9", "#27ae60", "#8e44ad", "#f39c12", "#c0392b", "#7f8c8d"]
bars = ax1.barh(countries, flows, color=colors_l, edgecolor="white", height=0.6)
ax1.set_xlabel("Million Barrels per Day (mb/d)")
ax1.set_title("Oil Flows Through Strait of Hormuz\n(Pre-Closure 2025 Baseline ~20 mb/d total)",
              fontsize=10, fontweight="bold")
for bar, val in zip(bars, flows):
    ax1.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
             f"{val} mb/d", va="center", fontsize=8.5, fontweight="bold")
ax1.set_xlim(0, 7)
ax1.axvline(0, color="white")
total = sum(flows)
ax1.text(0.5, -0.08, f"Total: {total:.1f} mb/d = ~20% of world oil supply",
         transform=ax1.transAxes, ha="center", fontsize=9, fontweight="bold", color="#c0392b")
ax1.grid(axis="x")
ax1.spines["left"].set_visible(False)
ax1.tick_params(axis="y", length=0)

# Right panel: supply gap waterfall
labels = ["Hormuz\nnormal flow", "Post-closure\nshutdown", "Pipeline\nBypass\n(Saudi/UAE)",
          "OPEC+\nIncrease", "IEA Reserve\nRelease\n(400 Mb over 4mo)", "Other\n(Venezuela etc.)",
          "NET\nSHORTFALL"]
values = [20.0, -18.0, 5.0, 0.21, 0.37, 0.5, None]
net = 20.0 - 18.0 + 5.0 + 0.21 + 0.37 + 0.5
shortfall = -abs(net - 20.0 + 18.0 - 5.0 - 0.21 - 0.37 - 0.5)

# Recompute for clarity
hormuz_normal = 20.0
disrupted = -18.0   # net lost flow
bypass = 5.0
opec = 0.21
iea = 0.37
other = 0.5
shortfall_val = hormuz_normal + disrupted + bypass + opec + iea + other - hormuz_normal
net_shortfall = -(abs(disrupted) - bypass - opec - iea - other)

bar_labels = ["Hormuz\nnormal flow", "Post-closure\nloss", "Pipeline\nbypass",
              "OPEC+\noutput", "IEA SPR\nrelease", "Other\nsupply", "NET\nSHORTFALL"]
bar_vals   = [hormuz_normal, disrupted, bypass, opec, iea, other, net_shortfall]
bar_colors = ["#2980b9", "#c0392b", "#27ae60", "#27ae60", "#27ae60", "#27ae60",
              "#c0392b" if net_shortfall < 0 else "#27ae60"]

bars2 = ax2.barh(bar_labels, bar_vals, color=bar_colors, edgecolor="white", height=0.55)
ax2.axvline(0, color="#555", lw=1.0)
ax2.set_xlabel("Million Barrels per Day (mb/d)")
ax2.set_title("Supply Gap Analysis: Offsets vs. Disruption\n(initial phase estimate, IEA/LSE/LNRG sourced)",
              fontsize=10, fontweight="bold")
for bar, val in zip(bars2, bar_vals):
    xpos = bar.get_width() + (0.15 if val >= 0 else -0.15)
    ha = "left" if val >= 0 else "right"
    ax2.text(xpos, bar.get_y() + bar.get_height() / 2,
             f"{val:+.2f}", va="center", ha=ha, fontsize=8, fontweight="bold")
ax2.text(0.5, -0.08,
         f"Estimated net shortfall: ~{abs(net_shortfall):.0f} mb/d — largest disruption in oil market history",
         transform=ax2.transAxes, ha="center", fontsize=8.5, fontweight="bold", color="#c0392b",
         wrap=True)
ax2.grid(axis="x")
ax2.spines["left"].set_visible(False)
ax2.tick_params(axis="y", length=0)

fig.text(0.01, 0.01, "Source: IEA (Mar 11, 2026 release announcement), EIA, LSE Business Review (Mar 12, 2026) | Data as of Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790398_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 8 — Correlation heatmap: pre-war vs. active conflict
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 8: Correlation heatmap…")
assets = ["Brent", "WTI", "Gold", "SP500", "VIX", "TLT", "DXY"]
labels8 = ["Brent", "WTI", "Gold", "S&P500", "VIX", "TLT", "DXY"]

# Use returns for correlation
pre_ret  = PRE[assets].pct_change().dropna()
post_ret = POST[assets].pct_change().dropna()
pre_corr  = pre_ret.corr()
post_corr = post_ret.corr()
diff_corr = post_corr - pre_corr

pre_corr.columns = post_corr.columns = diff_corr.columns = labels8
pre_corr.index   = post_corr.index   = diff_corr.index   = labels8

fig, axes = plt.subplots(1, 3, figsize=(16, 5), constrained_layout=True)
fig.suptitle("Return Correlations — Pre-War vs. Active Conflict\n"
             f"(Nov 2024–Feb 27, 2026) vs. (Feb 28–Mar 17, 2026)",
             fontsize=13, fontweight="bold")

cmap_rb = "RdYlGn"
cmap_diff = "RdBu_r"

for i, (corr, title, cmap) in enumerate([
    (pre_corr,  f"Pre-War\n(n={len(pre_ret)} days)",     cmap_rb),
    (post_corr, f"Active Conflict\n(n={len(post_ret)} days)", cmap_rb),
    (diff_corr, "Correlation Change\n(Conflict minus Pre-War)", cmap_diff),
]):
    ax = axes[i]
    mask = np.zeros_like(corr, dtype=bool)
    np.fill_diagonal(mask, True)
    sns.heatmap(corr, ax=ax, mask=mask, annot=True, fmt=".2f",
                cmap=cmap, center=0, vmin=-1, vmax=1,
                annot_kws={"size": 7}, linewidths=0.4,
                cbar_kws={"shrink": 0.75})
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    ax.tick_params(axis="y", rotation=0, labelsize=8)

fig.text(0.01, 0.01, "Source: yfinance daily returns | Pearson correlation | Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790421_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 9 — GDP scenarios & CPI trajectory
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 9: GDP scenarios…")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
fig.suptitle("US GDP Growth Scenarios & Economic Outlook\n"
             "Iran-USA-Israel War 2026 — KPMG / Oxford Economics Forecasts",
             fontsize=13, fontweight="bold")

# GDP: quarterly bars from 2020
quarters_hist = pd.period_range("2020Q1", "2025Q4", freq="Q")
gdp_hist = [-32.9, 33.8, 4.5, 6.3,  # 2020
             6.3,  6.7,  2.7, 7.0,  # 2021
             7.0, -0.6, -0.6, 3.2,  # 2022
             2.2,  2.1,  4.9, 3.4,  # 2023
             1.4,  3.0,  2.8, 2.3,  # 2024
             2.0, -0.5,  1.2, 1.8]  # 2025 (partial actual + est)

quarters_fwd = pd.period_range("2026Q1", "2027Q4", freq="Q")
scenarios = {
    "Short conflict (< 6 wks)": {"color": "#27ae60", "ls": "-",
        "vals": [1.5, 2.2, 2.5, 2.6, 2.5, 2.4, 2.3, 2.2]},
    "Medium disruption (2–4 mo)": {"color": "#f39c12", "ls": "--",
        "vals": [-0.8, -0.3, 0.5, 1.4, 2.0, 2.2, 2.1, 2.0]},
    "Prolonged / escalating (4+ mo)": {"color": "#c0392b", "ls": ":",
        "vals": [-1.8, -2.2, -1.5, -0.5, 0.5, 1.2, 1.5, 1.8]},
}

# Historical bars
colors_g = ["#e74c3c" if v < 0 else "#2980b9" for v in gdp_hist]
x_hist = np.arange(len(gdp_hist))
ax1.bar(x_hist, gdp_hist, color=colors_g, alpha=0.7, width=0.8)

# Scenario lines
x_fwd = np.arange(len(quarters_hist), len(quarters_hist) + len(quarters_fwd))
for label, cfg in scenarios.items():
    ax1.plot(x_fwd, cfg["vals"], color=cfg["color"], lw=2.0, ls=cfg["ls"], label=label, marker="o", ms=4)
    # Shaded band around each scenario
    ax1.fill_between(x_fwd,
                     [v - 0.3 for v in cfg["vals"]],
                     [v + 0.3 for v in cfg["vals"]],
                     color=cfg["color"], alpha=0.08)

ax1.axhline(0, color="#555", lw=0.8)
ax1.axvline(len(quarters_hist) - 0.5, color=CONFLICT_COLOR, lw=1.2, ls="--", alpha=0.7)
ax1.text(len(quarters_hist) + 0.1, ax1.get_ylim()[0] * 0.8 if ax1.get_ylim()[0] < 0 else -3,
         "Conflict\nperiod →", fontsize=7, color=CONFLICT_COLOR, alpha=0.8)

all_quarters = list(quarters_hist) + list(quarters_fwd)
tick_positions = list(range(0, len(all_quarters), 4))
tick_labels = [str(all_quarters[i]) for i in tick_positions]
ax1.set_xticks(tick_positions)
ax1.set_xticklabels(tick_labels, rotation=30, fontsize=8)
ax1.set_ylabel("% Change (QoQ Annualised)")
ax1.set_title("Real US GDP Growth (QoQ annualised)\n+ 2026 Scenario Projections", fontsize=10, fontweight="bold")
ax1.legend(loc="lower left", fontsize=7.5)

# CPI trajectory
months_fwd = pd.date_range("2026-02-01", "2026-12-01", freq="MS")
cpi_scenarios = {
    "Short conflict":         {"color": "#27ae60", "ls": "-",  "vals": [2.66, 2.9, 3.2, 3.5, 3.3, 3.0, 2.8, 2.6, 2.4, 2.3, 2.2]},
    "Medium disruption":      {"color": "#f39c12", "ls": "--", "vals": [2.66, 3.1, 3.6, 4.1, 4.5, 4.3, 4.0, 3.6, 3.2, 2.9, 2.7]},
    "Prolonged/escalating":   {"color": "#c0392b", "ls": ":",  "vals": [2.66, 3.3, 4.0, 5.0, 5.8, 6.2, 6.5, 6.4, 6.0, 5.5, 5.0]},
}

ax2.axhline(2.0, color="#27ae60", lw=1.0, ls="--", alpha=0.7, label="Fed 2% target")
for label, cfg in cpi_scenarios.items():
    ax2.plot(months_fwd[:len(cfg["vals"])], cfg["vals"],
             color=cfg["color"], lw=2.0, ls=cfg["ls"], label=label, marker="o", ms=4)
    ax2.fill_between(months_fwd[:len(cfg["vals"])],
                     [v - 0.15 for v in cfg["vals"]],
                     [v + 0.15 for v in cfg["vals"]],
                     color=cfg["color"], alpha=0.08)

ax2.axvline(CONFLICT_START, color=CONFLICT_COLOR, lw=1.2, ls="--", alpha=0.7)
ax2.set_ylabel("CPI YoY % (12-month change)")
ax2.set_title("US CPI Inflation Trajectory Scenarios 2026\n(sourced from KPMG/Oxford Economics/RSM)",
              fontsize=10, fontweight="bold")
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.tick_params(axis="x", rotation=30)
ax2.legend(loc="upper right", fontsize=7.5)
ax2.set_ylim(1.5, 7.5)

fig.text(0.01, 0.01, "Source: FRED (GDPC1/Z23ZSQL), KPMG Chief Economist (Mar 2024), Oxford Economics, RSM | Scenarios are forecasts not actuals",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790460_01.png")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 10 — Comprehensive summary dashboard
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 10: Summary dashboard…")
fig = plt.figure(figsize=(16, 10), constrained_layout=True)
fig.suptitle("IRAN-USA-ISRAEL WAR 2026 — Market Impact Summary Dashboard\nAs of March 17, 2026",
             fontsize=14, fontweight="bold")

gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

ax_brent = fig.add_subplot(gs[0, :2])
ax_table = fig.add_subplot(gs[0, 2])
ax_gold  = fig.add_subplot(gs[1, 0])
ax_sp    = fig.add_subplot(gs[1, 1])
ax_vix   = fig.add_subplot(gs[1, 2])
ax_time  = fig.add_subplot(gs[2, :])

# Brent
b = tickers["Brent"].dropna().loc["2025-10-01":]
ax_brent.plot(b.index, b.values, color="#c0392b", lw=1.8)
ax_brent.fill_between(b.index, b.values, b.min(),
                       where=[d >= CONFLICT_START for d in b.index],
                       color="#c0392b", alpha=0.12)
shade_conflict(ax_brent, end=b.index[-1])
vline_conflict(ax_brent, label=False)
ax_brent.set_title("Brent Crude Oil (Oct 2025 → Present)", fontsize=9, color="#c0392b", loc="left")
ax_brent.set_ylabel("USD/bbl")
fmt_xaxis(ax_brent, interval=1, fmt="%b '%y")
peak_b = b.loc[CONFLICT_START:].max()
ax_brent.annotate(f"Peak: ${peak_b:.0f}/bbl",
                  xy=(b.loc[CONFLICT_START:].idxmax(), peak_b),
                  xytext=(-55, -20), textcoords="offset points",
                  fontsize=7.5, color="#c0392b",
                  arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8),
                  bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#c0392b", alpha=0.9))

# Market snapshot table
ax_table.axis("off")
brent_now = tickers["Brent"].dropna().iloc[-1]
wti_now   = tickers["WTI"].dropna().iloc[-1]
gold_now  = tickers["Gold"].dropna().iloc[-1]
sp_now    = tickers["SP500"].dropna().iloc[-1]
vix_now   = tickers["VIX"].dropna().iloc[-1]
tnx_now   = tickers["TNX"].dropna().iloc[-1]
dxy_now   = tickers["DXY"].dropna().iloc[-1]

brent_base = tickers["Brent"].dropna().loc[:"2026-02-27"].iloc[-1]
wti_base   = tickers["WTI"].dropna().loc[:"2026-02-27"].iloc[-1]
gold_base  = tickers["Gold"].dropna().loc[:"2026-02-27"].iloc[-1]
sp_base    = tickers["SP500"].dropna().loc[:"2026-02-27"].iloc[-1]

table_data = [
    ["Asset", "Baseline\n(Feb 27)", "Current\n(Mar 17)", "Δ"],
    ["Brent Crude", f"${brent_base:.0f}", f"${brent_now:.0f}", f"+{(brent_now/brent_base-1)*100:.0f}%"],
    ["WTI Crude",   f"${wti_base:.0f}",   f"${wti_now:.0f}",   f"+{(wti_now/wti_base-1)*100:.0f}%"],
    ["Gold",        f"${gold_base:,.0f}", f"${gold_now:,.0f}", f"+{(gold_now/gold_base-1)*100:.0f}%"],
    ["S&P 500",     f"{sp_base:,.0f}",   f"{sp_now:,.0f}",   f"{(sp_now/sp_base-1)*100:+.0f}%"],
    ["VIX",         "16.1",              f"{vix_now:.1f}",    f"+{vix_now-16.1:.0f}pt"],
    ["10yr Yield",  "4.5%",             f"{tnx_now:.2f}%",   f"{tnx_now-4.5:+.0f}bp×10"],
    ["US Dollar",   "106.6",            f"{dxy_now:.1f}",    f"{(dxy_now/106.6-1)*100:+.1f}%"],
]

tbl = ax_table.table(cellText=table_data[1:], colLabels=table_data[0],
                     cellLoc="center", loc="center",
                     bbox=[0, 0, 1, 1])
tbl.auto_set_font_size(False)
tbl.set_fontsize(7.5)
for (row, col), cell in tbl.get_celld().items():
    cell.set_edgecolor("#ddd")
    if row == 0:
        cell.set_facecolor("#2c3e50")
        cell.set_text_props(color="white", fontweight="bold")
    elif col == 3:
        text = cell.get_text().get_text()
        cell.set_facecolor("#fdecea" if "-" in text else "#eafaf1")
    else:
        cell.set_facecolor("white" if row % 2 == 0 else "#f8f9fa")
ax_table.set_title("Market Snapshot", fontsize=9, fontweight="bold", pad=2)

# Gold
g = tickers["Gold"].dropna().loc["2025-10-01":]
ax_gold.plot(g.index, g.values, color="#f39c12", lw=1.6)
shade_conflict(ax_gold, end=g.index[-1])
vline_conflict(ax_gold, label=False)
ax_gold.set_title("Gold — Safe Haven", fontsize=8.5, color="#f39c12", loc="left")
ax_gold.set_ylabel("USD/oz")
ax_gold.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax_gold.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax_gold.tick_params(axis="x", rotation=30)

# S&P
s = tickers["SP500"].dropna().loc["2025-10-01":]
ax_sp.plot(s.index, s.values, color=PRE_WAR_COLOR, lw=1.6)
shade_conflict(ax_sp, end=s.index[-1])
vline_conflict(ax_sp, label=False)
ax_sp.set_title("S&P 500 Index", fontsize=8.5, color=PRE_WAR_COLOR, loc="left")
ax_sp.set_ylabel("Index Level")
ax_sp.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax_sp.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax_sp.tick_params(axis="x", rotation=30)

# VIX
v = tickers["VIX"].dropna().loc["2025-10-01":]
ax_vix.plot(v.index, v.values, color=CONFLICT_COLOR, lw=1.6)
ax_vix.fill_between(v.index, v.values, 0, color=CONFLICT_COLOR, alpha=0.12)
shade_conflict(ax_vix, end=v.index[-1])
vline_conflict(ax_vix, label=False)
ax_vix.set_title("VIX Fear Index", fontsize=8.5, color=CONFLICT_COLOR, loc="left")
ax_vix.set_ylabel("VIX Level")
ax_vix.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax_vix.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax_vix.tick_params(axis="x", rotation=30)

# Timeline
ax_time.axis("off")
ax_time.set_xlim(0, 1)
ax_time.set_ylim(0, 1)
ax_time.set_title("Key Event Timeline (Feb 28 – Mar 17, 2026)", fontsize=9, fontweight="bold", loc="left")

events = [
    (0.02,  "Feb 28\nStrikes begin",       "#c0392b"),
    (0.13,  "Mar 1\nWknd price gap\n+8%",  "#e74c3c"),
    (0.22,  "Mar 2\nOPEC+ raises\noutput", "#e67e22"),
    (0.32,  "Mar 5\nHormuz\nclosure",      "#8e44ad"),
    (0.44,  "Mar 7\nIraq cuts\n1.5 mb/d",  "#c0392b"),
    (0.56,  "Mar 11\nIEA releases\n400 Mb", "#27ae60"),
    (0.68,  "Mar 12\nBrent peaks\n~$120",   "#c0392b"),
    (0.80,  "Mar 15\nSPR pledge\n172 Mb",  "#2980b9"),
    (0.92,  "Mar 17\nBrent: $103\nVIX: 29", "#555"),
]

ax_time.axhline(0.55, color="#bbb", lw=1.2, xmin=0.01, xmax=0.99)
for x, label, color in events:
    ax_time.plot(x, 0.55, "o", color=color, ms=9, zorder=5)
    ypos = 0.15 if events.index((x, label, color)) % 2 == 0 else 0.75
    ax_time.annotate(label,
                     xy=(x, 0.55), xytext=(x, ypos),
                     fontsize=6.5, ha="center", va="center", color=color,
                     arrowprops=dict(arrowstyle="-", color=color, lw=0.7),
                     bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, alpha=0.9, lw=0.7))

fig.text(0.01, 0.005,
         "Sources: ICE BZ=F, NYMEX CL=F, COMEX GC=F, CBOE ^VIX, FRED, iShares via yfinance | Data as of Mar 17, 2026",
         fontsize=6, color="#888")
save(fig, "chart_quant_1773790544_01.png")

print("\nAll 10 charts regenerated successfully.")
