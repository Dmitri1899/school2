
import calendar
from datetime import date

import holidays
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="SchoolMove Calendar",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌 SchoolMove Calendar")
st.write(
    "월별 평일·주말·공휴일을 분석해 "
    "실제 달력 기준으로 예상 교통비를 계산합니다."
)

st.caption(
    "한국 공휴일은 holidays 라이브러리 기준입니다. "
    "학교별 방학과 재량휴업일은 별도로 반영해야 합니다."
)

# -----------------------------
# 사용자 입력
# -----------------------------
st.sidebar.header("⚙️ 계산 설정")

current_year = date.today().year

year = st.sidebar.number_input(
    "분석 연도",
    min_value=2020,
    max_value=2100,
    value=current_year,
    step=1
)

fare = st.sidebar.number_input(
    "편도 교통요금 (원)",
    min_value=0,
    value=1500,
    step=50
)

weekday_trips = st.sidebar.selectbox(
    "평일 하루 이용 횟수",
    options=[1, 2, 3, 4],
    index=1,
    format_func=lambda x: {
        1: "편도 1회",
        2: "왕복 2회",
        3: "3회",
        4: "4회"
    }[x]
)

st.sidebar.subheader("주말 설정")

include_weekends = st.sidebar.checkbox(
    "주말 교통비 포함",
    value=False
)

weekend_trips = st.sidebar.selectbox(
    "주말 하루 이용 횟수",
    options=[1, 2, 3, 4],
    index=1,
    format_func=lambda x: {
        1: "편도 1회",
        2: "왕복 2회",
        3: "3회",
        4: "4회"
    }[x],
    disabled=not include_weekends
)

st.sidebar.subheader("공휴일 설정")

exclude_holidays = st.sidebar.checkbox(
    "평일 공휴일은 등교일에서 제외",
    value=True
)

budget = st.sidebar.number_input(
    "월간 교통비 예산 (원)",
    min_value=0,
    value=70000,
    step=5000
)

# -----------------------------
# 달력 분석 함수
# -----------------------------
kr_holidays = holidays.country_holidays(
    "KR",
    years=[int(year)]
)

monthly_records = []

for month in range(1, 13):
    days_in_month = calendar.monthrange(
        int(year), month
    )[1]

    weekdays = 0
    weekends = 0
    weekday_holidays = 0
    holiday_names = []

    for day in range(1, days_in_month + 1):
        current_date = date(int(year), month, day)
        holiday_name = kr_holidays.get(current_date)

        if current_date.weekday() < 5:
            # 월요일부터 금요일
            weekdays += 1

            if holiday_name:
                weekday_holidays += 1
                holiday_names.append(
                    f"{day}일 ({holiday_name})"
                )
        else:
            # 토요일과 일요일
            weekends += 1

    # 공휴일을 제외한 실제 평일 등교일 추정치
    if exclude_holidays:
        commute_weekdays = weekdays - weekday_holidays
    else:
        commute_weekdays = weekdays

    weekday_cost = (
        commute_weekdays * weekday_trips * fare
    )

    if include_weekends:
        weekend_cost = weekends * weekend_trips * fare
    else:
        weekend_cost = 0

    total_cost = weekday_cost + weekend_cost

    monthly_records.append({
        "월": f"{month}월",
        "평일 수": weekdays,
        "평일 공휴일 수": weekday_holidays,
        "주말 수": weekends,
        "평일 등교일 추정": commute_weekdays,
        "주말 포함": "포함" if include_weekends else "미포함",
        "평일 교통비": weekday_cost,
        "주말 교통비": weekend_cost,
        "월간 예상 교통비": total_cost,
        "공휴일": ", ".join(holiday_names) if holiday_names else "-"
    })

df = pd.DataFrame(monthly_records)

# -----------------------------
# 연간 요약
# -----------------------------
st.subheader(f"📅 {int(year)}년 통학 달력 분석")

total_weekdays = int(df["평일 수"].sum())
total_weekends = int(df["주말 수"].sum())
total_holidays = int(df["평일 공휴일 수"].sum())
total_commute_days = int(df["평일 등교일 추정"].sum())
annual_cost = int(df["월간 예상 교통비"].sum())

col1, col2, col3, col4 = st.columns(4)

