CREATE TABLE IF NOT EXISTS mp_macro_market_data (
    date DATE PRIMARY KEY,           -- 기준 날짜 (고유 기본 키)

    -- [거시경제 지표 (FRED)]
    fed_funds NUMERIC(5, 2),         -- 미국 기준금리 (FEDFUNDS)
    dgs3m NUMERIC(6, 2),             -- 3개월 국채금리 (DGS3MO)
    dgs2 NUMERIC(6, 2),              -- 2년 국채금리 (DGS2)
    dgs10 NUMERIC(6, 2),             -- 10년 국채금리 (DGS10)
    dgs30 NUMERIC(6, 2),             -- 30년 국채금리 (DGS30)
    t10y2y NUMERIC(5, 2),            -- 장단기 금리차 (T10Y2Y, 10년물-2년물)
    t10y3m NUMERIC(6, 2),            -- 10년-3개월 금리차 (T10Y3M)
    hy_spread NUMERIC(6, 2),         -- 하이일드 스프레드 (BAMLH0A0HYM2)
    unrate NUMERIC(5, 2),            -- 실업률 (UNRATE)
    cpi_yoy NUMERIC(6, 2),           -- CPI 전년비 (CPIAUCSL에서 계산)
    m2sl NUMERIC(15, 2),             -- M2 통화량 (M2SL)
    dollar NUMERIC(8, 2),            -- 달러지수 (DTWEXBGS)

    -- [시장 자산 가격 (yfinance)]
    spy NUMERIC(10, 2),              -- 미국 S&P 500 (SPY)
    qqq NUMERIC(10, 2),              -- 미국 나스닥 100 (QQQ)
    tlt NUMERIC(10, 2),              -- 미국 장기채 (TLT)
    ioz_ax NUMERIC(10, 2),           -- 호주 ASX 200 (IOZ.AX)
    vgb_ax NUMERIC(10, 2),           -- 호주 국채 (VGB.AX)
    kospi NUMERIC(10, 2),            -- 한국 KOSPI (^KS11)
    dbc NUMERIC(10, 2),              -- 글로벌 원자재 (DBC)

    created_at TIMESTAMP DEFAULT NOW() -- 데이터 적재 시간
);

CREATE TABLE IF NOT EXISTS mp_regime_history (
    date DATE PRIMARY KEY,           -- 기준 날짜 (고유 기본 키)
    regime_en VARCHAR(50) NOT NULL,  -- 영어 국면 명 (Goldilocks, Overheating 등)
    regime_kr VARCHAR(50) NOT NULL,  -- 한글 국면 명 (골디락스, 과열 등)
    created_at TIMESTAMP DEFAULT NOW() -- 판정 및 저장 시간
);
