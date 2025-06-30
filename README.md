# 📊 CSV 파일 분석 도구 (CSV Analysis Tool)

> 여러 CSV 파일을 업로드하여 SIP 잉크젯 Edge Profile 분석 및 시각화를 수행하는 Python 웹 애플리케이션

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 주요 기능

### 📂 **스마트 파일 업로드**
- 🔄 **다중 파일 지원**: 여러 CSV 파일을 한번에 업로드
- 🧠 **자동 컬럼 매핑**: 다양한 컬럼명 형식 자동 인식
- 📋 **데이터 검증**: 업로드된 파일의 구조 자동 확인

### 🔍 **고급 데이터 분석**
- 📊 **Position별 분석**: Left, Right, Top, Down 위치별 데이터 처리
- 📈 **Hump 분석**: 각 위치별 높이 차이(Hump DY) 및 위치(Hump DX) 계산
- 🎯 **Split 카테고리**: Cell 위치에 따른 자동 분류 (Sp1, Sp2, Sp3)

### 📈 **인터랙티브 시각화**
- 🎨 **전체 데이터 시각화**: Glass ID와 Cell별 scatter plot
- 📉 **SIP 프로파일**: 위치별 평균 Edge Profile 그래프
- 📊 **Hump 분석 차트**: Position별 높이 비교 bar chart

### 💾 **결과 내보내기**
- 📄 **CSV 다운로드**: 분석 결과를 CSV 파일로 저장
- 🖼️ **그래프 저장**: 인터랙티브 HTML 그래프 다운로드
- 📦 **통합 패키지**: 모든 결과를 ZIP 파일로 한번에 다운로드

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-username/csv-analysis-tool.git
cd csv-analysis-tool

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. 애플리케이션 실행

#### 🌐 **Streamlit 웹 앱 (권장)**
```bash
streamlit run app.py --server.fileWatcherType none --server.runOnSave false
```

#### 📓 **Jupyter Notebook 버전**
```bash
jupyter notebook
# jupyter_app.ipynb 파일 실행
```

### 3. 웹 브라우저 접속
- Streamlit: `http://localhost:8501`
- Jupyter: `http://localhost:8888`

## 📦 필요한 패키지

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0
ipywidgets>=8.0.0  # Jupyter 버전용
```

## 📁 프로젝트 구조

```
csv-analysis-tool/
├── app.py                 # Streamlit 메인 애플리케이션
├── jupyter_app.py         # Jupyter Notebook 버전
├── requirements.txt       # 필수 패키지 목록
├── README.md             # 프로젝트 문서
├── data/                 # 샘플 데이터 (선택사항)
│   └── sample.csv
└── docs/                 # 추가 문서
    ├── user_guide.md
    └── troubleshooting.md
```

## 🎯 사용법

### 1단계: 파일 업로드 📂
1. **"🔄 파일 업로드"** 탭 선택
2. **"파일 선택"** 버튼 클릭 또는 드래그 앤 드롭
3. 여러 CSV 파일을 동시 선택 (Ctrl+클릭)
4. **"📂 데이터 로드"** 버튼 클릭

### 2단계: 데이터 분석 📈
1. **"📈 데이터 분석"** 탭으로 이동
2. **"🚀 분석 시작"** 버튼 클릭
3. 실시간 분석 진행 상황 확인
4. 생성된 그래프 및 결과 테이블 확인

### 3단계: 결과 다운로드 💾
1. **"💾 결과 다운로드"** 탭으로 이동
2. 원하는 형식으로 결과 다운로드:
   - **CSV 파일**: 분석 결과 데이터
   - **HTML 그래프**: 인터랙티브 차트
   - **ZIP 패키지**: 모든 결과 통합

## 📊 지원되는 데이터 형식

### 필수 컬럼
애플리케이션은 다양한 컬럼명을 자동으로 인식합니다:

| 표준 컬럼명 | 지원되는 대안 |
|------------|---------------|
| `no` | `No`, `NO`, `index`, `Index` (또는 자동 생성) |
| `CELL ID` | `Cell ID`, `cell_id`, `cellid`, `Cell_ID`, `CellID` |
| `Avg Offset` | `avg_offset`, `AvgOffset`, `Average Offset`, `Offset` |
| `Glass ID` | `Glass_ID`, `glass_id`, `glassid`, `GlassID`, `glass` |

### 데이터 예시
```csv
no,CELL ID,Avg Offset,Glass ID
1,A01,12.5,G001
2,A01,13.2,G001
3,A01,11.8,G001
...
```

## 🔧 환경별 설정

### 🐳 **Docker 환경**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.fileWatcherType", "none"]
```

