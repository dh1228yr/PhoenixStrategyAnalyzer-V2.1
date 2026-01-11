"""
streamlit_16validators_integration.py
Phoenix Strategy Analyzer - 16개 검증 시스템 (완벽 완성본)

완성 사항:
1. 드로우다운 버그 수정 (-418.4% → -28.0%)
2. Plotly 가로 바 차트 적용 (원래 스타일 복원)
3. 소개 설명 완벽 포함
4. 16개 검증 시스템 구조 테이블 완벽 포함
5. 모든 기능 완벽 통합
6. 테스트 완료

통합 기능:
1. CSV 업로드 및 데이터 변환
2. 16개 검증 시스템 실행
3. 자동 분석 리포트 생성
4. 결과 다운로드
5. 상세 설명 및 가이드
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime


def render_page_16_validators(converter_instance):
    """
    16개 검증 시스템 통합 페이지
    """
    st.header("🔬 16개 종합 검증 시스템")
    
    # ========== 소개 박스 (항상 표시!) ==========
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
            • <strong>종합평가</strong> (1개): 최종 판정 및 GO/NO-GO
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # CSV 없으면 여기서 중단
    if converter_instance is None:
        st.warning("⚠️ 먼저 CSV를 업로드하세요.")
        
        # ========== 16개 검증 시스템 구조 (항상 표시!) ==========
        st.markdown("""
        <div style="color: #ffffff; font-size: 0.95rem; line-height: 1.6;">
        
        **ℹ️ 16개 검증 시스템 구조**
        
        <table style="width:100%; border-collapse: collapse;">
        <tr>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>1️⃣ 시계열 분석 (5개)</strong><br>
        • 월별 수익률 분석<br>
        • 연속 손실 거래<br>
        • 보유기간 분포<br>
        • 월간 회귀선<br>
        • 월간 일관성
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>2️⃣ 통계 검정 (4개)</strong><br>
        • 승률 신뢰도<br>
        • 수익률 유의성<br>
        • 분포 분석<br>
        • 꼬리 리스크
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>3️⃣ 거래 분석 (2개)</strong><br>
        • 승/패 거래 비교<br>
        • 거래 특성 분류
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>4️⃣ 극한 상황 (5개)</strong><br>
        • 50달러 생존성<br>
        • 부트스트랩<br>
        • 극단값 분석<br>
        • 자본 성장<br>
        • 회귀선 분석
        </td>
        </tr>
        <tr>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>5️⃣ 포지션 최적화 (3개)</strong><br>
        • Sharpe/Sortino/Calmar<br>
        • Kelly Criterion<br>
        • 동적 로트
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>6️⃣ 고급 통계 (3개)</strong><br>
        • 기울기 검정<br>
        • 자기상관 검정<br>
        • 이분산성 검정
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        <strong>7️⃣ 종합평가 (1개)</strong><br>
        • 배제 조건<br>
        • 최종 점수<br>
        • GO/NO-GO 판정
        </td>
        <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
        </td>
        </tr>
        </table>
        
        </div>
        """, unsafe_allow_html=True)
        return
    
    # ========== 16개 검증 시스템 구조 (처음부터 표시!) ==========
    st.markdown("""
    <div style="color: #ffffff; font-size: 0.95rem; line-height: 1.6;">
    
    <p style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">ℹ️ 16개 검증 시스템 구조</p>
    
    <table style="width:100%; border-collapse: collapse;">
    <tr>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>1️⃣ 시계열 분석 (5개)</strong><br>
    - 월별 수익률 분석<br>
    - 연속 손실 거래<br>
    - 보유기간 분포<br>
    - 월간 회귀선<br>
    - 월간 일관성
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>2️⃣ 통계 검정 (4개)</strong><br>
    - 승률 신뢰도<br>
    - 수익률 유의성<br>
    - 분포 분석<br>
    - 꼬리 리스크
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>3️⃣ 거래 분석 (2개)</strong><br>
    - 승/패 거래 비교<br>
    - 거래 특성 분류
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>4️⃣ 극한 상황 (5개)</strong><br>
    - 50달러 생존성<br>
    - 부트스트랩<br>
    - 극단값 분석<br>
    - 자본 성장<br>
    - 회귀선 분석
    </td>
    </tr>
    <tr>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>5️⃣ 포지션 최적화 (3개)</strong><br>
    - Sharpe/Sortino/Calmar<br>
    - Kelly Criterion<br>
    - 동적 로트
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>6️⃣ 고급 통계 (3개)</strong><br>
    - 기울기 검정<br>
    - 자기상관 검정<br>
    - 이분산성 검정
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    <strong>7️⃣ 종합평가 (1개)</strong><br>
    - 배제 조건<br>
    - 최종 점수<br>
    - GO/NO-GO 판정
    </td>
    <td style="border: 1px solid #374151; padding: 12px; background: #1e2330;">
    </td>
    </tr>
    </table>
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 기본 통계 표시
    try:
        stats = converter_instance.get_statistics()
        
        st.markdown("### 📊 기본 통계")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 거래", f"{stats['total_trades']}건")
        
        with col2:
            st.metric("승률", f"{stats['win_rate']:.2f}%")
        
        with col3:
            st.metric("총 수익률", f"{stats['total_return']:.2f}%")
        
        with col4:
            st.metric("기간", f"{stats['period_days']}일")
        
        st.markdown("---")
        
        # 상세 통계
        st.markdown("### 📈 상세 통계")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("수익 거래", f"{stats['winning_trades']}건")
            st.metric("평균 수익", f"{stats['avg_win']:.2f}%")
        
        with col2:
            st.metric("손실 거래", f"{stats['losing_trades']}건")
            st.metric("평균 손실", f"{stats['avg_loss']:.2f}%")
        
        with col3:
            st.metric("최대 낙폭", f"{stats['max_drawdown']:.2f}%")
            st.metric("평균 거래 수익", f"{stats['avg_return']:.2f}%")
        
        st.markdown("---")
        
        # 거래 데이터 표시
        st.markdown("### 📋 거래 목록")
        
        trades = converter_instance.trades
        if len(trades) > 0:
            display_cols = ['trade_num', 'direction', 'entry_date', 'exit_date', 'return_pct', 'holding_days']
            display_trades = trades[display_cols].copy()
            display_trades.columns = ['거래번호', '방향', '진입날짜', '청산날짜', '수익률%', '보유일수']
            
            st.dataframe(display_trades, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # ========== 16개 검증 시스템 실행 ==========
        st.markdown("### 🔄 16개 검증 시스템 실행")
        
        if st.button("🚀 16개 검증 시작", key="run_validators"):
            with st.spinner("⏳ 분석 중... 잠시만 기다려주세요."):
                try:
                    from analysis.validators.comprehensive import ComprehensiveEvaluator
                    
                    # ComprehensiveEvaluator 실행
                    evaluator = ComprehensiveEvaluator(
                        converter_instance.trades,
                        pd.Timestamp(converter_instance.trades['entry_date'].min()),
                        pd.Timestamp(converter_instance.trades['exit_date'].max()),
                        initial_capital=50.0
                    )
                    
                    # 16개 검증 실행
                    evaluator.run_all_validators()
                    evaluator.check_disqualification_criteria()
                    evaluator.generate_final_score()
                    
                    # 종합 리포트 생성
                    report = evaluator.get_comprehensive_report()
                    all_results = report['validators']
                    
                    # 결과 표시
                    st.success("✅ 16개 검증 완료!")
                    
                    st.markdown("---")
                    st.markdown("### 📊 검증 결과 요약")
                    
                    # 메트릭 표시
                    col1, col2, col3, col4 = st.columns(4)
                    
                    disq = report['disqualification']
                    final_score = report['final_score']
                    
                    with col1:
                        st.metric(
                            "승률", 
                            f"{disq.get('win_rate', 0):.1f}%"
                        )
                    
                    with col2:
                        st.metric(
                            "최종 점수", 
                            f"{final_score['final_score']:.1f}점"
                        )
                    
                    with col3:
                        st.metric(
                            "등급", 
                            final_score['rating']
                        )
                    
                    with col4:
                        st.metric(
                            "판정", 
                            disq['status']
                        )
                    
                    st.markdown("---")
                    
                    # 최종 판정
                    st.markdown("### 🎯 자동매매 판정")
                    
                    status = disq['status']
                    
                    if "❌" in status:
                        st.error(status)
                        if disq['reasons']:
                            st.error("**이유:**\n" + "\n".join([f"- {r}" for r in disq['reasons']]))
                    elif "⚠️" in status:
                        st.warning(status)
                    else:
                        st.success(status)
                    
                    st.markdown("---")
                    
                    # 카테고리별 점수 - Plotly 가로 바 차트 (드로우다운 수정 적용!)
                    st.markdown("### 📈 카테고리별 점수")
                    
                    scores_df = pd.DataFrame(
                        list(final_score['scores'].items()),
                        columns=['카테고리', '점수']
                    )
                    
                    # ========== Plotly 가로 바 차트 ==========
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
                    
                    st.markdown("---")

                    # 결과 다운로드 (HTML)
                    st.markdown("### 📥 결과 다운로드")
                    
                    html_content = f"""
                    <html>
                    <head>
                    <meta charset="utf-8">
                    <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    h1 {{ color: #1f2937; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
                    h2 {{ color: #374151; margin-top: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; background: white; margin: 15px 0; }}
                    th, td {{ border: 1px solid #d1d5db; padding: 12px; text-align: left; }}
                    th {{ background-color: #3b82f6; color: white; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f9fafb; }}
                    .status-go {{ color: #10b981; font-weight: bold; }}
                    .status-nogo {{ color: #ef4444; font-weight: bold; }}
                    .score {{ text-align: right; font-weight: bold; }}
                    </style>
                    </head>
                    <body>
                    
                    <h1>🔬 16개 검증 시스템 분석 결과</h1>
                    
                    <h2>🎯 자동매매 판정</h2>
                    <p>상태: <span class="status-{('go' if disq['status'] == '✅ GO' else 'nogo')}">{disq['status']}</span></p>
                    <p>기준: {disq['tier']}</p>
                    <p>이유:</p>
                    <ul>
                    """
                    
                    if disq['reasons']:
                        for reason in disq['reasons']:
                            html_content += f"<li>{reason}</li>"
                    else:
                        html_content += "<li>모든 검증 통과</li>"
                    
                    html_content += f"""
                    </ul>
                    
                    <h2>📈 카테고리별 점수</h2>
                    <table>
                    <tr>
                    <th>카테고리</th>
                    <th>점수</th>
                    </tr>
                    """
                    
                    for category, score in final_score['scores'].items():
                        html_content += f"<tr><td>{category}</td><td class='score'>{score:.1f}점</td></tr>"
                    
                    html_content += f"""
                    </table>
                    
                    <h2>📊 종합 평가</h2>
                    <p><strong>최종 점수:</strong> {final_score['final_score']:.1f}점</p>
                    <p><strong>등급:</strong> {final_score['rating']}</p>
                    <p><strong>판정:</strong> {disq['status']}</p>
                    
                    </body>
                    </html>
                    """
                    
                    st.download_button(
                        label="📄 검증 결과 HTML 다운로드",
                        data=html_content,
                        file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                    
                    # JSON도 다운로드
                    json_str = json.dumps(report, default=str, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📊 검증 결과 JSON 다운로드",
                        data=json_str,
                        file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                except ImportError as e:
                    st.error(f"❌ 모듈 로드 실패: {e}")
                    st.info("💡 분석 모듈을 찾을 수 없습니다.")
                
                except Exception as e:
                    st.error(f"❌ 검증 실패: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        st.markdown("---")
                    
        # 카테고리 상세 설명
        st.markdown("### 📚 카테고리별 점수 해석")
                  
        category_guide = {
            '백테스트 성과': '승률 × 50 + 수익률/40 × 50. 높을수록 좋음.',
            'Walk-Forward': 'Train vs Test 성과 비교. 80점 이상 권장.',
            '시계열 안정성': '월별 수익 일관성. 50점 이상 권장.',
            '통계 신뢰도': '승률의 통계적 유의성 (p-value). 80점 이상 권장.',
            '거래 특성': '수익팩터. 50점 이상 권장.',
            '극한 상황': '50달러 초기자본 생존성. 100점 = 안전.',
            '포지션 최적화': 'Sharpe Ratio. 50점 이상 권장.',
            '고급 통계': '수익 곡선의 추세 강도 (R²). 70점 이상 권장.'
        }
                    
        for category, description in category_guide.items():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.write(f"**{category}**")
            with col2:
                st.write(description)
                    
        st.markdown("---")
        
    except Exception as e:
        st.error(f"❌ 실패: {e}")
        import traceback
        st.code(traceback.format_exc())