import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="지하역 동선 최적화 시뮬레이터", layout="wide")

@st.cache_data
def load_data():
    file_path = 'subway_all.csv'
    try:
        # cp949 인코딩으로 먼저 시도 (한국 공공데이터 표준)
        df = pd.read_csv(file_path, encoding='cp949', engine='python')
    except:
        df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        
    # 1. 컬럼명 앞뒤 공백 및 보이지 않는 문자 제거
    df.columns = df.columns.str.strip()
    
    # 2. 컬럼명 자동 매핑 (에러 방지 핵심!)
    # '호선명'이 없으면 '호선'이나 '노선'을 찾음
    col_mapping = {
        '역명': ['역명', '지하철역', '역이름'],
        '호선명': ['호선명', '호선', '노선명', '노선']
    }
    
    for standard_col, options in col_mapping.items():
        for opt in options:
            if opt in df.columns:
                df.rename(columns={opt: standard_col}, inplace=True)
                break
                
    return df

# 데이터 로드
df = load_data()

# 만약 데이터 로드 후에도 컬럼이 없으면 안내 출력
if '역명' not in df.columns or '호선명' not in df.columns:
    st.error("데이터 파일의 컬럼명을 확인해주세요. ('역명', '호선명' 컬럼이 필요합니다.)")
    st.write("현재 확인된 컬럼들:", df.columns.tolist())
    st.stop()

st.title("🚉 지하철 역 혼잡도 분석 및 동선 최적화 시스템")

# 사이드바 설정
st.sidebar.header("🕒 시뮬레이션 설정")

# 역 선택 (가나다 순 정렬)
station_list = sorted(df['역명'].unique())
station = st.sidebar.selectbox("역 선택", station_list)

# 해당 역에 존재하는 호선만 필터링해서 표시
line_list = sorted(df[df['역명'] == station]['호선명'].unique())
line = st.sidebar.selectbox("호선 선택", line_list)

# 최종 데이터 필터링
filtered = df[(df['역명'] == station) & (df['호선명'] == line)]

if filtered.empty:
    st.warning("선택한 역의 데이터를 찾을 수 없습니다.")
    st.stop()

# 수치 데이터 합계 (숫자형 컬럼만)
data_sum = filtered.select_dtypes(include=['number']).sum()

# 시간대 슬라이더
selected_hour = st.sidebar.slider("시뮬레이션 시간대 (시)", 4, 23, 8)

# 컬럼명 패턴 매칭 (데이터 형식에 따라 08시-09시 또는 8시-9시 대응)
def get_val(hour, type_str):
    # '08시-09시' 형식 시도
    col = f"{hour:02d}시-{hour+1:02d}시 {type_str}"
    if col in data_sum.index:
        return data_sum[col]
    # '8시-9시' 형식 시도
    col_alt = f"{hour}시-{hour+1}시 {type_str}"
    if col_alt in data_sum.index:
        return data_sum[col_alt]
    return 0

val_on = get_val(selected_hour, "승차인원")
val_off = get_val(selected_hour, "하차인원")
congestion = val_on + val_off

# 상단 지표
c1, c2, c3, c4 = st.columns(4)
c1.metric("현재 시간", f"{selected_hour:02d}:00")
c2.metric("승차 인원", f"{int(val_on):,} 명")
c3.metric("하차 인원", f"{int(val_off):,} 명")
c4.metric("총 혼잡도", f"{int(congestion):,}")

st.markdown("---")

# 메인 분석 영역
left_col, right_col = st.columns([1.5, 1])

with left_col:
    st.subheader("📍 역사 내 혼잡도 모니터링")
    fig = go.Figure()
    
    # 혼잡도 시각화용 사각형
    color_map = {"매우 혼잡": "rgba(255, 0, 0, 0.3)", "보통": "rgba(255, 165, 0, 0.3)", "원활": "rgba(0, 128, 0, 0.3)"}
    
    if congestion > 30000:
        status, status_color = "매우 혼잡", color_map["매우 혼잡"]
    elif congestion > 10000:
        status, status_color = "보통", color_map["보통"]
    else:
        status, status_color = "원활", color_map["원활"]
        
    fig.add_shape(type="rect", x0=1, y0=1, x1=9, y1=4, fillcolor=status_color, line_color="black")
    fig.add_annotation(x=5, y=2.5, text=f"{station}역 [{status}]", showarrow=False, font=dict(size=20))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("📢 시스템 권고")
    if congestion > 30000:
        st.error("🚨 인파 밀집 주의! 우회 동선을 안내하세요.")
    elif congestion > 10000:
        st.warning("⚠️ 승하차 동선을 분리하여 안내 중입니다.")
    else:
        st.success("✅ 현재 역사 내 이동이 원활합니다.")

# 하단 시간대별 트렌드
st.subheader(f"📈 {station}역 시간대별 유동인구 추이")
hours = range(4, 24)
trend_data = []
for h in hours:
    trend_data.append({
        "시간": f"{h:02d}시",
        "승차": get_val(h, "승차인원"),
        "하차": get_val(h, "하차인원")
    })
trend_df = pd.DataFrame(trend_data)

fig_line = px.line(trend_df, x="시간", y=["승차", "하차"], markers=True, template="plotly_white")
st.plotly_chart(fig_line, use_container_width=True)

# TOP 10 
st.markdown("---")
st.subheader("🚨 전체 역 혼잡도 TOP 10 (누적)")
df_top = df.groupby('역명').sum(numeric_only=True)
df_top['총합'] = df_top.filter(like='승차').sum(axis=1) + df_top.filter(like='하차').sum(axis=1)
top10 = df_top.sort_values('총합', ascending=False).head(10)
st.bar_chart(top10['총합'])
