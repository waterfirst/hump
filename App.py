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
        # 데이터 구조 확인
        st.info("📋 데이터 구조 확인 중...")
        st.write("컬럼명:", df_combined.columns.tolist())
        st.write("데이터 형태:", df_combined.shape)
        st.write("첫 5행 미리보기:")
        st.dataframe(df_combined.head())
        
        # 기본 데이터 전처리
        df = df_combined.copy()
        
        # 'no' 컬럼 확인 및 생성
        if 'no' not in df.columns:
            if 'No' in df.columns:
                df['no'] = df['No']
            elif 'NO' in df.columns:
                df['no'] = df['NO']
            elif 'index' in df.columns:
                df['no'] = df['index']
            elif 'Index' in df.columns:
                df['no'] = df['Index']
            else:
                # 인덱스를 'no' 컬럼으로 사용
                df['no'] = df.index + 1
                st.warning("⚠️ 'no' 컬럼을 찾을 수 없어서 인덱스를 사용합니다.")
        
        # 필수 컬럼 확인
        required_cols = ['CELL ID', 'Avg Offset', 'Glass ID']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            # 대안 컬럼명 확인
            col_mapping = {}
            for col in missing_cols:
                if col == 'CELL ID':
                    alternatives = ['Cell ID', 'cell_id', 'cellid', 'Cell_ID', 'CellID']
                elif col == 'Avg Offset':
                    alternatives = ['avg_offset', 'AvgOffset', 'Average Offset', 'Offset']
                elif col == 'Glass ID':
                    alternatives = ['Glass_ID', 'glass_id', 'glassid', 'GlassID', 'glass']
                
                for alt in alternatives:
                    if alt in df.columns:
                        col_mapping[col] = alt
                        break
            
            # 컬럼명 변경
            for original, alternative in col_mapping.items():
                df[original] = df[alternative]
                st.info(f"✅ '{alternative}' 컬럼을 '{original}'로 매핑했습니다.")
            
            # 여전히 없는 컬럼 확인
            still_missing = [col for col in required_cols if col not in df.columns]
            if still_missing:
                st.error(f"❌ 다음 필수 컬럼을 찾을 수 없습니다: {still_missing}")
                st.error("사용 가능한 컬럼:", df.columns.tolist())
                return pd.DataFrame(), pd.DataFrame()
        
        # 데이터 전처리 계속
        df['cell'] = df['CELL ID'].apply(extract_cell_from_id)
        df['position'] = df['file'].apply(extract_position_from_file)
        df['x'] = df['no'] * 10.96
        df['side'] = df['position'].apply(position_to_side)
        
        # position이 "4"가 아닌 데이터 분석 (result1)
        df_not_4 = df[df['position'] != "4"].copy()
        
        if len(df_not_4) > 0:
            st.info("📊 Position 1-3 데이터 분석 중...")
            
            # pivot_wider 구현
            try:
                df_pivot = df_not_4.pivot_table(
                    index='no',
                    columns=['Glass ID', 'cell', 'position'],
                    values='Avg Offset',
                    aggfunc='first'
                )
                
                st.success(f"✅ Pivot 테이블 생성 완료: {df_pivot.shape}")
                
                # 기준점 차감 (456번째 행이 있는 경우)
                reference_row = min(455, len(df_pivot) - 1)  # 안전한 인덱스 사용
                if reference_row >= 0:
                    df_pivot = df_pivot.sub(df_pivot.iloc[reference_row], axis=1)
                    st.info(f"✅ 기준점({reference_row + 1}번째 행) 차감 완료")
                
                # pivot_longer 구현 - 더 안전한 방법 사용
                df_pivot_reset = df_pivot.reset_index()
                
                # 컬럼을 수동으로 melt
                value_columns = [col for col in df_pivot_reset.columns if col != 'no']
                
                df_long_list = []
                for col in value_columns:
                    if isinstance(col, tuple) and len(col) == 3:  # (glass, cell, position)
                        glass, cell, position = col
                        temp_df = pd.DataFrame({
                            'no': df_pivot_reset['no'],
                            'glass': glass,
                            'cell': cell,
                            'position': position,
                            'y': df_pivot_reset[col]
                        })
                        df_long_list.append(temp_df)
                
                if df_long_list:
                    df_long = pd.concat(df_long_list, ignore_index=True)
                    df_long = df_long.dropna()  # NaN 값 제거
                else:
                    st.error("❌ 데이터 변환 실패")
                    df_long = pd.DataFrame()
                
            except Exception as e:
                st.error(f"❌ Pivot 처리 중 오류: {str(e)}")
                df_long = pd.DataFrame()
            if len(df_long) > 0:
                df_long['side'] = df_long['position'].apply(position_to_side)
                
                # hump 분석 - 더 안전한 방법
                try:
                    result1_list = []
                    
                    for (glass, cell, side), group in df_long.groupby(['glass', 'cell', 'side']):
                        if len(group) > 0 and not group['y'].isna().all():
                            max_y = group['y'].max()
                            max_idx = group['y'].idxmax()
                            max_x_position = group.loc[max_idx, 'no'] if max_idx in group.index else 0
                            
                            result1_list.append({
                                'glass': glass,
                                'cell': cell,
                                'side': side,
                                'hump_dy': round(max_y, 1),
                                'hump_dx': round(10.96 * max_x_position, 0)
                            })
                    
                    if result1_list:
                        result1 = pd.DataFrame(result1_list)
                        result1['split'] = result1['cell'].apply(assign_split_category)
                        st.success(f"✅ Position 1-3 분석 완료: {len(result1)}개 결과")
                    else:
                        result1 = pd.DataFrame()
                        st.warning("⚠️ Position 1-3 분석 결과가 없습니다.")
                        
                except Exception as e:
                    st.error(f"❌ Hump 분석 중 오류: {str(e)}")
                    result1 = pd.DataFrame()
            else:
                result1 = pd.DataFrame()
                st.warning("⚠️ Position 1-3 데이터 변환 결과가 없습니다.")
        else:
            result1 = pd.DataFrame()
            st.info("ℹ️ Position 1-3 데이터가 없습니다.")
        
        # position이 "4"인 데이터 분석 (result2)
        df_4 = df[df['position'] == "4"].copy()
        
        if len(df_4) > 0:
            st.info("📊 Position 4 데이터 분석 중...")
            
            try:
                df_4 = df_4.rename(columns={'Glass ID': 'glass', 'Avg Offset': 'y'})
                
                result2_list = []
                
                for (glass, cell, side), group in df_4.groupby(['glass', 'cell', 'side']):
                    if len(group) > 0 and not group['y'].isna().all():
                        max_y = group['y'].max()
                        min_y = group['y'].min()
                        max_idx = group['y'].idxmax()
                        max_x_position = group.loc[max_idx, 'x'] if max_idx in group.index else 0
                        
                        result2_list.append({
                            'glass': glass,
                            'cell': cell,
                            'side': side,
                            'hump_dy': round(max_y - min_y, 1),
                            'hump_dx': round(max_x_position, 0)
                        })
                
                if result2_list:
                    result2 = pd.DataFrame(result2_list)
                    result2['split'] = result2['cell'].apply(assign_split_category)
                    st.success(f"✅ Position 4 분석 완료: {len(result2)}개 결과")
                else:
                    result2 = pd.DataFrame()
                    st.warning("⚠️ Position 4 분석 결과가 없습니다.")
                    
            except Exception as e:
                st.error(f"❌ Position 4 분석 중 오류: {str(e)}")
                result2 = pd.DataFrame()
        else:
            result2 = pd.DataFrame()
            st.info("ℹ️ Position 4 데이터가 없습니다.")
        
        # 결과 합치기
        if len(result1) > 0 and len(result2) > 0:
            result = pd.concat([result1, result2], ignore_index=True)
            st.success("✅ 모든 분석 결과 합치기 완료")
        elif len(result1) > 0:
            result = result1
            st.info("ℹ️ Position 1-3 결과만 사용")
        elif len(result2) > 0:
            result = result2
            st.info("ℹ️ Position 4 결과만 사용")
        else:
            result = pd.DataFrame()
            st.error("❌ 분석 결과가 없습니다.")
        
        if len(result) > 0:
            result = result.sort_values(['glass', 'cell', 'side']).reset_index(drop=True)
            st.success(f"🎉 최종 분석 완료! 총 {len(result)}개의 결과가 생성되었습니다.")
        
        return result, df
        
    except Exception as e:
        st.error(f"❌ 데이터 분석 중 전체 오류가 발생했습니다: {str(e)}")
        st.error("디버그 정보:")
        st.write("DataFrame 컬럼:", df_combined.columns.tolist() if df_combined is not None else "None")
        st.write("DataFrame 크기:", df_combined.shape if df_combined is not None else "None")
        return pd.DataFrame(), pd.DataFrame()

