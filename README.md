# macro-pulse

> A macro-driven dynamic asset allocation engine designed to classify economic regimes and optimize cross-border portfolios across the US, Australian, and South Korean markets.

---

## Key Features

* **Macro Regime Classification:** Evaluates core macroeconomic indicators—yield curve spreads, unemployment rates, and central bank policy rates—to automatically classify market conditions into four distinct economic phases: Goldilocks, Overheating, Stagflation, or Recession.
* **Multi-Market Data Tracking:** Ingests and synchronizes historical time-series pricing data across global benchmarks:
  * **US:** SPY, QQQ, TLT
  * **Australia:** IOZ.AX, VGB.AX
  * **South Korea:** KOSPI
  * **Global Commodities:** DBC
* **Cloud Database Persistence:** Integrates with Supabase (PostgreSQL) to store raw market feed data and regime transition history.
* **Interactive Dashboard:** Built with Streamlit and Plotly, offering real-time visualization, dual-language support (English / Korean), and interactive performance metrics.

---

## Tech Stack

* **Language:** Python 3.10+
* **Database:** Supabase (PostgreSQL)
* **Data Sources:** `yfinance` (Yahoo Finance), `fredapi` (Federal Reserve Economic Data)
* **Dashboard & Charts:** Streamlit, Plotly
