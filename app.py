import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="지하역 동선 최적화 시뮬레이터", layout="wide")

@st.cache_data
def load_data():
    file_path = 'subway_all.csv'
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        df = pd.read_csv(file_path, encoding='cp949')
        
    df.columns = df.columns.str.strip()
    return df

df = load_data()

st.title("🚉 지하철 역 혼잡도 분석 및 동선 최적화 시스템")

# 사이드바 설정
st.sidebar.header("🕒 시뮬레이션 설정")
station = st.sidebar.selectbox("역 선택", sorted(df['역명'].unique()))
line = st.sidebar.selectbox("호선 선택", sorted(df[df['역명'] == station]['호선명'].unique()))

# 데이터 필터링 (해당 역/호선의 모든 행 합산)
filtered = df[(df['역명'] == station) & (df['호선명'] == line)]

if filtered.empty:
    st.error("선택한 역 데이터가 없습니다.")
    st.stop()

# 수치형 데이터만 합산하여 Series로 변환
data_sum = filtered.select_dtypes(include=['number']).sum()

selected_hour = st.sidebar.slider("시뮬레이션 시간대 (시)", 4, 23, 8)

# 컬럼명 매칭 (f-string 포맷 확인 필수)
col_on = f"{selected_hour:02d}시-{selected_hour+1:02d}시 승차인원"
col_off = f"{selected_hour:02d}시-{selected_hour+1:02d}시 하차인원"

# 컬럼 존재 여부 체크 (에러 방지)
if col_on not in data_sum.index or col_off not in data_sum.index:
    st.error(f"데이터 컬럼을 찾을 수 없습니다. (찾는 컬럼: {col_on})")
    st.info("CSV 파일의 컬럼명 형식이 '08시-09시 승차인원'인지 확인해주세요.")
    st.stop()

val_on = data_sum[col_on]
val_off = data_sum[col_off]
congestion = val_on + val_off

# 상단 지표 출력
c1, c2, c3, c4 = st.columns(4)
c1.metric("현재 시간", f"{selected_hour:02d}:00")
c2.metric("승차 인원", f"{int(val_on):,}")
c3.metric("하차 인원", f"{int(val_off):,}")
c4.metric("총 혼잡도", f"{int(congestion):,}")

st.markdown("---")

# 그래프 영역
left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.subheader("📍 역사 내 실시간 흐름 모니터링")
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=5, line_color="RoyalBlue", fillcolor="LightSkyBlue", opacity=0.2)
    
    # 혼잡도 기준 설정 (데이터 규모에 따라 조정 필요)
    if congestion > 50000:
        status_text = "매우 혼잡"
        color = "red"
    elif congestion > 20000:
        status_text = "보통"
        color = "orange"
    else:
        status_text = "원활"
        color = "green"

    fig.update_layout(title=f"{station}역 상태: {status_text}", height=400)
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("📢 시스템 권고 사항")
    if congestion > 50000:
        st.error("🚨 주요 출구 분산 안내 및 안전요원 배치 필요")
    elif congestion > 20000:
        st.warning("⚠️ 승하차 동선 분리 유도")
    else:
        st.success("✅ 현재 역사 내 이동 원활")

# 하단 트렌드
st.subheader(f"📈 {station}역 시간대별 패턴")
hours_range = range(4, 24)
on_trends = [data_sum.get(f"{i:02d}시-{i+1:02d}시 승차인원", 0) for i in hours_range]
off_trends = [data_sum.get(f"{i:02d}시-{i+1:02d}시 하차인원", 0) for i in hours_range]

trend_df = pd.DataFrame({'시간': [f"{i:02d}시" for i in hours_range], '승차': on_trends, '하차': off_trends})
st.plotly_chart(px.line(trend_df, x='시간', y=['승차', '하차'], markers=True), use_container_width=True)

# TOP 10 집계
st.markdown("---")
st.subheader("🚨 전체 역 혼잡도 TOP 10")
# 역별로 그룹화하여 합산
df_group = df.groupby('역명').sum(numeric_only=True)
df_group['총합'] = df_group.filter(like='승차').sum(axis=1) + df_group.filter(like='하차').sum(axis=1)
top10 = df_group.sort_values('총합', ascending=False).head(10)
st.bar_chart(top10['총합'])
