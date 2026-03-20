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

    st.write("데이터 로딩 완료")
    return df

# 🔥 여기부터 함수 밖
df = load_data()

st.title("🚉 지하철 역 혼잡도 분석 및 동선 최적화 시스템")
st.info("데이터 분석 결과에 따른 시간대별 최적 동선 가이드를 제공합니다.")

# 사이드바
st.sidebar.header("🕒 시뮬레이션 설정")

station = st.sidebar.selectbox("역 선택", df['지하철역'].unique())
line = st.sidebar.selectbox("호선 선택", df['호선명'].unique())

filtered = df[(df['지하철역'] == station) & (df['호선명'] == line)]

if filtered.empty:
    st.error("선택한 역 데이터가 없습니다.")
    st.stop()

# 🔥 여러 행이면 합계 처리
data = filtered.sum(numeric_only=True)

selected_hour = st.sidebar.slider("시뮬레이션 시간대 (시)", 4, 23, 8)

col_on = f"{selected_hour:02d}시-{selected_hour+1:02d}시 승차인원"
col_off = f"{selected_hour:02d}시-{selected_hour+1:02d}시 하차인원"

if col_on not in data or col_off not in data:
    st.error("해당 시간대 데이터가 없습니다.")
    st.stop()

val_on = data[col_on]
val_off = data[col_off]

# 상단 지표
c1, c2, c3 = st.columns(3)
c1.metric("현재 시간", f"{selected_hour:02d}:00")
c2.metric("승차 인원", f"{val_on:,} 명", delta_color="normal")
c3.metric("하차 인원", f"{val_off:,} 명", delta_color="inverse")
congestion = val_on + val_off

c4 = st.columns(1)[0]
c4.metric("혼잡도", f"{congestion:,}")

st.markdown("---")

# 메인 시뮬레이션 영역
left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.subheader("📍 역사 내 실시간 흐름 모니터링")
    
    fig = go.Figure()
    
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=10, y1=5,
        line_color="RoyalBlue",
        fillcolor="LightSkyBlue",
        opacity=0.2
    )
    
    if congestion > 50000:
        status_text = f"{station}역 혼잡도 매우 높음 (집중 관리 필요)"
        fig.add_annotation(x=5, y=5.5, text="혼잡 구간 집중 관리", showarrow=True)

    elif congestion > 30000:
        status_text = f"{station}역 혼잡도 높음 (분산 유도 필요)"
        fig.add_annotation(x=5, y=5.5, text="우회 동선 권장", showarrow=True)

    else:
        status_text = f"{station}역 원활 상태"

    fig.update_layout(
        title=status_text,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

# ✅ 여기 중요 (같은 레벨)
with right_col:
    st.subheader("📢 시스템 권고 사항")

    if congestion > 50000:
        st.error(f"[{station}역 혼잡도 매우 높음] 현재 이용객 {congestion:,}명")
        st.markdown("""
        - 주요 출구 분산 안내
        - 안전요원 배치 확대
        - 인근 역 우회 유도
        """)

    elif congestion > 30000:
        st.warning(f"[{station}역 혼잡도 높음] 현재 이용객 {congestion:,}명")
        st.markdown("""
        - 승하차 동선 분리
        - 안내 방송 강화
        - 출입구 분산 유도
        """)

    else:
        st.success(f"[{station}역 원활]")
    # 하단 전체 트렌드 그래프
st.subheader(f"📈 {station}역 시간대별 승하차 패턴")

hours = [f"{i:02d}시" for i in range(4, 24)]
on_trends = [data[f"{i:02d}시-{i+1:02d}시 승차인원"] for i in range(4, 24)]
off_trends = [data[f"{i:02d}시-{i+1:02d}시 하차인원"] for i in range(4, 24)]

trend_df = pd.DataFrame({
    '시간': hours,
    '승차': on_trends,
    '하차': off_trends
})

fig_line = px.line(
    trend_df,
    x='시간',
    y=['승차', '하차'],
    markers=True,
    title="시간대별 인원 추이"
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")
st.subheader("🚨 전체 역 혼잡도 TOP 10")

df['총합'] = df.filter(like='승차').sum(axis=1) + df.filter(like='하차').sum(axis=1)

top10 = df.sort_values('총합', ascending=False).head(10)

st.bar_chart(top10.set_index('지하철역')['총합'])
