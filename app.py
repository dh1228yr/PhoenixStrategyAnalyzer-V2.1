"""
Phoenix Strategy Analyzer
신규 분석 모듈 통합 대시보드
기능:
- CSV 업로드
- Walk-Forward 검증
- Quantstats 리포트
- 손실 분석
- 종합 평가
- PDF 리포트 생성
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os
import base64
from io import BytesIO

# 현재 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 신규 분석 모듈
from analysis.returns_converter import ReturnsConverter
from analysis.walk_forward import WalkForwardAnalyzer
from analysis.quantstats_wrapper import QuantstatsAnalyzer

# 포맷팅 함수
def format_number(value):
    """천단위 콤마 포맷"""
    if isinstance(value, (int, float)):
        if abs(value) >= 1:
            return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
        else:
            return f"{value:.2f}"
    return str(value)

def format_percent(value):
    """퍼센트 포맷 (천단위 콤마)"""
    if isinstance(value, (int, float)):
        return f"{value:,.2f}%"
    return str(value)

# 페이지 설정
st.set_page_config(
    page_title="🔥 Phoenix Strategy Analyzer",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit 테마 강제 적용
st.markdown("""
<style>
    /* Streamlit 루트 배경 */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(
            135deg,
            #0a0d12 0%,
            #12161f 50%,
            #0a0d12 100%
        ) !important;
    }
    
    /* 헤더 배경 */
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* 툴바 배경 */
    [data-testid="stToolbar"] {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# CSS 스타일 - 완전한 다크 테마 + 그라데이션 + 최대 가독성
st.markdown("""
<style>
    /* Streamlit 기본 배경 완전 제거 및 다크 그라데이션 강제 적용 */
    .stApp {
        background: linear-gradient(
            135deg,
            #0a0d12 0%,
            #12161f 50%,
            #0a0d12 100%
        ) !important;
    }
    
    /* 메인 컨텐츠 영역 */
    .main {
        background: transparent !important;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
        background: transparent !important;
    }
    
    /* 메인 영역 추가 그라데이션 오버레이 */
    section[data-testid="stAppViewContainer"] > .main {
        background: radial-gradient(
            ellipse at top center,
            rgba(30, 36, 51, 0.3) 0%,
            transparent 70%
        ) !important;
    }
    
    /* 사이드바 - 그라데이션 배경 */
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #14171e 0%,
            #0c0f15 100%
        );
        padding-top: 2rem;
    }
    
    /* 사이드바 타이틀 */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #ffa366 !important;
        margin-bottom: 1.5rem !important;
        text-shadow: 0 0 15px rgba(255, 107, 53, 0.5), 0 2px 8px rgba(255, 107, 53, 0.3) !important;
    }
    
    /* 사이드바 라디오 버튼 라벨 - 크게 + 이모지 스타일 */
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 1rem !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.8rem;
    }
    
    /* 사이드바 메뉴 옵션 */
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1.1rem !important;
        padding: 0.7rem 1rem !important;
        border-radius: 8px;
        transition: all 0.2s;
        color: #e5e7eb !important;
        background: linear-gradient(145deg, #1a1f2c 0%, #14171e 100%);
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background: linear-gradient(145deg, #242b3d 0%, #1e2535 100%);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.15);
    }
    
    /* 사이드바 섹션 제목 (상태 등) */
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    }
    
    /* 사이드바 일반 텍스트 */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #f3f4f6 !important;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* 사이드바 메트릭 */
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #e5e7eb !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    /* 메인 헤더 - 최대 가독성 */
    h1 {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        color: #ffa366 !important;
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.6), 0 2px 8px rgba(255, 107, 53, 0.4) !important;
    }
    
    /* 섹션 헤더 - 매우 밝게 */
    h2 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
    }
    
    h3 {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.8rem !important;
        color: #f3f4f6 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
    }
    
    /* 메트릭 스타일 */
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #e5e7eb !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.95rem !important;
        font-weight: 600;
    }
    
    /* 성공/경고/위험 박스 - 그라데이션 */
    .success-box {
        background: linear-gradient(120deg, #064e3b 0%, #065f46 50%, #047857 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #10b981;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    .success-box h3 {
        font-size: 1.4rem !important;
        margin-bottom: 0.5rem !important;
        color: #a7f3d0 !important;
        font-weight: 700;
    }
    .success-box p {
        font-size: 1.1rem !important;
        margin: 0;
        color: #d1fae5 !important;
        font-weight: 500;
    }
    
    .warning-box {
        background: linear-gradient(120deg, #78350f 0%, #92400e 50%, #b45309 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #f59e0b;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }
    .warning-box h3 {
        font-size: 1.4rem !important;
        margin-bottom: 0.5rem !important;
        color: #fde68a !important;
        font-weight: 700;
    }
    .warning-box p {
        font-size: 1.1rem !important;
        margin: 0;
        color: #fef3c7 !important;
        font-weight: 500;
    }
    
    .danger-box {
        background: linear-gradient(120deg, #7f1d1d 0%, #991b1b 50%, #b91c1c 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #ef4444;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }
    .danger-box h3 {
        font-size: 1.4rem !important;
        margin-bottom: 0.5rem !important;
        color: #fecaca !important;
        font-weight: 700;
    }
    .danger-box p {
        font-size: 1.1rem !important;
        margin: 0;
        color: #fee2e2 !important;
        font-weight: 500;
    }
    
    /* 일반 텍스트 */
    .stMarkdown p {
        font-size: 1rem;
        line-height: 1.6;
        color: #d1d5db;
    }
    
    /* 판정 텍스트 */
    .judgment-text {
        font-size: 1.15rem !important;
        font-weight: 500;
        line-height: 1.8;
        margin: 0.8rem 0;
        color: #f3f4f6;
    }
    
    /* 가이드 박스 - 그라데이션 */
    .guide-box {
        font-size: 1rem !important;
        line-height: 1.8 !important;
        padding: 1.5rem !important;
        background: linear-gradient(120deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        color: #ffffff !important;
    }
    .guide-box strong {
        font-size: 1.05rem !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* 캡션 */
    .caption-text {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-top: 0.3rem;
        line-height: 1.4;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }
    
    /* 파일 업로더 */
    [data-testid="stFileUploader"] label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #e5e7eb;
    }
    
    [data-testid="stFileUploader"] section {
        font-size: 1rem !important;
        background: linear-gradient(145deg, #1e2330 0%, #181d28 100%);
        border: 2px dashed #4b5563;
        transition: all 0.3s;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #ff6b35;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
    }
    
    /* Success/Info/Warning/Error 메시지 */
    .stAlert {
        font-size: 1.05rem !important;
        padding: 1rem !important;
        font-weight: 500;
    }
    
    .stAlert p {
        font-size: 1.05rem !important;
        margin: 0 !important;
    }
    
    /* 버튼 - 그라데이션 */
    .stButton > button {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        background: linear-gradient(135deg, #ff6b35 0%, #ff8555 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #ff8555 0%, #ffa575 100%);
        box-shadow: 0 6px 16px rgba(255, 107, 53, 0.4);
        transform: translateY(-1px);
    }
    
    /* 셀렉트박스 */
    .stSelectbox label {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #e5e7eb;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: linear-gradient(145deg, #1e2330 0%, #181d28 100%);
    }
    
    /* 데이터프레임 */
    [data-testid="stDataFrame"] {
        font-size: 0.95rem !important;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.95rem;
        margin-top: 3rem;
        padding: 1.5rem 0;
        border-top: 1px solid #374151;
    }
    
    /* 사이드바 구분선 */
    [data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
        border-color: #374151;
    }
    
    /* 구분선 */
    hr {
        border-color: #374151;
    }
    
    /* 차트 배경 - 다크 그레이 */
    .js-plotly-plot .plotly {
        background: #2d3748 !important;
    }
    
    /* 차트 텍스트 가독성 - 매우 밝게 */
    .js-plotly-plot .plotly text {
        fill: #f3f4f6 !important;
        font-weight: 600 !important;
    }
    
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text {
        fill: #ffffff !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    
    .js-plotly-plot .plotly .gtitle {
        fill: #ffffff !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }
    
    /* 차트 그리드 라인 */
    .js-plotly-plot .plotly .gridlayer path {
        stroke: #4a5568 !important;
        stroke-opacity: 0.3 !important;
    }
</style>
""", unsafe_allow_html=True)


class EnhancedDashboard:
    """Phoenix Strategy Analyzer"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """세션 상태 초기화"""
        if 'csv_data' not in st.session_state:
            st.session_state.csv_data = None
        if 'converter' not in st.session_state:
            st.session_state.converter = None
        if 'wf_results' not in st.session_state:
            st.session_state.wf_results = None
        if 'rolling_wf_results' not in st.session_state:
            st.session_state.rolling_wf_results = None
        if 'qs_metrics' not in st.session_state:
            st.session_state.qs_metrics = None
        if 'validators_16_report' not in st.session_state:  # ← 추가!
            st.session_state.validators_16_report = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "📤 CSV 업로드"
    
    def render_sidebar(self):
        """사이드바 메뉴"""
        with st.sidebar:
            st.markdown("# 🔥 Phoenix Analyzer")
            st.markdown("---")
            
            # 🚀 전체 분석 실행 버튼 제거! (자동 실행되므로)
            # if st.session_state.csv_data is not None:
            #     if st.button("🚀 전체 분석 한번에 실행", ...):
            #         ...
            
            # 라디오 버튼으로 메뉴 구성
            menu_options = [
                "📤 CSV 업로드",
                "📊 Walk-Forward",
                "🔄 Rolling WF (고급)",
                "📈 Quantstats",
                "📉 손실 분석",
                "💰 수익 분석",
                "🔬 16개 검증",
                "🎯 종합 평가"
            ]
            
            selected = st.radio(
                "📋 분석 메뉴",
                menu_options,
                index=menu_options.index(st.session_state.current_page)
            )
            
            st.session_state.current_page = selected
            
            st.markdown("---")
            
            # 분석 상태 표시
            if st.session_state.csv_data is not None:
                st.markdown("### 📊 분석 상태")
                
                stats = st.session_state.converter.get_statistics() if st.session_state.converter else {}
                
                st.metric("거래 수", f"{format_number(stats.get('total_trades', 0))}건")
                st.metric("승률", format_percent(stats.get('win_rate', 0)))
                
                # 분석 완료 상태 표시
                wf_status = "✅ 완료" if st.session_state.wf_results else "❌ 미완료"
                st.markdown(f"**Walk-Forward**: {wf_status}")
                
                qs_status = "✅ 완료" if st.session_state.qs_metrics else "❌ 미완료"
                st.markdown(f"**Quantstats**: {qs_status}")
                
                v16_status = "✅ 완료" if st.session_state.validators_16_report else "❌ 미완료"
                st.markdown(f"**16개 검증**: {v16_status}")
    
    def render_header(self):
        """헤더 렌더링"""
        st.title("🔥 Phoenix Strategy Analyzer")
        st.markdown('<p class="subtitle">백테스트 분석 → Walk-Forward 검증 → Quantstats 평가 → 16개 검증 시스템</p>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_page_upload(self):
        """CSV 업로드 페이지"""
        st.header("📤 백테스트 CSV 업로드")
        
        # 업로드 방법 두 가지 제공
        st.markdown("""
        <div style="background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <p style="color: #ffffff; margin: 0;">
                <strong>📁 TradingView CSV 업로드</strong><br>
                Strategy Tester → List of Trades → 마우스로 드래그 또는 클릭으로 업로드<br><br>
                <strong style="color: #fbbf24;">⚡ 업로드 즉시 모든 분석이 자동으로 실행됩니다!</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 파일 업로드 (드래그 앤 드롭 지원)
        uploaded_file = st.file_uploader(
            "CSV 파일을 여기에 드래그하거나 클릭하세요",
            type=['csv'],
            help="TradingView Strategy Tester → List of Trades → Export (CSV)",
            key="csv_uploader_main"
        )
        
        if uploaded_file is not None:
            try:
                import tempfile
                import os
                
                # Hugging Face Spaces 임시 폴더에 파일 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_path = tmp_file.name
                
                # 파일 읽기 (다양한 인코딩 지원)
                try:
                    df = pd.read_csv(tmp_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(tmp_path, encoding='euc-kr')
                    except:
                        df = pd.read_csv(tmp_path, encoding='latin1')
                
                # 임시 파일 삭제
                os.unlink(tmp_path)
                
                st.session_state.csv_data = df
                
                # ReturnsConverter 생성
                converter = ReturnsConverter(df)
                trades = converter.parse_trades()
                
                if len(trades) == 0:
                    st.error("❌ Entry/Exit 매칭 실패")
                    st.info("💡 CSV 형식 확인: 거래번호, 타입, 날짜/시간, 진입가, 청산가 컬럼 필요")
                    return
                
                st.session_state.converter = converter
                
                # 기본 통계
                stats = converter.get_statistics()
                
                st.success(f"✅ CSV 파싱 완료: {format_number(stats['total_trades'])}건 거래")
                
                # ========== 🚀 전체 분석 자동 실행 시작! ==========
                st.markdown("---")
                st.markdown("### 🚀 전체 분석 자동 실행 중...")
                
                # 프로그레스 바
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 1. Walk-Forward 분석
                status_text.markdown("**1/3 📊 Walk-Forward 분석 중...**")
                progress_bar.progress(20)
                
                try:
                    wf = WalkForwardAnalyzer(trades, train_ratio=0.7)
                    st.session_state.wf_results = wf.analyze()
                    progress_bar.progress(40)
                    st.success("✅ Walk-Forward 분석 완료")
                except Exception as e:
                    st.warning(f"⚠️ Walk-Forward 분석 실패: {e}")
                    st.session_state.wf_results = None
                
                # 2. Quantstats 분석
                status_text.markdown("**2/3 📈 Quantstats 분석 중...**")
                progress_bar.progress(50)
                
                try:
                    returns = converter.to_daily_returns()
                    if len(returns) > 0:
                        qs_analyzer = QuantstatsAnalyzer(returns)
                        metrics = qs_analyzer.get_metrics()
                        if 'error' not in metrics:
                            st.session_state.qs_metrics = metrics
                            progress_bar.progress(70)
                            st.success("✅ Quantstats 분석 완료")
                        else:
                            st.warning(f"⚠️ Quantstats 분석 실패: {metrics['error']}")
                            st.session_state.qs_metrics = None
                    else:
                        st.warning("⚠️ 수익률 데이터 부족")
                        st.session_state.qs_metrics = None
                except Exception as e:
                    st.warning(f"⚠️ Quantstats 분석 실패: {e}")
                    st.session_state.qs_metrics = None
                
                # 3. 16개 검증 시스템
                status_text.markdown("**3/3 🔬 16개 검증 시스템 실행 중...**")
                progress_bar.progress(80)
                
                try:
                    from analysis.validators.comprehensive import ComprehensiveEvaluator
                    
                    evaluator = ComprehensiveEvaluator(
                        trades,
                        pd.Timestamp(trades['entry_date'].min()),
                        pd.Timestamp(trades['exit_date'].max()),
                        initial_capital=50.0
                    )
                    
                    # 16개 검증 실행
                    evaluator.run_all_validators()
                    evaluator.check_disqualification_criteria()
                    evaluator.generate_final_score()
                    
                    report = evaluator.get_comprehensive_report()
                    st.session_state.validators_16_report = report
                    
                    progress_bar.progress(100)
                    st.success("✅ 16개 검증 완료")
                    
                except ImportError as e:
                    st.warning(f"⚠️ 16개 검증 모듈 로드 실패: {e}")
                    st.session_state.validators_16_report = None
                except Exception as e:
                    st.warning(f"⚠️ 16개 검증 실패: {e}")
                    st.session_state.validators_16_report = None
                
                # 완료 메시지
                status_text.empty()
                progress_bar.empty()
                
                st.markdown("---")
                st.success("🎉 **모든 분석 완료!** 이제 '🎯 종합 평가' 페이지로 이동하세요.")
                
                # 자동 페이지 이동 버튼
                if st.button("🎯 종합 평가 보러가기", type="primary", use_container_width=True):
                    st.session_state.current_page = "🎯 종합 평가"
                    st.rerun()
                
                # ========== 🚀 전체 분석 자동 실행 끝! ==========
                
                st.markdown("---")
                
                # 기본 통계 표시 (간단 버전)
                st.markdown("### 📊 기본 통계 (미리보기)")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("총 거래", f"{format_number(stats['total_trades'])}건")
                
                with col2:
                    st.metric("승률", format_percent(stats['win_rate']))
                
                with col3:
                    st.metric("총 수익률", format_percent(stats['total_return']))
                
                with col4:
                    period = stats['period_days']
                    st.metric("기간", f"{format_number(period)}일")
                
                # 거래 목록 (접기)
                with st.expander("📋 최근 거래 목록 (상위 20개)"):
                    display_df = trades[['trade_num', 'direction', 'entry_date', 'exit_date', 
                                        'return_pct', 'runup_pct', 'drawdown_pct']].tail(20).copy()
                    display_df.columns = ['거래번호', '방향', '진입날짜', '청산날짜', 
                                          '수익률%', '런업%', '드로다운%']
                    st.dataframe(display_df, use_container_width=True, height=400)
                
            except Exception as e:
                st.error(f"❌ CSV 로딩 실패: {str(e)}")
                st.info("💡 문제 해결:")
                st.write("1. CSV 파일이 UTF-8 인코딩인지 확인")
                st.write("2. 한글 헤더가 있는지 확인")
                st.write("3. 파일에 거래 데이터가 있는지 확인")
        else:
            st.info("💡 CSV 파일을 업로드하여 시작하세요!")
            
            # 예시 형식
            with st.expander("📋 예상되는 CSV 형식"):
                st.write("""
                | 거래 # | 타입 | 날짜/시간 | 신호 | 가격 | ... |
                |--------|------|----------|------|------|-----|
                | 1 | 매수 진입 | 2020-06-30 | 신호 | 0.083 | ... |
                | 1 | 매수 청산 | 2020-06-30 | 익절 | 0.084 | ... |
                """)
    
    
    def render_page_walkforward(self):
        """Walk-Forward 페이지"""
        st.header("📊 Walk-Forward 분석")
        
        if st.session_state.converter is None:
            st.warning("⚠️ 먼저 CSV를 업로드하세요.")
            return
        
        # 분석 버튼
        if st.button("🚀 Walk-Forward 분석 실행", type="primary", use_container_width=True):
            with st.spinner("분석 중..."):
                trades = st.session_state.converter.trades
                
                # Walk-Forward 분석
                wf = WalkForwardAnalyzer(trades, train_ratio=0.7)
                results = wf.analyze()
                
                st.session_state.wf_results = results
        
        # 결과 표시
        if st.session_state.wf_results is not None:
            results = st.session_state.wf_results
            
            # 과적합 점수
            score = results['overfit_score']
            
            if score >= 80:
                st.markdown(f'<div class="success-box"><h3>✅ 과적합 점수: {format_number(score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            elif score >= 60:
                st.markdown(f'<div class="warning-box"><h3>⚠️ 과적합 점수: {format_number(score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="danger-box"><h3>❌ 과적합 점수: {format_number(score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Train vs Test 비교
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Train 구간")
                train = results['train_metrics']
                st.metric("거래 수", f"{format_number(train['total_trades'])}건")
                st.metric("승률", format_percent(train['win_rate']))
                st.metric("총 수익률", format_percent(train['total_return']))
                st.metric("최대 낙폭", format_percent(train['max_drawdown']))
            
            with col2:
                st.markdown("### 📉 Test 구간")
                test = results['test_metrics']
                st.metric("거래 수", f"{format_number(test['total_trades'])}건")
                st.metric("승률", format_percent(test['win_rate']), 
                         delta=format_percent(results['comparison']['win_rate_diff']))
                st.metric("총 수익률", format_percent(test['total_return']))
                st.metric("최대 낙폭", format_percent(test['max_drawdown']))
            
            st.markdown("---")
            
            # 판정 상세
            st.markdown("### 🎯 판정 상세")
            
            # 판정 결과 표시
            for key, judgment in results['judgments'].items():
                st.markdown(f'<p class="judgment-text"><strong>{key}</strong>: {judgment}</p>', 
                            unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 📚 판정 기준 가이드
            st.markdown("### 📚 Walk-Forward 판정 기준 가이드")
            
            # 실제 계산 값 표시
            comp = results['comparison']
            win_rate_diff = abs(comp['win_rate_diff'])
            return_diff_pct = abs(comp['return_diff_pct'])
            
            # drawdown_ratio 안전하게 계산
            train_dd = abs(train['max_drawdown'])
            test_dd = abs(test['max_drawdown'])
            
            if train_dd > 0:
                dd_ratio = test_dd / train_dd
            else:
                dd_ratio = 0.0
            
            # 현재 전략의 실제 값
            st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📊 현재 전략의 실제 값</h4>', unsafe_allow_html=True)
            st.markdown('<p style="color: #9ca3af; font-size: 0.9rem; margin-top: -0.5rem;">Train과 Test 구간의 실제 차이를 확인하세요</p>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1rem; border-radius: 8px; border-left: 4px solid #10b981;">
                    <p style="color: #a7f3d0; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.5rem;">1️⃣ 승률 차이</p>
                    <p style="color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0.3rem 0;">{}</p>
                    <p style="color: #d1d5db; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                        Train: {} → Test: {}<br>
                        차이: {}
                    </p>
                </div>
                """.format(
                    format_percent(win_rate_diff),
                    format_percent(train['win_rate']),
                    format_percent(test['win_rate']),
                    ('+' if comp['win_rate_diff'] > 0 else '') + format_percent(comp['win_rate_diff'])
                ), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <p style="color: #93c5fd; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.5rem;">2️⃣ 수익률 차이</p>
                    <p style="color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0.3rem 0;">{}</p>
                    <p style="color: #d1d5db; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                        Train: {} → Test: {}<br>
                        차이율: {} (절대값)
                    </p>
                </div>
                """.format(
                    format_percent(return_diff_pct),
                    format_percent(train['total_return']),
                    format_percent(test['total_return']),
                    format_percent(return_diff_pct)
                ), unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <p style="color: #fcd34d; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.5rem;">3️⃣ 낙폭 비율</p>
                    <p style="color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0.3rem 0;">{:.2f}배</p>
                    <p style="color: #d1d5db; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                        Train: {} → Test: {}<br>
                        Test ÷ Train = {:.2f}배
                    </p>
                </div>
                """.format(
                    dd_ratio,
                    format_percent(train['max_drawdown']),
                    format_percent(test['max_drawdown']),
                    dd_ratio
                ), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 판정 기준 설명 - 테이블 형식
            st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📋 판정 기준표</h4>', unsafe_allow_html=True)
            st.markdown('<p style="color: #9ca3af; font-size: 0.9rem; margin-top: -0.5rem;">각 지표별 우수/보통/위험 기준</p>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1.2rem; border-radius: 8px; border-left: 4px solid #10b981;">
                    <p style="color: #ffffff; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">✅ 승률 (Win Rate)</p>
                    <table style="width: 100%; color: #e5e7eb; font-size: 0.9rem; line-height: 1.6;">
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #6ee7b7; font-weight: 600;">🟢 우수</td>
                            <td style="padding: 0.5rem 0; text-align: right;">≤ 5%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #fcd34d; font-weight: 600;">🟡 보통</td>
                            <td style="padding: 0.5rem 0; text-align: right;">5~10%</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem 0; color: #fca5a5; font-weight: 600;">🔴 불안정</td>
                            <td style="padding: 0.5rem 0; text-align: right;">> 10%</td>
                        </tr>
                    </table>
                    <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 1rem; line-height: 1.5;">
                        차이가 클수록 과적합 가능성이 높으며, 실전에서 승률이 급락할 수 있습니다.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1.2rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <p style="color: #ffffff; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">✅ 수익률 (Return)</p>
                    <table style="width: 100%; color: #e5e7eb; font-size: 0.9rem; line-height: 1.6;">
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #6ee7b7; font-weight: 600;">🟢 우수</td>
                            <td style="padding: 0.5rem 0; text-align: right;">< 20%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #fcd34d; font-weight: 600;">🟡 보통</td>
                            <td style="padding: 0.5rem 0; text-align: right;">20~50%</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem 0; color: #fca5a5; font-weight: 600;">🔴 위험</td>
                            <td style="padding: 0.5rem 0; text-align: right;">≥ 50%</td>
                        </tr>
                    </table>
                    <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 1rem; line-height: 1.5;">
                        수익률 차이가 50% 이상이면 심각한 과적합으로 전략 재검토가 필요합니다.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #1e2330 0%, #181d28 100%); 
                            padding: 1.2rem; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <p style="color: #ffffff; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">✅ 최대낙폭 (Max DD)</p>
                    <table style="width: 100%; color: #e5e7eb; font-size: 0.9rem; line-height: 1.6;">
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #6ee7b7; font-weight: 600;">🟢 우수</td>
                            <td style="padding: 0.5rem 0; text-align: right;">< 2배</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #374151;">
                            <td style="padding: 0.5rem 0; color: #fcd34d; font-weight: 600;">🟡 보통</td>
                            <td style="padding: 0.5rem 0; text-align: right;">2~3배</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem 0; color: #fca5a5; font-weight: 600;">🔴 위험</td>
                            <td style="padding: 0.5rem 0; text-align: right;">≥ 3배</td>
                        </tr>
                    </table>
                    <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 1rem; line-height: 1.5;">
                        Test 낙폭이 Train의 3배 이상이면 리스크 관리 실패로 실전 투입 위험합니다.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 종합 해석
            st.markdown("### 💡 종합 해석")
            
            # 점수별 해석
            if score >= 80:
                st.markdown("""
                <div style="background: linear-gradient(120deg, #064e3b 0%, #047857 100%); 
                            padding: 1.5rem; border-radius: 10px; border-left: 5px solid #10b981;">
                    <p style="color: #ffffff; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;">
                        🎉 실전 투입 강력 추천
                    </p>
                    <ul style="color: #d1fae5; font-size: 1rem; line-height: 1.8; margin: 0; padding-left: 1.5rem;">
                        <li>Train과 Test 구간의 성과가 거의 동일합니다.</li>
                        <li>전략이 과적합되지 않았으며, 미래에도 안정적인 성과를 기대할 수 있습니다.</li>
                        <li>승률, 수익률, 리스크 모두 예측 가능한 범위 내에 있습니다.</li>
                        <li>실전 매매 시작을 적극 권장합니다.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            elif score >= 60:
                st.markdown("""
                <div style="background: linear-gradient(120deg, #78350f 0%, #b45309 100%); 
                            padding: 1.5rem; border-radius: 10px; border-left: 5px solid #f59e0b;">
                    <p style="color: #ffffff; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;">
                        ⚠️ 조건부 실전 투입
                    </p>
                    <ul style="color: #fef3c7; font-size: 1rem; line-height: 1.8; margin: 0; padding-left: 1.5rem;">
                        <li>Test 구간에서 일부 성과 저하가 관찰됩니다.</li>
                        <li>경미한 과적합 가능성이 있으나, 치명적인 수준은 아닙니다.</li>
                        <li>소액으로 실전 테스트를 시작하고, 성과를 모니터링하세요.</li>
                        <li>리스크 관리를 강화하고, 포지션 사이즈를 보수적으로 설정하세요.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: linear-gradient(120deg, #7f1d1d 0%, #b91c1c 100%); 
                            padding: 1.5rem; border-radius: 10px; border-left: 5px solid #ef4444;">
                    <p style="color: #ffffff; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;">
                        ❌ 전략 재검토 필요
                    </p>
                    <ul style="color: #fee2e2; font-size: 1rem; line-height: 1.8; margin: 0; padding-left: 1.5rem;">
                        <li>Test 구간에서 성과가 크게 하락했습니다.</li>
                        <li>전략이 Train 데이터에 과최적화되었을 가능성이 높습니다.</li>
                        <li>현재 상태로 실전 투입 시 예상과 다른 결과가 나올 수 있습니다.</li>
                        <li>전략 로직을 단순화하거나, 파라미터를 재조정하세요.</li>
                        <li>더 긴 기간의 데이터로 재검증이 필요합니다.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    def render_page_quantstats(self):
        """Quantstats 페이지"""
        st.header("📈 Quantstats 포트폴리오 분석")
        
        if st.session_state.converter is None:
            st.warning("⚠️ 먼저 CSV를 업로드하세요.")
            return
        
        # 분석 버튼
        if st.button("📊 Quantstats 분석 실행", type="primary", use_container_width=True):
            with st.spinner("Quantstats 분석 중..."):
                try:
                    # 일별 수익률 변환
                    returns = st.session_state.converter.to_daily_returns()
                    
                    if len(returns) == 0:
                        st.error("❌ 수익률 데이터가 비어있습니다.")
                        st.session_state.qs_metrics = None
                        st.stop()
                    
                    # Quantstats 분석
                    qs_analyzer = QuantstatsAnalyzer(returns)
                    metrics = qs_analyzer.get_metrics()
                    
                    # 에러 체크
                    if 'error' in metrics:
                        st.error(f"❌ Quantstats 분석 실패: {metrics['error']}")
                        if qs_analyzer.last_error:
                            st.code(qs_analyzer.last_error)
                        st.session_state.qs_metrics = None
                        st.stop()
                    
                    st.session_state.qs_metrics = metrics
                    
                except ImportError as e:
                    st.error("❌ Quantstats 미설치")
                    st.code("pip install quantstats ipython --break-system-packages")
                    st.session_state.qs_metrics = None
                except Exception as e:
                    st.error(f"❌ Quantstats 분석 실패: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.session_state.qs_metrics = None
        
        # 결과 표시
        if st.session_state.qs_metrics is not None:
            st.success("✅ Quantstats 분석 완료!")
            
            metrics = st.session_state.qs_metrics
            
            if not metrics:
                st.warning("⚠️ 지표를 가져올 수 없습니다.")
                return
            
            st.markdown("### 📊 핵심 지표")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cagr = metrics.get('cagr', 0)
                st.metric("CAGR", format_percent(cagr*100) if cagr else "N/A")
                sharpe = metrics.get('sharpe', 0)
                st.metric("Sharpe Ratio", f"{sharpe:,.2f}" if sharpe else "N/A")
            
            with col2:
                sortino = metrics.get('sortino', 0)
                st.metric("Sortino Ratio", f"{sortino:,.2f}" if sortino else "N/A")
                calmar = metrics.get('calmar', 0)
                st.metric("Calmar Ratio", f"{calmar:,.2f}" if calmar else "N/A")
            
            with col3:
                max_dd = metrics.get('max_drawdown', 0)
                st.metric("Max Drawdown", format_percent(max_dd*100) if max_dd else "N/A")
                vol = metrics.get('volatility', 0)
                st.metric("Volatility", format_percent(vol*100) if vol else "N/A")
            
            with col4:
                var = metrics.get('var', 0)
                st.metric("VaR (95%)", format_percent(var*100) if var else "N/A")
                cvar = metrics.get('cvar', 0)
                st.metric("CVaR (95%)", format_percent(cvar*100) if cvar else "N/A")
            
            st.markdown("---")
            
            st.markdown("### 🎯 고급 지표")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                risk_of_ruin = metrics.get('risk_of_ruin', 0)
                if risk_of_ruin is not None and risk_of_ruin > 0:
                    st.metric("파산 확률", format_percent(risk_of_ruin*100))
                    st.markdown('<p class="caption-text">💡 0%에 가까울수록 안전</p>', unsafe_allow_html=True)
                else:
                    st.metric("파산 확률", "0.00%")
                    st.markdown('<p class="caption-text">✅ 파산 위험 거의 없음</p>', unsafe_allow_html=True)
            
            with col2:
                ulcer = metrics.get('ulcer_index', 0)
                st.metric("Ulcer Index", f"{ulcer:,.2f}" if ulcer else "N/A")
                st.markdown('<p class="caption-text">💡 낮을수록 좋음</p>', unsafe_allow_html=True)
            
            with col3:
                gain_pain = metrics.get('gain_pain_ratio', 0)
                st.metric("Gain/Pain Ratio", f"{gain_pain:,.2f}" if gain_pain else "N/A")
                st.markdown('<p class="caption-text">💡 높을수록 좋음</p>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 지표 해석 가이드
            st.markdown("""
            <div class="guide-box">
                <strong>📊 지표 해석 가이드</strong><br><br>
                • <strong>Sharpe Ratio</strong>: > 2.0 우수 | 1.0~2.0 양호 | < 1.0 개선 필요<br>
                • <strong>Max Drawdown</strong>: < 20% 우수 | 20~30% 양호 | > 30% 위험<br>
                • <strong>Ulcer Index</strong>: < 5 우수 | 5~10 양호 | > 10 높은 스트레스<br>
                • <strong>Gain/Pain Ratio</strong>: > 3.0 우수 | 1.0~3.0 양호 | < 1.0 개선 필요
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 위의 '📊 Quantstats 분석 실행' 버튼을 클릭하세요.")
    
    def render_page_loss(self):
        """손실 분석 페이지"""
        from analysis.loss_analysis_enhanced import render_page_loss_enhanced
        render_page_loss_enhanced(st.session_state.converter)

    def render_page_profit(self):
        """수익 분석 페이지"""
        from analysis.profit_analysis_enhanced import render_page_profit_enhanced
        render_page_profit_enhanced(st.session_state.converter)
    
    def render_page_rolling_walkforward(self):
        """Rolling Walk-Forward 페이지"""
        st.header("🔄 Rolling Walk-Forward 분석 (고급)")
        
        st.markdown("""
        <div style="background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 100%); 
                    padding: 1.2rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <p style="color: #ffffff; font-size: 1rem; line-height: 1.7; margin: 0;">
                <strong style="font-size: 1.1rem;">💡 Rolling Walk-Forward란?</strong><br><br>
                • 단일 Train/Test 분할이 아닌 <strong>여러 Window로 검증</strong><br>
                • 모든 구간에서 과적합 여부를 철저히 테스트<br>
                • 신뢰도가 일반 Walk-Forward 대비 <strong>3~5배 높음</strong><br>
                • <strong>실전 자본 투입 전 필수 검증</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.converter is None:
            st.warning("⚠️ 먼저 CSV를 업로드하세요.")
            return
        
        # Window 수 선택
        st.markdown("### ⚙️ 분석 설정")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            num_windows = st.selectbox(
                "Window 수 선택",
                [3, 4, 5],
                index=0,
                help="많을수록 신뢰도 높음, 3개 권장"
            )
        
        with col2:
            st.info(f"💡 **{num_windows}개 Window**로 검증 → 신뢰도 {'⭐' * (num_windows + 2)}")
        
        # 분석 버튼
        if st.button("🚀 Rolling Walk-Forward 분석 실행", type="primary", use_container_width=True):
            with st.spinner(f"🔄 {num_windows}개 Window 분석 중..."):
                trades = st.session_state.converter.trades
                results = self.perform_rolling_walkforward(trades, num_windows)
                st.session_state.rolling_wf_results = results
        
        # 결과 표시
        if st.session_state.rolling_wf_results is not None:
            results = st.session_state.rolling_wf_results
            
            st.markdown("---")
            
            # 종합 점수
            avg_score = results['avg_score']
            
            if avg_score >= 80:
                st.markdown(f'<div class="success-box"><h3>✅ 평균 과적합 점수: {format_number(avg_score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            elif avg_score >= 60:
                st.markdown(f'<div class="warning-box"><h3>⚠️ 평균 과적합 점수: {format_number(avg_score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="danger-box"><h3>❌ 평균 과적합 점수: {format_number(avg_score)}점</h3><p>{results["final_judgment"]}</p></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 통계 요약
            st.markdown("### 📈 통계 요약")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("평균 점수", f"{format_number(results['avg_score'])}점")
            
            with col2:
                consistency_emoji = "✅" if results['consistency_class'] == "success" else "⚠️" if results['consistency_class'] == "warning" else "❌"
                st.metric("일관성", f"{consistency_emoji} {results['consistency']}")
                st.markdown(f'<p class="caption-text">편차: {results["score_std"]:.1f}점</p>', unsafe_allow_html=True)
            
            with col3:
                st.metric("최고 점수", f"{format_number(results['max_score'])}점")
            
            with col4:
                st.metric("최저 점수", f"{format_number(results['min_score'])}점")
            
            st.markdown("---")
            
            # 각 Window 결과
            st.markdown("### 🪟 Window별 상세 결과")
            
            for window in results['window_results']:
                score = window['overfit_score']
                
                if score >= 80:
                    badge = "✅ 우수"
                    color = "#10b981"
                elif score >= 60:
                    badge = "⚠️ 보통"
                    color = "#f59e0b"
                else:
                    badge = "❌ 위험"
                    color = "#ef4444"
                
                with st.expander(f"**Window {window['window_num']}: {format_number(score)}점** {badge}", expanded=(window['window_num'] == 1)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**📈 Train 구간** `거래 {window['train_range']}`")
                        train = window['train_metrics']
                        st.metric("거래 수", f"{format_number(train['total_trades'])}건")
                        st.metric("승률", format_percent(train['win_rate']))
                        st.metric("총 수익률", format_percent(train['total_return']))
                        st.metric("최대 낙폭", format_percent(train['max_drawdown']))
                    
                    with col2:
                        st.markdown(f"**📉 Test 구간** `거래 {window['test_range']}`")
                        test = window['test_metrics']
                        st.metric("거래 수", f"{format_number(test['total_trades'])}건")
                        st.metric("승률", format_percent(test['win_rate']))
                        st.metric("총 수익률", format_percent(test['total_return']))
                        st.metric("최대 낙폭", format_percent(test['max_drawdown']))
                    
                    # 판정 상세
                    st.markdown("**🎯 판정 상세**")
                    for key, judgment in window['judgments'].items():
                        st.markdown(f"• **{key}**: {judgment}")
    
    def perform_rolling_walkforward(self, trades, num_windows):
        """Rolling Walk-Forward 분석 수행"""
        total_trades = len(trades)
        window_results = []
        
        # Window 비율 설정
        if num_windows == 3:
            train_ratios = [0.70, 0.80, 0.90]
        elif num_windows == 4:
            train_ratios = [0.65, 0.75, 0.85, 0.92]
        else:  # 5
            train_ratios = [0.60, 0.70, 0.80, 0.90, 0.95]
        
        # 각 Window 분석
        for i, train_ratio in enumerate(train_ratios):
            train_end = int(total_trades * train_ratio)
            
            if i < len(train_ratios) - 1:
                test_end = int(total_trades * train_ratios[i + 1])
            else:
                test_end = total_trades
            
            # Train/Test 분할
            train_trades = trades.iloc[:train_end].copy()
            test_trades = trades.iloc[train_end:test_end].copy()
            
            # 분석
            combined = pd.concat([train_trades, test_trades])
            wf = WalkForwardAnalyzer(combined, train_ratio=len(train_trades)/len(combined))
            window_result = wf.analyze()
            window_result['window_num'] = i + 1
            window_result['train_range'] = f"1~{train_end}"
            window_result['test_range'] = f"{train_end+1}~{test_end}"
            
            window_results.append(window_result)
        
        # 통합 결과 계산
        avg_score = sum(r['overfit_score'] for r in window_results) / len(window_results)
        scores = [r['overfit_score'] for r in window_results]
        score_std = np.std(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # 일관성 판정
        if score_std < 5:
            consistency = "매우 높음"
            consistency_class = "success"
        elif score_std < 10:
            consistency = "높음"
            consistency_class = "success"
        elif score_std < 15:
            consistency = "보통"
            consistency_class = "warning"
        else:
            consistency = "낮음"
            consistency_class = "danger"
        
        # 최종 판정
        if avg_score >= 80 and min_score >= 70:
            final_judgment = "실전 투입 강력 추천 (모든 Window 우수)"
        elif avg_score >= 70 and min_score >= 60:
            final_judgment = "조건부 실전 투입 (대체로 양호)"
        elif avg_score >= 60:
            final_judgment = "신중한 접근 필요 (Window간 편차 존재)"
        else:
            final_judgment = "전략 재검토 필요 (과적합 위험)"
        
        return {
            'num_windows': num_windows,
            'window_results': window_results,
            'avg_score': avg_score,
            'score_std': score_std,
            'min_score': min_score,
            'max_score': max_score,
            'consistency': consistency,
            'consistency_class': consistency_class,
            'final_judgment': final_judgment
        }
    
    def render_page_summary(self):
        """종합 평가 페이지"""
        st.header("🎯 종합 평가 및 실전 투입 판정")
        
        if st.session_state.converter is None:
            st.warning("⚠️ 먼저 CSV를 업로드하고 분석을 실행하세요.")
            return
        
        # ========== 🎉 전체 분석 완료 안내 ==========
        st.markdown("""
        <div style="background: linear-gradient(120deg, #064e3b 0%, #047857 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <h3 style="color: #ffffff; margin: 0 0 1rem 0;">🎉 전체 분석 완료!</h3>
            <p style="color: #d1fae5; margin: 0; line-height: 1.6;">
                CSV 업로드 시 자동으로 실행된 모든 분석 결과를 확인하세요.<br>
                • Walk-Forward 검증 ✅<br>
                • Quantstats 포트폴리오 분석 ✅<br>
                • 16개 종합 검증 시스템 ✅
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 기본 통계
        stats = st.session_state.converter.get_statistics()
        
        # ========== 📊 1. 전략 성과 요약 ==========
        st.markdown("### 📊 1. 전략 성과 요약")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 거래", f"{format_number(stats['total_trades'])}건")
            st.metric("기간", f"{format_number(stats['period_days'])}일")
        
        with col2:
            st.metric("승률", format_percent(stats['win_rate']))
            st.metric("수익 거래", f"{format_number(stats['winning_trades'])}건")
        
        with col3:
            st.metric("총 수익률", format_percent(stats['total_return']))
            st.metric("평균 수익", format_percent(stats['avg_return']))
        
        with col4:
            st.metric("평균 승", format_percent(stats['avg_win']))
            st.metric("평균 패", format_percent(stats['avg_loss']))
        
        st.markdown("---")
        
        # ========== 📈 2. Walk-Forward 검증 결과 ==========
        st.markdown("### 📈 2. Walk-Forward 과적합 검증")
        
        if st.session_state.wf_results:
            wf_results = st.session_state.wf_results
            wf_score = wf_results['overfit_score']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if wf_score >= 80:
                    st.metric("과적합 점수", f"{format_number(wf_score)}점", delta="✅ 우수", delta_color="normal")
                elif wf_score >= 60:
                    st.metric("과적합 점수", f"{format_number(wf_score)}점", delta="⚠️ 보통", delta_color="off")
                else:
                    st.metric("과적합 점수", f"{format_number(wf_score)}점", delta="❌ 위험", delta_color="inverse")
            
            with col2:
                train = wf_results['train_metrics']
                st.metric("Train 승률", format_percent(train['win_rate']))
            
            with col3:
                test = wf_results['test_metrics']
                st.metric("Test 승률", format_percent(test['win_rate']))
            
            with col4:
                comp = wf_results['comparison']
                win_rate_diff = comp['win_rate_diff']
                st.metric("승률 차이", format_percent(abs(win_rate_diff)))
            
            # 최종 판정
            final_judgment = wf_results['final_judgment']
            if wf_score >= 80:
                st.success(f"✅ {final_judgment}")
            elif wf_score >= 60:
                st.warning(f"⚠️ {final_judgment}")
            else:
                st.error(f"❌ {final_judgment}")
        else:
            st.warning("⚠️ Walk-Forward 분석 결과 없음 (CSV를 다시 업로드하세요)")
        
        st.markdown("---")
        
        # ========== 📊 3. Quantstats 포트폴리오 분석 ==========
        st.markdown("### 📊 3. Quantstats 포트폴리오 분석")
        
        if st.session_state.qs_metrics:
            metrics = st.session_state.qs_metrics
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cagr = metrics.get('cagr', 0)
                st.metric("CAGR", format_percent(cagr*100) if cagr else "N/A")
            
            with col2:
                sharpe = metrics.get('sharpe', 0)
                if sharpe >= 2.0:
                    st.metric("Sharpe Ratio", f"{sharpe:,.2f}", delta="✅ 우수", delta_color="normal")
                elif sharpe >= 1.0:
                    st.metric("Sharpe Ratio", f"{sharpe:,.2f}", delta="⚠️ 양호", delta_color="off")
                else:
                    st.metric("Sharpe Ratio", f"{sharpe:,.2f}", delta="❌ 개선 필요", delta_color="inverse")
            
            with col3:
                max_dd = metrics.get('max_drawdown', 0)
                st.metric("Max Drawdown", format_percent(max_dd*100) if max_dd else "N/A")
            
            with col4:
                sortino = metrics.get('sortino', 0)
                st.metric("Sortino Ratio", f"{sortino:,.2f}" if sortino else "N/A")
            
            # 추가 지표
            col1, col2, col3 = st.columns(3)
            
            with col1:
                calmar = metrics.get('calmar', 0)
                st.metric("Calmar Ratio", f"{calmar:,.2f}" if calmar else "N/A")
            
            with col2:
                var = metrics.get('var', 0)
                st.metric("VaR (95%)", format_percent(var*100) if var else "N/A")
            
            with col3:
                risk_of_ruin = metrics.get('risk_of_ruin', 0)
                if risk_of_ruin is not None and risk_of_ruin > 0:
                    st.metric("파산 확률", format_percent(risk_of_ruin*100))
                else:
                    st.metric("파산 확률", "0.00%")
        else:
            st.warning("⚠️ Quantstats 분석 결과 없음 (CSV를 다시 업로드하세요)")
        
        st.markdown("---")
        
        # ========== 🔬 4. 16개 종합 검증 시스템 ==========
        st.markdown("### 🔬 4. 16개 종합 검증 시스템")
        
        if 'validators_16_report' in st.session_state and st.session_state.validators_16_report:
            report = st.session_state.validators_16_report
            final_score = report['final_score']
            disq = report['disqualification']
            
            # 메트릭
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                score_val = final_score['final_score']
                if score_val >= 80:
                    st.metric("최종 점수", f"{score_val:.1f}점", delta="✅ 우수", delta_color="normal")
                elif score_val >= 60:
                    st.metric("최종 점수", f"{score_val:.1f}점", delta="⚠️ 보통", delta_color="off")
                else:
                    st.metric("최종 점수", f"{score_val:.1f}점", delta="❌ 개선 필요", delta_color="inverse")
            
            with col2:
                rating = final_score['rating']
                st.metric("등급", rating)
            
            with col3:
                tier = disq['tier']
                st.metric("검증 기준", tier)
            
            with col4:
                wr = disq.get('win_rate', 0)
                st.metric("검증 승률", f"{wr:.1f}%")
            
            # 자동매매 판정
            st.markdown("**🎯 자동매매 판정**")
            
            if "❌" in disq['status']:
                st.error(disq['status'])
                if disq['reasons']:
                    st.error("**실격 사유:**\n" + "\n".join([f"- {r}" for r in disq['reasons']]))
            elif "⚠️" in disq['status']:
                st.warning(disq['status'])
            else:
                st.success(disq['status'])
            
            # 카테고리별 점수 (간단 버전)
            with st.expander("📊 카테고리별 점수 상세"):
                scores_df = pd.DataFrame(
                    list(final_score['scores'].items()),
                    columns=['카테고리', '점수']
                )
                scores_df['점수'] = scores_df['점수'].round(1)
                st.dataframe(scores_df, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ 16개 검증 결과 없음 (CSV를 다시 업로드하세요)")
        
        st.markdown("---")
        
        # ========== 🎯 5. 최종 실전 투입 판정 ==========
        st.markdown("### 🎯 5. 최종 실전 투입 판정")
        
        # 16개 검증 결과 반영
        validators_passed = True
        validators_score = 0
        
        if 'validators_16_report' in st.session_state and st.session_state.validators_16_report:
            disq_status = st.session_state.validators_16_report['disqualification']['status']
            validators_score = st.session_state.validators_16_report['final_score']['final_score']
            
            if "❌" in disq_status:
                validators_passed = False
        
        # Walk-Forward 결과 반영
        wf_passed = True
        wf_score_val = 0
        
        if st.session_state.wf_results:
            wf_score_val = st.session_state.wf_results['overfit_score']
            if wf_score_val < 60:
                wf_passed = False
        
        # Quantstats 결과 반영
        qs_passed = True
        sharpe_val = 0
        
        if st.session_state.qs_metrics:
            sharpe_val = st.session_state.qs_metrics.get('sharpe', 0)
            if sharpe_val < 1.0:
                qs_passed = False
        
        # 종합 판정 테이블
        st.markdown("**📋 검증 항목별 판정**")
        
        judgment_data = {
            "검증 항목": [
                "기본 성과 (승률 ≥ 80%, 수익률 ≥ 40%)",
                "Walk-Forward 과적합 검증 (≥ 60점)",
                "Quantstats Sharpe Ratio (≥ 1.0)",
                "16개 종합 검증 시스템 (실격 없음)"
            ],
            "목표": [
                f"승률 {stats['win_rate']:.1f}% / 수익률 {stats['total_return']:.1f}%",
                f"{wf_score_val:.1f}점",
                f"{sharpe_val:.2f}",
                f"{validators_score:.1f}점"
            ],
            "판정": [
                "✅ 통과" if stats['win_rate'] >= 80 and stats['total_return'] >= 40 else "❌ 미달",
                "✅ 통과" if wf_passed else "❌ 미달",
                "✅ 통과" if qs_passed else "❌ 미달",
                "✅ 통과" if validators_passed else "❌ 실격"
            ]
        }
        
        judgment_df = pd.DataFrame(judgment_data)
        st.dataframe(judgment_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 최종 판정 박스
        all_passed = (
            stats['win_rate'] >= 80 and 
            stats['total_return'] >= 40 and 
            validators_passed and 
            wf_passed and 
            qs_passed
        )
        
        partial_passed = (
            stats['win_rate'] >= 70 and 
            stats['total_return'] >= 30 and 
            validators_passed and 
            wf_score_val >= 60
        )
        
        if all_passed:
            st.markdown("""
            <div class="success-box">
                <h3>✅ 실전 투입 강력 추천</h3>
                <p><strong>모든 검증 항목 통과!</strong></p>
                <ul style="margin: 0.5rem 0 0 1.5rem; line-height: 1.8;">
                    <li>승률 80% 이상, 수익률 40% 이상 달성</li>
                    <li>Walk-Forward 과적합 검증 통과</li>
                    <li>Quantstats 포트폴리오 지표 양호</li>
                    <li>16개 종합 검증 시스템 통과</li>
                </ul>
                <p style="margin-top: 1rem; font-weight: 600;">
                    💡 실전 자동매매 투입을 권장합니다. 초기 자본금 $50로 시작하세요.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            final_judgment = "✅ 실전 투입 강력 추천"
            judgment_reason = "모든 검증 항목 통과"
            
        elif partial_passed:
            st.markdown("""
            <div class="warning-box">
                <h3>⚠️ 조건부 실전 투입</h3>
                <p><strong>기본 목표에 근접했으나 일부 항목 미달</strong></p>
                <ul style="margin: 0.5rem 0 0 1.5rem; line-height: 1.8;">
                    <li>승률 70% 이상, 수익률 30% 이상 달성</li>
                    <li>주요 검증은 통과했으나 완벽하지 않음</li>
                </ul>
                <p style="margin-top: 1rem; font-weight: 600;">
                    💡 소액($50)으로 실전 테스트를 시작하고, 성과를 면밀히 모니터링하세요.<br>
                    리스크 관리를 강화하고, 포지션 사이즈를 보수적으로 설정하세요.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            final_judgment = "⚠️ 조건부 실전 투입"
            judgment_reason = "목표 근접 - 소액 테스트 권장"
            
        else:
            # 실패 사유 수집
            fail_reasons = []
            
            if stats['win_rate'] < 70 or stats['total_return'] < 30:
                fail_reasons.append(f"기본 성과 미달 (승률 {stats['win_rate']:.1f}%, 수익률 {stats['total_return']:.1f}%)")
            
            if not validators_passed:
                fail_reasons.append("16개 검증 시스템 실격")
            
            if not wf_passed:
                fail_reasons.append(f"Walk-Forward 과적합 위험 ({wf_score_val:.1f}점)")
            
            if not qs_passed:
                fail_reasons.append(f"Sharpe Ratio 낮음 ({sharpe_val:.2f})")
            
            fail_text = "<br>".join([f"• {r}" for r in fail_reasons])
            
            st.markdown(f"""
            <div class="danger-box">
                <h3>❌ 추가 최적화 필요</h3>
                <p><strong>다음 항목에서 문제 발견:</strong></p>
                <p style="margin: 0.5rem 0 0 1rem; line-height: 1.8;">
                    {fail_text}
                </p>
                <p style="margin-top: 1rem; font-weight: 600;">
                    💡 전략 로직을 재검토하고, 파라미터를 재조정하세요.<br>
                    더 긴 기간의 데이터로 재검증이 필요합니다.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            final_judgment = "❌ 추가 최적화 필요"
            judgment_reason = " | ".join(fail_reasons)
        
        st.markdown("---")
        
        # ========== 📥 6. 분석 결과 다운로드 ==========
        st.markdown("### 📥 6. 분석 결과 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 100%); 
                        padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;">
                <p style="color: #ffffff; font-size: 0.95rem; margin: 0; line-height: 1.6;">
                    <strong>📄 HTML 리포트</strong><br><br>
                    • 전략 요약 및 상세 통계<br>
                    • 모든 검증 결과<br>
                    • 실전 투입 판정<br><br>
                    💡 브라우저로 확인 후 Ctrl+P로 PDF 저장
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # HTML 리포트 다운로드
            html_content = self.generate_html_report()
            
            st.download_button(
                label="📄 HTML 리포트 다운로드",
                data=html_content,
                file_name=f"Phoenix_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 100%); 
                        padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem;">
                <p style="color: #ffffff; font-size: 0.95rem; margin: 0; line-height: 1.6;">
                    <strong>📦 통합 JSON</strong><br><br>
                    • 모든 분석 결과 통합<br>
                    • 전략 DB 업로드용<br>
                    • 프로그래밍 방식 처리 가능<br><br>
                    💡 전략명 입력 후 다운로드
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            strategy_name = st.text_input(
                "전략명 입력",
                placeholder="예: Phoenix_KAMA_V2.0",
                key="strategy_name_final",
                label_visibility="collapsed"
            )
            
            if strategy_name:
                # 통합 결과 생성
                import json
                
                combined_result = {
                    "strategy_name": strategy_name,
                    "timestamp": datetime.now().isoformat(),
                    "basic_stats": stats,
                    "walk_forward": st.session_state.wf_results if st.session_state.wf_results else {},
                    "quantstats": st.session_state.qs_metrics if st.session_state.qs_metrics else {},
                    "validators_16": st.session_state.validators_16_report if st.session_state.validators_16_report else {},
                    "final_evaluation": {
                        "judgment": final_judgment,
                        "reason": judgment_reason,
                        "all_passed": all_passed,
                        "validators_passed": validators_passed,
                        "wf_passed": wf_passed,
                        "qs_passed": qs_passed,
                        "meets_target": stats['win_rate'] >= 80 and stats['total_return'] >= 40
                    }
                }
                
                # JSON 다운로드 버튼
                json_str = json.dumps(combined_result, default=str, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label=f"📦 {strategy_name} JSON 다운로드",
                    data=json_str,
                    file_name=f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                
                # 미리보기
                with st.expander("📋 JSON 미리보기"):
                    st.code(json_str, language="json")
            else:
                st.info("💡 전략명을 입력하세요")

    
    def generate_html_report(self):
        """HTML 리포트 생성"""
        # session_state에서 가져오기
        if st.session_state.converter is None:
            return "<html><body><h1>데이터가 없습니다. CSV를 먼저 업로드하세요.</h1></body></html>"
        
        stats = st.session_state.converter.get_statistics()
        
        # Walk-Forward 결과
        wf_results = st.session_state.wf_results if st.session_state.wf_results else {}
        wf_score = wf_results.get('overfit_score', 0) if wf_results else 0
        
        # Quantstats 결과
        qs_metrics = st.session_state.qs_metrics if st.session_state.qs_metrics else {}
        sharpe = qs_metrics.get('sharpe', 0) if qs_metrics else 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Phoenix Strategy Analyzer - 종합 리포트</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 40px;
                    background: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #ff6b35;
                    border-bottom: 3px solid #ff6b35;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #2c3e50;
                    margin-top: 30px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 20px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3b82f6;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    color: #6b7280;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #1f2937;
                }}
                .status-box {{
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .status-success {{
                    background: #d1fae5;
                    border-left: 5px solid #10b981;
                }}
                .status-warning {{
                    background: #fef3c7;
                    border-left: 5px solid #f59e0b;
                }}
                .status-danger {{
                    background: #fee2e2;
                    border-left: 5px solid #ef4444;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e5e7eb;
                }}
                th {{
                    background: #3b82f6;
                    color: white;
                    font-weight: 600;
                }}
                tr:hover {{
                    background: #f9fafb;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔥 Phoenix Strategy Analyzer - 종합 리포트</h1>
                <p style="color: #6b7280;">생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>📊 기본 통계</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-label">총 거래</div>
                        <div class="metric-value">{stats['total_trades']:,}건</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">승률</div>
                        <div class="metric-value">{stats['win_rate']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">총 수익률</div>
                        <div class="metric-value">{stats['total_return']:,.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">기간</div>
                        <div class="metric-value">{stats['period_days']:,}일</div>
                    </div>
                </div>
                
                <h2>📈 상세 통계</h2>
                <table>
                    <tr>
                        <th>항목</th>
                        <th>값</th>
                    </tr>
                    <tr>
                        <td>수익 거래</td>
                        <td>{stats['winning_trades']:,}건</td>
                    </tr>
                    <tr>
                        <td>손실 거래</td>
                        <td>{stats['losing_trades']:,}건</td>
                    </tr>
                    <tr>
                        <td>평균 수익</td>
                        <td>{stats['avg_win']:.2f}%</td>
                    </tr>
                    <tr>
                        <td>평균 손실</td>
                        <td>{stats['avg_loss']:.2f}%</td>
                    </tr>
                    <tr>
                        <td>최대 낙폭</td>
                        <td>{stats['max_drawdown']:.2f}%</td>
                    </tr>
                </table>
                
                <h2>📊 검증 결과</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-label">Walk-Forward 점수</div>
                        <div class="metric-value">{wf_score:.1f}점</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Sharpe Ratio</div>
                        <div class="metric-value">{sharpe:.2f}</div>
                    </div>
                </div>
                
                <h2>🎯 실전 투입 판정</h2>
                <div class="status-box {'status-success' if stats['win_rate'] >= 80 and stats['total_return'] >= 40 else 'status-warning' if stats['win_rate'] >= 70 else 'status-danger'}">
                    <h3>{'✅ 실전 투입 강력 추천' if stats['win_rate'] >= 80 and stats['total_return'] >= 40 else '⚠️ 조건부 실전 투입' if stats['win_rate'] >= 70 else '❌ 추가 최적화 필요'}</h3>
                    <p>
                        {'목표 달성: 승률 80% 이상, 수익률 40% 이상' if stats['win_rate'] >= 80 and stats['total_return'] >= 40 else '목표에 근접: 소액으로 테스트 권장' if stats['win_rate'] >= 70 else '목표 미달: 전략 재검토 필요'}
                    </p>
                </div>
                
                <div class="footer">
                    <p>🔥 Phoenix Strategy Analyzer v4.0</p>
                    <p>백테스트 → Walk-Forward → Quantstats → 16개 검증 통합</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_pdf_report(self):
        """PDF 리포트 생성"""
        # PDF 생성 로직 (기존과 동일)
        from weasyprint import HTML
        html_content = self.generate_html_report()
        return HTML(string=html_content).write_pdf()
    
    def render_page_16_validators(self):
        """16개 검증 시스템 페이지"""
        st.header("🔬 16개 종합 검증 시스템")
        
        st.markdown("""
        <div style="background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <p style="color: #ffffff; font-size: 1rem; line-height: 1.7; margin: 0;">
                <strong style="font-size: 1.1rem;">🔬 16개 종합 검증이란?</strong><br><br>
                Walk-Forward 검증을 넘어 <strong>체계적인 통계 분석</strong>을 통해<br>
                전략의 안정성, 신뢰도, 실전 생존성을 <strong>16개 차원</strong>에서 검증합니다.<br><br>
                • <strong>시계열 분석</strong> (5개): 월별/거래 연속성/보유기간<br>
                • <strong>통계 검정</strong> (4개): 승률 신뢰도/수익성/분포/꼬리 리스크<br>
                • <strong>거래 분석</strong> (2개): 승/패 비교/특성 분류<br>
                • <strong>극한 상황</strong> (5개): 50달러 생존성/부트스트랩/극단값<br>
                • <strong>포지션 최적화</strong> (3개): Sharpe/Kelly/동적 로트<br>
                • <strong>고급 통계</strong> (3개): 기울기/자기상관/이분산성<br>
                • <strong>종합평가</strong> (1개): 최종 판정 및 GO/NO-GO<br><br>
                <strong style="color: #fbbf24;">⚡ CSV 업로드 시 자동으로 실행됩니다!</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.session_state.converter is None:
            st.warning("⚠️ 먼저 CSV를 업로드하세요.")
            return
        
        # 16개 검증 버튼 제거! (자동 실행되므로)
        
        # 결과 표시
        if st.session_state.validators_16_report is not None:
            report = st.session_state.validators_16_report
            
            st.success("✅ 16개 검증 완료! (CSV 업로드 시 자동 실행됨)")
            
            st.markdown("---")
            st.markdown("### 📊 검증 결과 요약")
            
            disq = report['disqualification']
            final_score = report['final_score']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("승률", f"{disq.get('win_rate', 0):.1f}%")
            with col2:
                st.metric("최종 점수", f"{final_score['final_score']:.1f}점")
            with col3:
                st.metric("등급", final_score['rating'])
            with col4:
                st.metric("판정", disq['status'])
            
            st.markdown("---")
            st.markdown("### 🎯 자동매매 판정")
            
            if "❌" in disq['status']:
                st.error(disq['status'])
                if disq['reasons']:
                    st.error("**이유:**\n" + "\n".join([f"- {r}" for r in disq['reasons']]))
            elif "⚠️" in disq['status']:
                st.warning(disq['status'])
            else:
                st.success(disq['status'])
            
            st.markdown("---")
            st.markdown("### 📈 카테고리별 점수")
            
            scores_df = pd.DataFrame(
                list(final_score['scores'].items()),
                columns=['카테고리', '점수']
            )
            
            # Plotly 가로 바 차트
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(
                    y=scores_df['카테고리'],
                    x=scores_df['점수'],
                    orientation='h',
                    marker=dict(
                        color=scores_df['점수'],
                        colorscale='RdYlGn',
                        showscale=False,
                        line=dict(color='#ffffff', width=1)
                    ),
                    text=scores_df['점수'].round(1),
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>점수: %{x:.1f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(
                    text='<b>16개 검증 카테고리별 점수</b>',
                    font=dict(size=18, color='#ffffff')
                ),
                xaxis=dict(
                    title='점수',
                    title_font=dict(size=14, color='#e2e8f0'),
                    tickfont=dict(size=12, color='#cbd5e1'),
                    gridcolor='#334155',
                    zeroline=False,
                    range=[0, 105]
                ),
                yaxis=dict(
                    title='',
                    tickfont=dict(size=12, color='#e2e8f0'),
                ),
                plot_bgcolor='#0f172a',
                paper_bgcolor='#0f172a',
                margin=dict(l=200, r=100, t=80, b=60),
                height=500,
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ 16개 검증 결과가 없습니다.")
            st.info("💡 CSV를 다시 업로드하면 자동으로 실행됩니다.")
    
    def run(self):
        """대시보드 실행"""
        # 사이드바
        self.render_sidebar()
        
        # 헤더
        self.render_header()
        
        # 선택된 페이지 렌더링
        if st.session_state.current_page == "📤 CSV 업로드":
            self.render_page_upload()
        elif st.session_state.current_page == "📊 Walk-Forward":
            self.render_page_walkforward()
        elif st.session_state.current_page == "🔄 Rolling WF (고급)":
            self.render_page_rolling_walkforward()
        elif st.session_state.current_page == "📈 Quantstats":
            self.render_page_quantstats()
        elif st.session_state.current_page == "📉 손실 분석":
            self.render_page_loss()
        elif st.session_state.current_page == "💰 수익 분석":
            self.render_page_profit()
        elif st.session_state.current_page == "🔬 16개 검증":
            self.render_page_16_validators()
        elif st.session_state.current_page == "🎯 종합 평가":
            self.render_page_summary()

        
        # 푸터
        st.markdown("""
        <div class="footer">
            🔥 Phoenix Strategy Analyzer v4.0<br>
            백테스트 분석 → Walk-Forward 검증 → Quantstats 평가 → 16개 검증 시스템
        </div>
        """, unsafe_allow_html=True)


# 메인 실행
if __name__ == "__main__":
    dashboard = EnhancedDashboard()
    dashboard.run()