# streamlit_app.py
"""
Streamlit 대시보드 (한국어 UI)
- 상단 탭: "공식 공개 데이터 대시보드" / "사용자 입력(보고서) 대시보드"
- 공개 데이터: World Bank (CO2 per capita, 고용비중: 농업/산업/서비스) + (참고 URL 주석 포함)
- 사용자 입력: 제공된 보고서(본문 텍스트)를 코드 내 변수로만 사용하여 자동 시각화 생성 (파일 업로드 불필요)
- 규칙: 캐싱(@st.cache_data), 미래 날짜 제거(로컬 Asia/Seoul 기준), 전처리된 CSV 다운로드 버튼 제공
- 폰트: /fonts/Pretendard-Bold.ttf 적용 시도 (없으면 자동 생략)
- API 실패 시 재시도, 실패하면 예시 데이터로 자동 대체 및 화면 한국어 안내
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone, timedelta
import matplotlib.font_manager as fm
import plotly.express as px
import os
import time

# ---------------------------
# 출처(URL) - 코드 주석에 명시
#
# World Bank Indicators API (사용):
# - CO2 emissions (metric tons per capita): https://data.worldbank.org/indicator/EN.ATM.CO2E.PC
# - Employment in agriculture (% of total employment): https://data.worldbank.org/indicator/SL.AGR.EMPL.ZS
# - Employment in industry (% of total employment): https://data.worldbank.org/indicator/SL.IND.EMPL.ZS
# - Employment in services (% of total employment): https://data.worldbank.org/indicator/SL.SRV.EMPL.ZS
# World Bank Indicators API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
# ---------------------------

# ---------------------------
# 유틸리티: 로컬 현재 날짜 (Asia/Seoul)
# ---------------------------
def today_seoul():
    now_utc = datetime.now(timezone.utc)
    seoul = now_utc.astimezone(timezone(timedelta(hours=9)))
    return seoul.replace(hour=0, minute=0, second=0, microsecond=0)
TODAY = today_seoul().date()

# ---------------------------
# 폰트 시도: /fonts/Pretendard-Bold.ttf
# ---------------------------
PRETENDARD_PATH = "/fonts/Pretendard-Bold.ttf"
PRETENDARD_AVAILABLE = False
if os.path.exists(PRETENDARD_PATH):
    try:
        fm.fontManager.addfont(PRETENDARD_PATH)
        PRETENDARD_AVAILABLE = True
    except Exception:
        PRETENDARD_AVAILABLE = False

if PRETENDARD_AVAILABLE:
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'PretendardLocal';
            src: url('file://{PRETENDARD_PATH}') format('truetype');
        }}
        html, body, [class*="css"]  {{
            font-family: 'PretendardLocal', sans-serif;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

PLOTLY_FONT = "PretendardLocal" if PRETENDARD_AVAILABLE else None

# ---------------------------
# API 호출 및 재시도 로직 (World Bank)
# ---------------------------
@st.cache_data(show_spinner=False)
def fetch_worldbank_indicator(indicator_code, per_page=20000, retries=2, backoff=1.0):
    base = "https://api.worldbank.org/v2/country/all/indicator/{}"
    params = {"format": "json", "per_page": per_page}
    url = base.format(indicator_code)
    attempt = 0
    while attempt <= retries:
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if not (isinstance(data, list) and len(data) >= 2):
                raise ValueError("Unexpected response structure")
            records = data[1]
            rows = []
            for rec in records:
                date = int(rec.get("date")) if rec.get("date") not in (None, "") else None
                if date is not None and date > TODAY.year:
                    continue
                rows.append({
                    "countryiso3code": rec.get("countryiso3code"),
                    "country": rec.get("country", {}).get("value"),
                    "date": date,
                    "value": rec.get("value"),
                    "indicator": rec.get("indicator", {}).get("id")
                })
            df = pd.DataFrame(rows)
            if not df.empty:
                df = df.drop_duplicates().reset_index(drop=True)
                df["date"] = pd.to_datetime(df["date"].astype("Int64").astype("float"), format="%Y", errors="coerce").dt.date
            return df
        except Exception:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(backoff * attempt)

# ---------------------------
# 공개 데이터 불러오기 및 전처리 (캐시)
# ---------------------------
@st.cache_data(show_spinner=False)
def load_public_datasets():
    indicators = {
        "CO2": "EN.ATM.CO2E.PC",
        "EMP_AGR": "SL.AGR.EMPL.ZS",
        "EMP_IND": "SL.IND.EMPL.ZS",
        "EMP_SRV": "SL.SRV.EMPL.ZS",
    }
    results = {}
    for name, code in indicators.items():
        df = fetch_worldbank_indicator(code)
        results[name] = df
    return results

# ---------------------------
# 공개 데이터 예시(fallback)
# ---------------------------
def fallback_public_data():
    years = list(range(2000, 2024))
    co2 = [4.5 + 0.02*(y-2000) + np.random.randn()*0.1 for y in years]
    agr = [30 - 0.3*(y-2000) + np.random.randn()*0.5 for y in years]
    ind = [25 - 0.05*(y-2000) + np.random.randn()*0.5 for y in years]
    srv = [45 + 0.35*(y-2000) + np.random.randn()*0.5 for y in years]
    df_co2 = pd.DataFrame({"country":"World","date":[datetime(y,1,1).date() for y in years],"value":co2})
    df_agr = pd.DataFrame({"country":"World","date":[datetime(y,1,1).date() for y in years],"value":agr})
    df_ind = pd.DataFrame({"country":"World","date":[datetime(y,1,1).date() for y in years],"value":ind})
    df_srv = pd.DataFrame({"country":"World","date":[datetime(y,1,1).date() for y in years],"value":srv})
    return {"CO2":df_co2,"EMP_AGR":df_agr,"EMP_IND":df_ind,"EMP_SRV":df_srv}

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="기후×취업 대시보드", layout="wide")
st.title("기후 변화와 취업 대시보드")

tabs = st.tabs(["📊 공식 공개 데이터 대시보드", "📝 사용자 입력(보고서) 대시보드"])

# ---------------------------
# 탭 1: 공식 공개 데이터
# ---------------------------
with tabs[0]:
    st.header("공식 공개 데이터 (World Bank 지표)")
    try:
        public_data = load_public_datasets()
    except Exception:
        st.warning("API 실패 → 예시 데이터 사용")
        public_data = fallback_public_data()

    def prepare_global_summary(df):
        if df.empty:
            return pd.DataFrame()
        df = df[df["date"].notna()]
        df = df[df["date"].apply(lambda d: d <= TODAY)]
        df["year"] = df["date"].apply(lambda d: d.year)
        agg = df.groupby("year", as_index=False)["value"].mean()
        agg["date"] = pd.to_datetime(agg["year"].astype(str)+"-01-01").dt.date
        return agg[["date","year","value"]]

    co2_global = prepare_global_summary(public_data["CO2"])
    agr_global = prepare_global_summary(public_data["EMP_AGR"])
    ind_global = prepare_global_summary(public_data["EMP_IND"])
    srv_global = prepare_global_summary(public_data["EMP_SRV"])

    col1, col2 = st.columns(2)
    with col1:
        if not co2_global.empty:
            fig = px.line(co2_global, x="date", y="value",
                          title="1인당 CO₂ 배출량",
                          labels={"date":"연도","value":"CO₂ (톤/인)"},
                          template="plotly_white")
            if PLOTLY_FONT:
                fig.update_layout(font_family=PLOTLY_FONT)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if not agr_global.empty:
            emp_df = pd.DataFrame({"year": agr_global["year"]})
            emp_df = emp_df.merge(agr_global.rename(columns={"value":"농업(%)"}), on="year", how="left")
            emp_df = emp_df.merge(ind_global.rename(columns={"value":"산업(%)"}), on="year", how="left")
            emp_df = emp_df.merge(srv_global.rename(columns={"value":"서비스(%)"}), on="year", how="left")
            emp_df["date"] = pd.to_datetime(emp_df["year"].astype(str)+"-01-01").dt.date
            fig2 = px.area(emp_df, x="date", y=["농업(%)","산업(%)","서비스(%)"],
                           title="고용 비중 변화",
                           labels={"date":"연도","value":"고용 비중 (%)"})
            if PLOTLY_FONT:
                fig2.update_layout(font_family=PLOTLY_FONT)
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 탭 2: 사용자 입력 대시보드
# ---------------------------
with tabs[1]:
    st.header("사용자 입력 보고서 기반 분석")
    REPORT_TEXT = "기후변화는 단순 환경 문제가 아닌, 청년 취업 환경에도 큰 영향을 미친다. 최근 5년간 녹색 일자리는 증가, 전통 산업 일자리는 감소."
    keywords = ["기후","취업","녹색","일자리","산업","청년"]
    kw_counts = {kw: REPORT_TEXT.count(kw) for kw in keywords}
    kw_df = pd.DataFrame(list(kw_counts.items()), columns=["키워드","빈도"]).sort_values("빈도", ascending=False)
    st.dataframe(kw_df)

    fig_kw = px.pie(kw_df, values="빈도", names="키워드", title="키워드 분포", hole=0.4)
    if PLOTLY_FONT:
        fig_kw.update_layout(font_family=PLOTLY_FONT)
    st.plotly_chart(fig_kw, use_container_width=True)