def create_plots(df, result_df):
    """그래프 생성"""
    plots = {}
    
    try:
        # 필수 컬럼 확인
        required_plot_cols = ['x', 'Avg Offset', 'side', 'cell', 'Glass ID']
        missing_cols = [col for col in required_plot_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ 그래프 생성에 필요한 컬럼이 없습니다: {missing_cols}")
            return plots
        
        if len(df) == 0:
            st.warning("⚠️ 그래프를 생성할 데이터가 없습니다.")
            return plots
        
        # Plotly 기본 템플릿 설정 (색상 보존을 위해)
        import plotly.io as pio
        pio.templates.default = "plotly"
        
        # 커스텀 색상 팔레트 정의
        color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            '#bcbd22', '#17becf'
        ]
            
        # 1. 전체 데이터 시각화
        try:
            fig1 = px.scatter(
                df, 
                x='x', 
                y='Avg Offset',
                color='side',
                facet_col='cell',
                facet_row='Glass ID',
                title="전체 데이터 시각화",
                labels={'x': 'X [um]', 'Avg Offset': 'Avg Offset [um]'},
                color_discrete_sequence=color_palette
            )
            fig1.update_layout(
                height=600,
                template='plotly',
                font=dict(size=12),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            # 마커 크기 및 투명도 설정
            fig1.update_traces(marker=dict(size=4, opacity=0.7))
            plots['main_plot'] = fig1
            st.success("✅ 전체 데이터 그래프 생성 완료")
        except Exception as e:
            st.error(f"❌ 전체 데이터 그래프 생성 실패: {str(e)}")
        
        # 2. 위치별 평균 프로파일
        try:
            df_avg = df.groupby(['side', 'x'])['Avg Offset'].mean().reset_index()
            if len(df_avg) > 0:
                df_avg['y_normalized'] = df_avg.groupby('side')['Avg Offset'].transform(lambda x: x - x.min())
                
                fig2 = px.line(
                    df_avg,
                    x='x',
                    y='y_normalized',
                    color='side',
                    title="위치별 SIP 잉크젯 Edge Profile",
                    labels={'x': 'x[um]', 'y_normalized': 'SIP_height [um]'},
                    color_discrete_sequence=color_palette
                )
                fig2.update_layout(
                    template='plotly',
                    font=dict(size=12),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                # 라인 스타일 설정
                fig2.update_traces(line=dict(width=3), marker=dict(size=6))
                plots['profile_plot'] = fig2
                st.success("✅ 프로파일 그래프 생성 완료")
            else:
                st.warning("⚠️ 프로파일 그래프용 데이터가 없습니다.")
        except Exception as e:
            st.error(f"❌ 프로파일 그래프 생성 실패: {str(e)}")
        
        # 3. Hump Height vs Position
        try:
            if len(result_df) > 0 and 'side' in result_df.columns and 'hump_dy' in result_df.columns:
                result_filtered = result_df[result_df['side'] != 'Down']
                
                if len(result_filtered) > 0:
                    fig3 = px.bar(
                        result_filtered,
                        x='side',
                        y='hump_dy',
                        color='side',
                        facet_col='cell',
                        facet_row='glass',
                        title="Hump Height vs Position of Panel",
                        labels={'hump_dy': 'Hump DY [um]', 'side': 'Side'},
                        color_discrete_sequence=color_palette
                    )
                    fig3.update_layout(
                        height=600,
                        template='plotly',
                        font=dict(size=12),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    # 바 차트 스타일 설정
                    fig3.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='white')))
                    plots['hump_plot'] = fig3
                    st.success("✅ Hump 분석 그래프 생성 완료")
                else:
                    st.warning("⚠️ Hump 그래프용 필터링된 데이터가 없습니다.")
            else:
                st.warning("⚠️ Hump 그래프를 생성할 결과 데이터가 없습니다.")
        except Exception as e:
            st.error(f"❌ Hump 그래프 생성 실패: {str(e)}")
        
        return plots
        
    except Exception as e:
        st.error(f"❌ 그래프 생성 중 전체 오류가 발생했습니다: {str(e)}")
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
                    
                    # 데이터 상태 표시
                    st.info(f"📊 분석 대상: {len(st.session_state.df_combined):,}개 데이터 포인트")
                    
                    result_df, processed_df = analyze_data(st.session_state.df_combined)
                    
                    if len(result_df) > 0:
                        st.session_state.result_df = result_df
                        st.session_state.processed_df = processed_df
                        st.session_state.analysis_complete = True
                        
                        # 그래프 생성
                        with st.spinner("그래프를 생성 중입니다..."):
                            plots = create_plots(processed_df, result_df)
                            st.session_state.plots = plots
                        
                        st.success("✅ 분석이 완료되었습니다!")
                        st.balloons()  # 성공 애니메이션
                    else:
                        st.error("❌ 분석 결과가 없습니다. 데이터 형식을 확인해주세요.")
                        st.info("💡 CSV 파일에 다음 컬럼들이 있는지 확인해주세요:")
                        st.write("- CELL ID (또는 Cell ID, cell_id 등)")
                        st.write("- Avg Offset (또는 avg_offset, AvgOffset 등)")
                        st.write("- Glass ID (또는 Glass_ID, glass_id 등)")
                        st.write("- no (또는 No, index 등의 순번 컬럼)")
        
        with col2:
            if st.session_state.analysis_complete:
                st.success("✅ 분석 완료")
                st.metric("📊 결과 데이터", f"{len(st.session_state.result_df)}개 행")
                st.metric("📈 생성된 그래프", f"{len(st.session_state.plots)}개")
            else:
                st.info("⏳ 분석 대기 중")
                if st.session_state.df_combined is not None:
                    st.metric("📂 로드된 데이터", f"{len(st.session_state.df_combined):,}개 행")
        
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
                # HTML로 그래프 저장 - 색상 보존
                def create_html_with_plots():
                    """색상이 보존된 HTML 생성"""
                    html_content = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>CSV 분석 결과 그래프</title>
                        <meta charset="utf-8">
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <style>
                            body {
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                margin: 20px;
                                background-color: #f8f9fa;
                            }
                            .container {
                                max-width: 1200px;
                                margin: 0 auto;
                                background-color: white;
                                padding: 20px;
                                border-radius: 10px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            }
                            h1 {
                                color: #2c3e50;
                                text-align: center;
                                margin-bottom: 30px;
                            }
                            h2 {
                                color: #34495e;
                                border-bottom: 2px solid #3498db;
                                padding-bottom: 10px;
                                margin-top: 40px;
                            }
                            .plot-container {
                                margin: 20px 0;
                                border: 1px solid #ddd;
                                border-radius: 5px;
                                padding: 10px;
                            }
                            .timestamp {
                                text-align: center;
                                color: #7f8c8d;
                                font-style: italic;
                                margin-top: 30px;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>📊 CSV 파일 분석 결과</h1>
                    """
                    
                    plot_titles = {
                        'main_plot': '📈 전체 데이터 시각화',
                        'profile_plot': '📉 위치별 SIP 잉크젯 Edge Profile', 
                        'hump_plot': '📊 Hump Height vs Position 분석'
                    }
                    
                    for plot_name, plot in st.session_state.plots.items():
                        title = plot_titles.get(plot_name, plot_name)
                        html_content += f'<h2>{title}</h2>\n'
                        html_content += '<div class="plot-container">\n'
                        
                        # Plotly 그래프를 HTML로 변환 (색상 보존 설정)
                        plot_html = plot.to_html(
                            include_plotlyjs=False,  # 이미 스크립트가 포함되어 있음
                            div_id=f"plot_{plot_name}",
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': f'plot_{plot_name}',
                                    'height': 500,
                                    'width': 700,
                                    'scale': 1
                                }
                            }
                        )
                        
                        # HTML에서 div 부분만 추출
                        import re
                        div_match = re.search(r'<div[^>]*>.*?</div>', plot_html, re.DOTALL)
                        if div_match:
                            html_content += div_match.group(0)
                        else:
                            html_content += plot_html
                        
                        html_content += '</div>\n<br>\n'
                    
                    # HTML 마무리
                    timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')
                    html_content += f"""
                            <div class="timestamp">
                                생성 일시: {timestamp}
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    return html_content
                
                try:
                    html_data = create_html_with_plots()
                    
                    st.download_button(
                        label="📥 그래프 HTML 다운로드",
                        data=html_data,
                        file_name=f"analysis_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    st.info(f"📊 그래프: {len(st.session_state.plots)}개")
                    st.success("✅ 색상이 보존된 HTML 파일로 다운로드됩니다!")
                    
                except Exception as e:
                    st.error(f"❌ HTML 생성 중 오류: {str(e)}")
                    # 폴백: 기본 방식으로 HTML 생성
                    html_buffer = io.StringIO()
                    html_buffer.write("<html><head><title>분석 결과</title></head><body>")
                    
                    for plot_name, plot in st.session_state.plots.items():
                        html_buffer.write(f"<h2>{plot_name}</h2>\n")
                        html_buffer.write(plot.to_html(include_plotlyjs='cdn'))
                        html_buffer.write("<br><br>\n")
                    
                    html_buffer.write("</body></html>")
                    html_data = html_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 그래프 HTML 다운로드 (기본)",
                        data=html_data,
                        file_name=f"analysis_plots_basic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ 다운로드할 그래프가 없습니다.")
        
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