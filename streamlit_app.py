# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import requests
import datetime
import io
import os

# ================================
# 폰트 설정
# ================================
font_path = './fonts/Pretendard-Bold.ttf'
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    rc('font', family='Pretendard-Bold')
    plt.rcParams['font.family'] = 'Pretendard-Bold'
else:
    if os.name == 'posix':  # Mac, Linux
        rc('font', family='AppleGothic')
        plt.rcParams['font.family'] = 'AppleGothic'
    else:  # Windows
        rc('font', family='Malgun Gothic')
        plt.rcParams['font.family'] = 'Malgun Gothic'

plt.rcParams['axes.unicode_minus'] = False

plotly_font_config = {
    'font': {'family': 'Pretendard-Bold, sans-serif'}
}

st.set_page_config(layout="wide")
st.title("기후변화와 일자리 : 녹색 전환의 기회와 위험 🌍💼")

# ================================
# 공통 함수
# ================================
def remove_future_data(df, date_col):
    today = datetime.datetime.now().date()
    df[date_col] = pd.to_datetime(df[date_col]).dt.date
    return df[df[date_col] <= today]

@st.cache_data
def get_data_from_url(url):
    """URL에서 데이터 불러오기 (CSV 또는 Excel 지원)."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.content

        if url.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif url.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        else:
            # 기본: Excel 시도
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        return df
    except Exception as e:
        st.error(f"데이터 불러오기에 실패했습니다: {e}")
        return None

# ================================
# 페이지 1. 기후변화 지표
# ================================
def run_public_data_dashboard():
    st.header("1. 공개 데이터로 보는 기후변화와 일자리")

    # 예시: 기후지표 데이터
    df_climate = pd.DataFrame({
        'year': [1990, 2000, 2010, 2020, 2023],
        '온실가스농도': [354, 370, 390, 412, 419],
        '해수면상승(mm)': [0, 2, 6, 12, 15],
        '해수온도(°C)': [14.0, 14.3, 14.7, 15.0, 15.1],
        '해양산성도(pH)': [8.2, 8.15, 8.1, 8.05, 8.03]
    })

    min_year = int(df_climate['year'].min())
    max_year = int(df_climate['year'].max())
    year_range = st.sidebar.slider(
        "기후 지표 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    df_climate_f = df_climate[(df_climate['year'] >= year_range[0]) & (df_climate['year'] <= year_range[1])]

    st.subheader("1-1. 기후변화 4대지표 추이")
    df_climate_melt = df_climate_f.melt(id_vars=['year'], var_name='지표', value_name='값')
    fig_climate = px.line(
        df_climate_melt,
        x='year',
        y='값',
        color='지표',
        title='기후변화 4대지표 변화 추이',
        markers=True,
        labels={'year':'연도', '값':'지표 값'}
    )
    fig_climate.update_layout(plotly_font_config)
    st.plotly_chart(fig_climate, use_container_width=True)

    st.download_button(
        label="✅ 기후변화 지표 데이터 다운로드 (CSV)",
        data=df_climate.to_csv(index=False).encode('utf-8'),
        file_name='기후변화_4대지표.csv',
        mime='text/csv'
    )

    st.markdown("---")

# ================================
# 페이지 2. 교육 및 취업 지표
# ================================
def run_education_employment_dashboard():
    st.header("2. 교육 및 취업 관련 지표")

    df_college = pd.DataFrame({
        'year': [2018, 2019, 2020, 2021, 2022, 2023],
        '대학진학률': [70.1, 71.3, 72.5, 73.0, 73.8, 74.6],
        '졸업 후 취업률': [65.0, 66.2, 65.8, 67.1, 68.0, 70.3]
    })

    min_year = int(df_college['year'].min())
    max_year = int(df_college['year'].max())
    year_range2 = st.sidebar.slider(
        "진학/취업 지표 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    df_college_f = df_college[(df_college['year'] >= year_range2[0]) & (df_college['year'] <= year_range2[1])]

    st.subheader("2-1. 대학 진학률 및 졸업 후 취업률 추이")
    fig_ed = px.line(
        df_college_f,
        x='year',
        y=['대학진학률', '졸업 후 취업률'],
        markers=True,
        title='대학 진학률 vs 졸업 후 취업률',
        labels={'value':'비율 (%)', 'year':'연도', 'variable':'지표'}
    )
    fig_ed.update_layout(plotly_font_config)
    st.plotly_chart(fig_ed, use_container_width=True)

    st.download_button(
        label="✅ 대학 진학/취업률 데이터 다운로드 (CSV)",
        data=df_college.to_csv(index=False).encode('utf-8'),
        file_name='대학진학취업률.csv',
        mime='text/csv'
    )

    st.markdown("---")

# ================================
# 페이지 3. 직무 기회 vs 위험
# ================================
def run_risk_opportunity_dashboard():
    st.header("3. 녹색 전환: 기회와 위험 직무 비교")

    df_op = pd.DataFrame({
        '직무': ['기후 데이터 분석가', '탄소배출권 전문가', '신재생 에너지 개발자', 'ESG 경영 컨설턴트'],
        '성장 가능성 (점수)': [95, 90, 88, 85]
    })
    df_r = pd.DataFrame({
        '직무': ['화력 발전소 기술자', '자동차 내연기관 엔지니어', '석유화학 공장 운영원'],
        '위험도 (점수)': [90, 85, 80]
    })

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("성장 가능성이 높은 녹색 직무")
        fig_op = px.bar(
            df_op,
            x='직무',
            y='성장 가능성 (점수)',
            color='성장 가능성 (점수)',
            color_continuous_scale=px.colors.sequential.Greens,
            title='새롭게 떠오르는 녹색 직무'
        )
        fig_op.update_layout(plotly_font_config)
        st.plotly_chart(fig_op, use_container_width=True)

    with col2:
        st.subheader("위험성이 높은 기존 직무")
        fig_risk = px.bar(
            df_r,
            x='직무',
            y='위험도 (점수)',
            color='위험도 (점수)',
            color_continuous_scale=px.colors.sequential.Reds,
            title='녹색 전환으로 위협받는 직무'
        )
        fig_risk.update_layout(plotly_font_config)
        st.plotly_chart(fig_risk, use_container_width=True)

    st.download_button(
        label="✅ 기회 직무 데이터 다운로드 (CSV)",
        data=df_op.to_csv(index=False).encode('utf-8'),
        file_name='녹색전환_기회.csv',
        mime='text/csv'
    )
    st.download_button(
        label="✅ 위험 직무 데이터 다운로드 (CSV)",
        data=df_r.to_csv(index=False).encode('utf-8'),
        file_name='녹색전환_위험.csv',
        mime='text/csv'
    )

# ================================
# 메인 실행
# ================================
def main():
    st.sidebar.title("메뉴 선택")
    menu = st.sidebar.radio("페이지", ["기후변화 지표", "교육 및 취업 지표", "직무 기회 vs 위험"])

    if menu == "기후변화 지표":
        run_public_data_dashboard()
    elif menu == "교육 및 취업 지표":
        run_education_employment_dashboard()
    elif menu == "직무 기회 vs 위험":
        run_risk_opportunity_dashboard()

if __name__ == "__main__":
    main()
