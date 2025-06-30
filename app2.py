"""
Jupyter Notebook용 CSV 파일 분석 도구
Streamlit 대신 Jupyter에서 위젯으로 실행
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ipywidgets as widgets
from IPython.display import display, HTML
import io
import zipfile
from datetime import datetime
import re
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Malgun Gothic', 'NanumGothic']
plt.rcParams['axes.unicode_minus'] = False

class CSVAnalyzer:
    def __init__(self):
        self.df_combined = None
        self.result_df = None
        self.processed_df = None
        self.plots = {}
        
        # 위젯 생성
        self.create_widgets()
        self.display_interface()
    
    def create_widgets(self):
        """위젯 생성"""
        # 파일 업로드 위젯
        self.file_upload = widgets.FileUpload(
            accept='.csv',
            multiple=True,
            description='CSV 파일 선택'
        )
        
        # 버튼들
        self.load_button = widgets.Button(
            description='📂 데이터 로드',
            button_style='primary',
            layout=widgets.Layout(width='150px')
        )
        
        self.analyze_button = widgets.Button(
            description='🚀 분석 시작',
            button_style='success',
            layout=widgets.Layout(width='150px')
        )
        
        self.download_button = widgets.Button(
            description='💾 결과 저장',
            button_style='info',
            layout=widgets.Layout(width='150px')
        )
        
        # 출력 위젯들
        self.output_status = widgets.Output()
        self.output_data = widgets.Output()
        self.output_plots = widgets.Output()
        
        # 이벤트 핸들러 연결
        self.load_button.on_click(self.load_data)
        self.analyze_button.on_click(self.analyze_data)
        self.download_button.on_click(self.save_results)
    
    def display_interface(self):
        """인터페이스 표시"""
        print("📊 CSV 파일 분석 도구")
        print("=" * 50)
        
        # 파일 업로드 섹션
        upload_box = widgets.VBox([
            widgets.HTML("<h3>📁 파일 업로드</h3>"),
            self.file_upload,
            self.load_button
        ])
        
        # 컨트롤 섹션
        control_box = widgets.HBox([
            self.analyze_button,
            self.download_button
        ])
        
        # 전체 레이아웃
        main_layout = widgets.VBox([
            upload_box,
            control_box,
            self.output_status,
            self.output_data,
            self.output_plots
        ])
        
        display(main_layout)
    
    def extract_cell_from_id(self, cell_id):
        """CELL ID에서 cell 정보 추출"""
        return str(cell_id)[-3:]
    
    def extract_position_from_file(self, filename):
        """파일명에서 position 정보 추출"""
        if len(filename) >= 13:
            return filename[-13]
        return "1"
    
    def assign_split_category(self, cell):
        """cell에 따른 split 카테고리 할당"""
        if cell in ["A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10"]:
            return "Sp1"
        elif cell in ["A03", "C03", "A08", "C08"]:
            return "Sp2"
        elif cell in ["B03", "D03", "B08", "D08"]:
            return "Sp3"
        else:
            return "Unknown"
    
    def position_to_side(self, position):
        """position을 side로 변환"""
        position_map = {
            "1": "Left",
            "2": "Right", 
            "3": "Top",
            "4": "Down"
        }
        return position_map.get(str(position), "Unknown")
    
    def load_data(self, button):
        """데이터 로드"""
        with self.output_status:
            self.output_status.clear_output()
            
            if not self.file_upload.value:
                print("⚠️ CSV 파일을 선택해주세요.")
                return
            
            print("📂 데이터를 로딩 중입니다...")
            
            try:
                dataframes = []
                for filename, file_info in self.file_upload.value.items():
                    # 파일 내용을 pandas로 읽기
                    content = file_info['content']
                    df = pd.read_csv(io.BytesIO(content))
                    df['file'] = filename
                    dataframes.append(df)
                    print(f"✅ {filename} 로드 완료")
                
                self.df_combined = pd.concat(dataframes, ignore_index=True)
                print(f"🎉 총 {len(self.df_combined):,}개의 데이터 포인트가 로드되었습니다!")
                
                # 데이터 미리보기
                with self.output_data:
                    self.output_data.clear_output()
                    print("📋 데이터 미리보기:")
                    display(self.df_combined.head(10))
                
            except Exception as e:
                print(f"❌ 오류 발생: {str(e)}")
    
    def analyze_data(self, button):
        """데이터 분석"""
        with self.output_status:
            if self.df_combined is None:
                print("⚠️ 먼저 데이터를 로드해주세요.")
                return
            
            print("🔍 데이터를 분석 중입니다...")
            
            try:
                # 데이터 구조 확인
                print("📋 데이터 구조 확인:")
                print(f"컬럼명: {list(self.df_combined.columns)}")
                print(f"데이터 형태: {self.df_combined.shape}")
                
                # 기본 데이터 전처리
                df = self.df_combined.copy()
                
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
                        print("⚠️ 'no' 컬럼을 찾을 수 없어서 인덱스를 사용합니다.")
                
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
                        print(f"✅ '{alternative}' 컬럼을 '{original}'로 매핑했습니다.")
                    
                    # 여전히 없는 컬럼 확인
                    still_missing = [col for col in required_cols if col not in df.columns]
                    if still_missing:
                        print(f"❌ 다음 필수 컬럼을 찾을 수 없습니다: {still_missing}")
                        print(f"사용 가능한 컬럼: {list(df.columns)}")
                        return
                
                # 데이터 전처리 계속
                df['cell'] = df['CELL ID'].apply(self.extract_cell_from_id)
                df['position'] = df['file'].apply(self.extract_position_from_file)
                df['x'] = df['no'] * 10.96
                df['side'] = df['position'].apply(self.position_to_side)
                
                # position이 "4"가 아닌 데이터 분석 (result1)
                df_not_4 = df[df['position'] != "4"].copy()
                
                if len(df_not_4) > 0:
                    print("📊 Position 1-3 데이터 분석 중...")
                    
                    try:
                        df_pivot = df_not_4.pivot_table(
                            index='no',
                            columns=['Glass ID', 'cell', 'position'],
                            values='Avg Offset',
                            aggfunc='first'
                        )
                        
                        print(f"✅ Pivot 테이블 생성 완료: {df_pivot.shape}")
                        
                        # 기준점 차감
                        reference_row = min(455, len(df_pivot) - 1)
                        if reference_row >= 0:
                            df_pivot = df_pivot.sub(df_pivot.iloc[reference_row], axis=1)
                            print(f"✅ 기준점({reference_row + 1}번째 행) 차감 완료")
                        
                        # pivot_longer 구현 - 안전한 방법
                        df_pivot_reset = df_pivot.reset_index()
                        value_columns = [col for col in df_pivot_reset.columns if col != 'no']
                        
                        df_long_list = []
                        for col in value_columns:
                            if isinstance(col, tuple) and len(col) == 3:
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
                            df_long = df_long.dropna()
                        else:
                            print("❌ 데이터 변환 실패")
                            df_long = pd.DataFrame()
                            
                    except Exception as e:
                        print(f"❌ Pivot 처리 중 오류: {str(e)}")
                        df_long = pd.DataFrame()
                    
                    if len(df_long) > 0:
                        df_long['side'] = df_long['position'].apply(self.position_to_side)
                        
                        # hump 분석
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
                                result1['split'] = result1['cell'].apply(self.assign_split_category)
                                print(f"✅ Position 1-3 분석 완료: {len(result1)}개 결과")
                            else:
                                result1 = pd.DataFrame()
                                print("⚠️ Position 1-3 분석 결과가 없습니다.")
                                
                        except Exception as e:
                            print(f"❌ Hump 분석 중 오류: {str(e)}")
                            result1 = pd.DataFrame()
                    else:
                        result1 = pd.DataFrame()
                        print("⚠️ Position 1-3 데이터 변환 결과가 없습니다.")
                else:
                    result1 = pd.DataFrame()
                    print("ℹ️ Position 1-3 데이터가 없습니다.")
                
                # position이 "4"인 데이터 분석 (result2)
                df_4 = df[df['position'] == "4"].copy()
                
                if len(df_4) > 0:
                    print("📊 Position 4 데이터 분석 중...")
                    
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
                            result2['split'] = result2['cell'].apply(self.assign_split_category)
                            print(f"✅ Position 4 분석 완료: {len(result2)}개 결과")
                        else:
                            result2 = pd.DataFrame()
                            print("⚠️ Position 4 분석 결과가 없습니다.")
                            
                    except Exception as e:
                        print(f"❌ Position 4 분석 중 오류: {str(e)}")
                        result2 = pd.DataFrame()
                else:
                    result2 = pd.DataFrame()
                    print("ℹ️ Position 4 데이터가 없습니다.")
                
                # 결과 합치기
                if len(result1) > 0 and len(result2) > 0:
                    self.result_df = pd.concat([result1, result2], ignore_index=True)
                    print("✅ 모든 분석 결과 합치기 완료")
                elif len(result1) > 0:
                    self.result_df = result1
                    print("ℹ️ Position 1-3 결과만 사용")
                elif len(result2) > 0:
                    self.result_df = result2
                    print("ℹ️ Position 4 결과만 사용")
                else:
                    self.result_df = pd.DataFrame()
                    print("❌ 분석 결과가 없습니다.")
                
                if len(self.result_df) > 0:
                    self.result_df = self.result_df.sort_values(['glass', 'cell', 'side']).reset_index(drop=True)
                    print(f"🎉 최종 분석 완료! 총 {len(self.result_df)}개의 결과가 생성되었습니다.")
                
                self.processed_df = df
                
                # 결과 표시
                with self.output_data:
                    self.output_data.clear_output()
                    if len(self.result_df) > 0:
                        print("📋 분석 결과:")
                        display(self.result_df)
                    else:
                        print("❌ 표시할 분석 결과가 없습니다.")
                        print("💡 데이터 형식을 확인해주세요:")
                        print("- CELL ID (또는 Cell ID, cell_id 등)")
                        print("- Avg Offset (또는 avg_offset, AvgOffset 등)")
                        print("- Glass ID (또는 Glass_ID, glass_id 등)")
                        print("- no (또는 No, index 등의 순번 컬럼)")
                
                # 그래프 생성
                if len(self.result_df) > 0:
                    self.create_plots()
                
            except Exception as e:
                print(f"❌ 분석 중 전체 오류 발생: {str(e)}")
                print("디버그 정보:")
                print(f"DataFrame 컬럼: {list(self.df_combined.columns) if self.df_combined is not None else 'None'}")
                print(f"DataFrame 크기: {self.df_combined.shape if self.df_combined is not None else 'None'}")
    
    def create_plots(self):
        """그래프 생성 및 표시"""
        with self.output_plots:
            self.output_plots.clear_output()
            
            try:
                print("📊 그래프를 생성 중입니다...")
                
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
                fig1 = px.scatter(
                    self.processed_df, 
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
                fig1.update_traces(marker=dict(size=4, opacity=0.7))
                fig1.show()
                
                # 2. 위치별 평균 프로파일
                df_avg = self.processed_df.groupby(['side', 'x'])['Avg Offset'].mean().reset_index()
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
                fig2.update_traces(line=dict(width=3), marker=dict(size=6))
                fig2.show()
                
                # 3. Hump Height vs Position
                if len(self.result_df) > 0:
                    result_filtered = self.result_df[self.result_df['side'] != 'Down']
                    
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
                    fig3.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='white')))
                    fig3.show()
                
                self.plots = {'fig1': fig1, 'fig2': fig2, 'fig3': fig3}
                print("✅ 그래프 생성 완료!")
                
            except Exception as e:
                print(f"❌ 그래프 생성 중 오류: {str(e)}")
    
    def save_results(self, button):
        """결과 저장"""
        with self.output_status:
            if self.result_df is None:
                print("⚠️ 먼저 분석을 완료해주세요.")
                return
            
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # CSV 저장
                csv_filename = f"analysis_result_{timestamp}.csv"
                self.result_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"💾 CSV 파일 저장 완료: {csv_filename}")
                
                # 색상이 보존된 그래프 HTML 저장
                if self.plots:
                    html_filename = f"analysis_plots_{timestamp}.html"
                    
                    # 색상이 보존된 HTML 생성
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
                        'fig1': '📈 전체 데이터 시각화',
                        'fig2': '📉 위치별 SIP 잉크젯 Edge Profile', 
                        'fig3': '📊 Hump Height vs Position 분석'
                    }
                    
                    for i, (name, plot) in enumerate(self.plots.items(), 1):
                        title = plot_titles.get(name, f'그래프 {i}')
                        html_content += f'<h2>{title}</h2>\n'
                        html_content += '<div class="plot-container">\n'
                        
                        # Plotly 그래프를 HTML로 변환 (색상 보존 설정)
                        plot_html = plot.to_html(
                            include_plotlyjs=False,  # 이미 스크립트가 포함되어 있음
                            div_id=f"plot_{name}",
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': f'plot_{name}',
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
                    display_timestamp = datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')
                    html_content += f"""
                            <div class="timestamp">
                                생성 일시: {display_timestamp}
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    with open(html_filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"🖼️ 색상이 보존된 그래프 HTML 파일 저장 완료: {html_filename}")
                
                print("🎉 모든 결과가 저장되었습니다!")
                print("✅ HTML 파일을 브라우저에서 열면 원본과 동일한 색상의 그래프를 확인할 수 있습니다!")
                
            except Exception as e:
                print(f"❌ 저장 중 오류 발생: {str(e)}")

# 사용법 출력
print("""
🚀 CSV 분석 도구 사용법:

1. 아래 코드를 실행하여 분석기를 시작합니다:
   analyzer = CSVAnalyzer()

2. 파일 업로드 위젯에서 CSV 파일들을 선택합니다.

3. '📂 데이터 로드' 버튼을 클릭합니다.

4. '🚀 분석 시작' 버튼을 클릭합니다.

5. '💾 결과 저장' 버튼으로 결과를 저장합니다.

필요한 패키지: pandas, numpy, matplotlib, seaborn, plotly, ipywidgets
설치: pip install pandas numpy matplotlib seaborn plotly ipywidgets
""")

# 분석기 시작
# analyzer = CSVAnalyzer()