### ☸️ **Kubeflow/Kubernetes 환경**
```bash
# 파일 워처 문제 해결
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
export STREAMLIT_SERVER_RUN_ON_SAVE=false
streamlit run app.py
```

### 🖥️ **로컬 개발 환경**
```bash
# 개발 모드 실행
streamlit run app.py --server.runOnSave true
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. `inotify watch limit reached` 오류
```bash
# 해결방법 1: 파일 워처 비활성화
streamlit run app.py --server.fileWatcherType none

# 해결방법 2: 시스템 한계 증가 (Linux)
echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches
```

#### 2. `컬럼을 찾을 수 없습니다` 오류
- CSV 파일의 첫 번째 행이 헤더인지 확인
- 필수 컬럼명이 포함되어 있는지 확인
- 파일 인코딩이 UTF-8인지 확인

#### 3. 메모리 부족 오류
```python
# 큰 파일 처리를 위한 청크 읽기
df = pd.read_csv(file, chunksize=10000)
```

#### 4. 그래프 렌더링 문제
- 브라우저 캐시 삭제
- 다른 브라우저에서 테스트
- Plotly 버전 확인

### 로그 및 디버깅

```bash
# 상세 로그와 함께 실행
streamlit run app.py --logger.level debug

# 특정 포트에서 실행
streamlit run app.py --server.port 8502
```

## 🎨 커스터마이징

### 테마 변경
`.streamlit/config.toml` 파일 생성:
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 기능 확장
새로운 분석 기능 추가 예시:
```python
def custom_analysis(df):
    """사용자 정의 분석 함수"""
    # 새로운 분석 로직 구현
    result = df.groupby('category').agg({
        'value': ['mean', 'std', 'count']
    })
    return result
```

## 🤝 기여하기

1. **Fork** 이 저장소
2. **Feature branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 개발 가이드라인
- 코드 스타일: PEP 8 준수
- 테스트: pytest 사용
- 문서화: docstring 필수
- 커밋 메시지: Conventional Commits 형식

## 📈 성능 최적화

### 대용량 파일 처리
```python
# 메모리 효율적인 처리
@st.cache_data
def load_large_file(file_path):
    return pd.read_csv(file_path, low_memory=False)

# 진행률 표시
progress_bar = st.progress(0)
for i, chunk in enumerate(chunks):
    # 처리 로직
    progress_bar.progress((i + 1) / total_chunks)
```

### 캐싱 활용
```python
# 결과 캐싱으로 속도 향상
@st.cache_data
def analyze_data(df_hash):
    # 분석 로직
    return result
```

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

## 👥 제작자

- **개발자**: [Your Name](https://github.com/your-username)
- **이메일**: your.email@example.com
- **프로젝트 링크**: [https://github.com/your-username/csv-analysis-tool](https://github.com/your-username/csv-analysis-tool)

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 라이브러리들을 사용합니다:
- [Streamlit](https://streamlit.io/) - 웹 애플리케이션 프레임워크
- [Pandas](https://pandas.pydata.org/) - 데이터 처리
- [Plotly](https://plotly.com/) - 인터랙티브 시각화
- [NumPy](https://numpy.org/) - 수치 계산

## 📞 지원 및 문의

- **이슈 리포트**: [GitHub Issues](https://github.com/your-username/csv-analysis-tool/issues)
- **기능 요청**: [GitHub Discussions](https://github.com/your-username/csv-analysis-tool/discussions)
- **문서**: [Wiki](https://github.com/your-username/csv-analysis-tool/wiki)

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! ⭐**

Made with ❤️ and Python

</div>