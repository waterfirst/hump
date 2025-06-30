"""
CSV 파일 분석 Streamlit 앱
여러 CSV 파일을 업로드하여 분석하고 그래프를 생성하는 앱
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import zipfile
from datetime import datetime
import re
import os

# Streamlit 환경 변수 설정 (파일 워처 비활성화)
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'false'

# 페이지 설정
st.set_page_config(
    page_title="CSV 파일 분석 도구",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Malgun Gothic', 'NanumGothic']
plt.rcParams['axes.unicode_minus'] = False

# 사이드바
st.sidebar.title("📊 CSV 분석 도구")
st.sidebar.markdown("---")

# 메인 페이지 선택
page = st.sidebar.selectbox(
    "페이지 선택",
    ["🔄 파일 업로드", "📈 데이터 분석", "💾 결과 다운로드"]
)

# 세션 상태 초기화
if 'df_combined' not in st.session_state:
    st.session_state.df_combined = None
if 'result_df' not in st.session_state:
    st.session_state.result_df = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'plots' not in st.session_state:
    st.session_state.plots = {}

def extract_cell_from_id(cell_id):
    """CELL ID에서 cell 정보 추출"""
    return str(cell_id)[-3:]

def extract_position_from_file(filename):
    """파일명에서 position 정보 추출"""
    # 파일명에서 마지막 13글자 중 첫 번째 글자 추출
    if len(filename) >= 13:
        return filename[-13]
    return "1"  # 기본값

def assign_split_category(cell):
    """cell에 따른 split 카테고리 할당"""
    if cell in ["A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10"]:
        return "Sp1"
    elif cell in ["A03", "C03", "A08", "C08"]:
        return "Sp2"
    elif cell in ["B03", "D03", "B08", "D08"]:
        return "Sp3"
    else:
        return "Unknown"

def position_to_side(position):
    """position을 side로 변환"""
    position_map = {
        "1": "Left",
        "2": "Right", 
        "3": "Top",
        "4": "Down"
    }
    return position_map.get(str(position), "Unknown")

def analyze_data(df_combined):
    """데이터 분석 수행"""
    try:
        # 기본 데이터 전처리
        df = df_combined.copy()
        df['cell'] = df['CELL ID'].apply(extract_cell_from_id)
        df['position'] = df['file'].apply(extract_position_from_file)
        df['x'] = df['no'] * 10.96
        df['side'] = df['position'].apply(position_to_side)
        
        # position이 "4"가 아닌 데이터 분석 (result1)
        df_not_4 = df[df['position'] != "4"].copy()
        
        if len(df_not_4) > 0:
            # pivot_wider 구현
            df_pivot = df_not_4.pivot_table(
                index='no',
                columns=['Glass ID', 'cell', 'position'],
                values='Avg Offset',
                aggfunc='first'
            )
            
            # 기준점(456번째 행) 차감
            if len(df_pivot) > 456:
                df_pivot = df_pivot.sub(df_pivot.iloc[455], axis=1)
            
            # pivot_longer 구현
            df_long = df_pivot.reset_index().melt(
                id_vars=['no'],
                var_name=['glass', 'cell', 'position'],
                value_name='y'
            )
            
            df_long['side'] = df_long['position'].apply(position_to_side)
            
            # hump 분석
            result1 = df_long.groupby(['glass', 'cell', 'side']).agg({
                'y': ['max', 'idxmax']
            }).round(1)
            
            result1.columns = ['hump_dy', 'hump_dx_idx']
            result1['hump_dx'] = (result1['hump_dx_idx'] * 10.96).round(0)
            result1 = result1.drop('hump_dx_idx', axis=1).reset_index()
            result1['split'] = result1['cell'].apply(assign_split_category)
        else:
            result1 = pd.DataFrame()
        
        # position이 "4"인 데이터 분석 (result2)
        df_4 = df[df['position'] == "4"].copy()
        
        if len(df_4) > 0:
            df_4 = df_4.rename(columns={'Glass ID': 'glass', 'Avg Offset': 'y'})
            
            result2 = df_4.groupby(['glass', 'cell', 'side']).agg({
                'y': lambda x: round(x.max() - x.min(), 1),
                'x': lambda x: round(10.96 * x.idxmax())
            })
            
            result2.columns = ['hump_dy', 'hump_dx']
            result2 = result2.reset_index()
            result2['split'] = result2['cell'].apply(assign_split_category)
        else:
            result2 = pd.DataFrame()
        
        # 결과 합치기
        if len(result1) > 0 and len(result2) > 0:
            result = pd.concat([result1, result2], ignore_index=True)
        elif len(result1) > 0:
            result = result1
        elif len(result2) > 0:
            result = result2
        else:
            result = pd.DataFrame()
        
        if len(result) > 0:
            result = result.sort_values(['glass', 'cell', 'side']).reset_index(drop=True)
        
        return result, df
        
    except Exception as e:
        st.error(f"데이터 분석 중 오류가 발생했습니다: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def create_plots(df, result_df):
    """그래프 생성"""
    plots = {}
    
    try:
        # 1. 전체 데이터 시각화
        fig1 = px.scatter(
            df, 
            x='x', 
            y='Avg Offset',
            color='side',
            facet_col='cell',
            facet_row='Glass ID',
            title="전체 데이터 시각화",
            labels={'x': 'X [um]', 'Avg Offset': 'Avg Offset [um]'}
        )
        fig1.update_layout(height=600)
        plots['main_plot'] = fig1
        
        # 2. 위치별 평균 프로파일
        df_avg = df.groupby(['side', 'x'])['Avg Offset'].mean().reset_index()
        df_avg['y_normalized'] = df_avg.groupby('side')['Avg Offset'].transform(lambda x: x - x.min())
        
        fig2 = px.line(
            df_avg,
            x='x',
            y='y_normalized',
            color='side',
            title="위치별 SIP 잉크젯 Edge Profile",
            labels={'x': 'x[um]', 'y_normalized': 'SIP_height [um]'}
        )
        plots['profile_plot'] = fig2
        
        # 3. Hump Height vs Position
        if len(result_df) > 0:
            result_filtered = result_df[result_df['side'] != 'Down']
            
            fig3 = px.bar(
                result_filtered,
                x='side',
                y='hump_dy',
                color='side',
                facet_col='cell',
                facet_row='glass',
                title="Hump Height vs Position of Panel",
                labels={'hump_dy': 'Hump DY [um]', 'side': 'Side'}
            )
            fig3.update_layout(height=600)
            plots['hump_plot'] = fig3
        
        return plots
        
    except Exception as e:
        st.error(f"그래프 생성 중 오류가 발생했습니다: {str(e)}")
        return {}

# 페이지별 내용
if page == "🔄 파일 업로드":
    st.title("📁 CSV 파일 업로드")
    st.markdown("---")
    
    # 파일 업로드
    uploaded_files = st.file_uploader(
        "CSV 파일을 선택하세요 (여러 파일 선택 가능)",
        type=['csv'],
        accept_multiple_files=True,
        help="Ctrl+클릭으로 여러 파일을 동시에 선택할 수 있습니다."
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)}개의 파일이 업로드되었습니다!")
        
        # 업로드된 파일 정보 표시
        file_info = []
        for file in uploaded_files:
            file_info.append({
                "파일명": file.name,
                "크기": f"{file.size / 1024:.2f} KB",
                "타입": file.type
            })
        
        st.subheader("📋 업로드된 파일 목록")
        st.dataframe(pd.DataFrame(file_info), use_container_width=True)
        
        # 데이터 읽기 및 합치기
        if st.button("🔄 데이터 로드", type="primary"):
            with st.spinner("데이터를 로딩 중입니다..."):
                try:
                    dataframes = []
                    for file in uploaded_files:
                        df = pd.read_csv(file)
                        df['file'] = file.name
                        dataframes.append(df)
                    
                    combined_df = pd.concat(dataframes, ignore_index=True)
                    st.session_state.df_combined = combined_df
                    st.session_state.analysis_complete = False
                    
                    st.success("✅ 데이터가 성공적으로 로드되었습니다!")
                    st.info(f"총 {len(combined_df):,}개의 데이터 포인트가 로드되었습니다.")
                    
                    # 데이터 미리보기
                    st.subheader("📊 데이터 미리보기")
                    st.dataframe(combined_df.head(10), use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ 데이터 로딩 중 오류가 발생했습니다: {str(e)}")
    
    else:
        st.info("🔍 CSV 파일을 업로드해주세요.")

elif page == "📈 데이터 분석":
    st.title("📈 데이터 분석 및 시각화")
    st.markdown("---")
    
    if st.session_state.df_combined is None:
        st.warning("⚠️ 먼저 CSV 파일을 업로드해주세요.")
        st.info("👈 사이드바에서 '파일 업로드' 페이지로 이동하여 파일을 업로드하세요.")
    else:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🚀 분석 시작", type="primary", use_container_width=True):
                with st.spinner("데이터를 분석 중입니다..."):
                    result_df, processed_df = analyze_data(st.session_state.df_combined)
                    
                    if len(result_df) > 0:
                        st.session_state.result_df = result_df
                        st.session_state.processed_df = processed_df
                        st.session_state.analysis_complete = True
                        
                        # 그래프 생성
                        plots = create_plots(processed_df, result_df)
                        st.session_state.plots = plots
                        
                        st.success("✅ 분석이 완료되었습니다!")
                    else:
                        st.error("❌ 분석 결과가 없습니다. 데이터를 확인해주세요.")
        
        with col2:
            if st.session_state.analysis_complete:
                st.success("✅ 분석 완료")
                st.info(f"📊 결과 데이터: {len(st.session_state.result_df)}개 행")
            else:
                st.info("⏳ 분석 대기 중")
        
        # 분석 결과 표시
        if st.session_state.analysis_complete and st.session_state.result_df is not None:
            st.markdown("---")
            
            # 결과 데이터 테이블
            st.subheader("📋 분석 결과 데이터")
            st.dataframe(st.session_state.result_df, use_container_width=True)
            
            st.markdown("---")
            
            # 그래프들
            if st.session_state.plots:
                # 전체 데이터 시각화
                if 'main_plot' in st.session_state.plots:
                    st.subheader("📊 전체 데이터 시각화")
                    st.plotly_chart(st.session_state.plots['main_plot'], use_container_width=True)
                
                # 프로파일과 Hump 그래프를 나란히 배치
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'profile_plot' in st.session_state.plots:
                        st.subheader("📈 위치별 SIP Profile")
                        st.plotly_chart(st.session_state.plots['profile_plot'], use_container_width=True)
                
                with col2:
                    if 'hump_plot' in st.session_state.plots:
                        st.subheader("📊 Hump Height vs Position")
                        st.plotly_chart(st.session_state.plots['hump_plot'], use_container_width=True)

elif page == "💾 결과 다운로드":
    st.title("💾 결과 다운로드")
    st.markdown("---")
    
    if not st.session_state.analysis_complete:
        st.warning("⚠️ 먼저 데이터 분석을 완료해주세요.")
        st.info("👈 사이드바에서 '데이터 분석' 페이지로 이동하여 분석을 실행하세요.")
    else:
        st.success("✅ 분석이 완료되어 다운로드가 가능합니다!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 CSV 결과 다운로드")
            
            if st.session_state.result_df is not None:
                csv_buffer = io.StringIO()
                st.session_state.result_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 CSV 파일 다운로드",
                    data=csv_data,
                    file_name=f"analysis_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.info(f"📋 데이터: {len(st.session_state.result_df)}개 행")
        
        with col2:
            st.subheader("🖼️ 그래프 다운로드")
            
            if st.session_state.plots:
                # HTML로 그래프 저장
                html_buffer = io.StringIO()
                
                for plot_name, plot in st.session_state.plots.items():
                    html_buffer.write(f"<h2>{plot_name}</h2>\n")
                    html_buffer.write(plot.to_html(include_plotlyjs='cdn'))
                    html_buffer.write("<br><br>\n")
                
                html_data = html_buffer.getvalue()
                
                st.download_button(
                    label="📥 그래프 HTML 다운로드",
                    data=html_data,
                    file_name=f"analysis_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
                
                st.info(f"📊 그래프: {len(st.session_state.plots)}개")
        
        # 전체 결과 ZIP 다운로드
        st.markdown("---")
        st.subheader("📦 전체 결과 패키지 다운로드")
        
        if st.button("📦 ZIP 파일로 모든 결과 다운로드", use_container_width=True):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # CSV 결과 추가
                if st.session_state.result_df is not None:
                    csv_buffer = io.StringIO()
                    st.session_state.result_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    zip_file.writestr("analysis_result.csv", csv_buffer.getvalue())
                
                # HTML 그래프 추가
                if st.session_state.plots:
                    html_buffer = io.StringIO()
                    for plot_name, plot in st.session_state.plots.items():
                        html_buffer.write(f"<h2>{plot_name}</h2>\n")
                        html_buffer.write(plot.to_html(include_plotlyjs='cdn'))
                        html_buffer.write("<br><br>\n")
                    zip_file.writestr("analysis_plots.html", html_buffer.getvalue())
            
            zip_data = zip_buffer.getvalue()
            
            st.download_button(
                label="📥 ZIP 파일 다운로드",
                data=zip_data,
                file_name=f"analysis_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )

# 사이드바 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ 앱 정보")
st.sidebar.info("""
📊 **CSV 분석 도구**

🔸 여러 CSV 파일 업로드
🔸 자동 데이터 분석  
🔸 인터랙티브 시각화
🔸 결과 다운로드

💡 **사용법:**
1. CSV 파일들을 업로드
2. 데이터 분석 실행
3. 결과 확인 및 다운로드
""")

# 하단 정보
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🔬 CSV 데이터 분석 도구 | Made with Streamlit 📊"
    "</div>", 
    unsafe_allow_html=True
)