col1.metric("연간 평일", f"{total_weekdays:,}일")
col2.metric("연간 주말", f"{total_weekends:,}일")
col3.metric("평일 공휴일", f"{total_holidays:,}일")
col4.metric("평일 등교일 추정", f"{total_commute_days:,}일")

st.divider()

# -----------------------------
# 월별 교통비
# -----------------------------
st.subheader("💰 월별 교통비 분석")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "연간 예상 교통비",
        f"{annual_cost:,}원"
    )

with col2:
    st.metric(
        "월평균 예상 교통비",
        f"{annual_cost / 12:,.0f}원"
    )

# -----------------------------
# 월별 비용 그래프
# -----------------------------
fig = px.bar(
    df,
    x="월",
    y="월간 예상 교통비",
    text="월간 예상 교통비",
    title="월별 예상 통학 교통비",
    labels={
        "월": "월",
        "월간 예상 교통비": "교통비 (원)"
    }
)

fig.update_traces(
    texttemplate="%{text:,}원",
    textposition="outside",
    cliponaxis=False
)

fig.update_layout(
    yaxis_rangemode="tozero",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 평일 및 주말 비용 비교
# -----------------------------
st.subheader("🗓️ 평일과 주말 비용 비교")

cost_df = df[
    ["월", "평일 교통비", "주말 교통비"]
].melt(
    id_vars="월",
    var_name="구분",
    value_name="교통비"
)

fig2 = px.bar(
    cost_df,
    x="월",
    y="교통비",
    color="구분",
    barmode="group",
    title="월별 평일·주말 교통비",
    labels={
        "월": "월",
        "교통비": "교통비 (원)",
        "구분": "구분"
    }
)

fig2.update_layout(yaxis_rangemode="tozero")

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# 월별 데이터 표
# -----------------------------
st.subheader("📊 월별 평일·주말 일수와 비용")

display_df = df[
    [
        "월",
        "평일 수",
        "평일 공휴일 수",
        "주말 수",
        "평일 등교일 추정",
        "주말 포함",
        "평일 교통비",
        "주말 교통비",
        "월간 예상 교통비"
    ]
].copy()

for column in [
    "평일 교통비",
    "주말 교통비",
    "월간 예상 교통비"
]:
    display_df[column] = display_df[column].map(
        lambda x: f"{x:,}원"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# 월별 공휴일 상세
# -----------------------------
with st.expander("공휴일 상세 확인"):
    holiday_df = df[["월", "공휴일"]].copy()
    st.dataframe(
        holiday_df,
        use_container_width=True,
        hide_index=True
    )

# -----------------------------
# 예산 분석
# -----------------------------
st.divider()
st.subheader("💳 월간 예산 분석")

df["예산 잔액"] = budget - df["월간 예상 교통비"]

over_budget = df[
    df["월간 예상 교통비"] > budget
]

if budget > 0:
    avg_monthly_cost = annual_cost / 12
    usage = avg_monthly_cost / budget * 100

    col1, col2 = st.columns(2)

    col1.metric(
        "월간 예산",
        f"{budget:,}원"
    )

    col2.metric(
        "평균 예산 사용률",
        f"{usage:.1f}%"
    )

    st.progress(min(usage / 100, 1.0))

    if not over_budget.empty:
        over_months = ", ".join(
            over_budget["월"].tolist()
        )
        st.warning(
            f"예산을 초과하는 달: {over_months}"
        )
    else:
        st.success(
            "모든 달의 예상 교통비가 월간 예산 이내입니다."
        )
else:
    st.info(
        "월간 예산을 0원보다 크게 설정하면 "
        "예산 분석을 확인할 수 있습니다."
    )

# -----------------------------
# CSV 다운로드
# -----------------------------
st.divider()
st.subheader("📥 결과 다운로드")

csv_data = df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="월별 교통비 분석 CSV 다운로드",
    data=csv_data,
    file_name=f"schoolmove_calendar_{int(year)}.csv",
    mime="text/csv"
)

st.caption(
    "주의: 평일 등교일 추정치는 월요일~금요일에서 "
    "선택한 공휴일을 제외해 계산합니다. "
    "학교 방학, 재량휴업일, 실제 출석일, 환승 할인 등은 "
    "자동 반영되지 않으므로 실제 지출과 차이가 날 수 있습니다."
)
