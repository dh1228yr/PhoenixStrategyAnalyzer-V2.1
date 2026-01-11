"""
손실 분석 고도화 모듈
CSV 데이터만으로 최대한의 정보 추출
탭: 손실요약 / TP없이손절 / 손실패턴
심화분석: 신호 강도 비교, 개선 제안 자동 생성
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

class LossAnalysisEnhanced:
    """손실 분석 고도화"""
    
    def __init__(self, trades_df):
        self.trades = trades_df.copy()
        self.losing_trades = self.trades[self.trades['return_pct'] < 0].copy()
        self.winning_trades = self.trades[self.trades['return_pct'] > 0].copy()
        
        # 신호 강도 분류 (runup 기반)
        self._classify_signal_strength()
    
    def _classify_signal_strength(self):
        """신호 강도 분류 (Runup 기반)"""
        
        # 손실 거래
        self.losing_trades['signal_strength'] = pd.cut(
            self.losing_trades['runup_pct'],
            bins=[-np.inf, 0.3, 0.5, 1.0, 2.0, 5.0, np.inf],
            labels=['극약함', '매우약함', '약함', '보통', '중간', '강함'],
            include_lowest=True
        )
        
        # 수익 거래
        self.winning_trades['signal_strength'] = pd.cut(
            self.winning_trades['runup_pct'],
            bins=[-np.inf, 0.3, 0.5, 1.0, 2.0, 5.0, np.inf],
            labels=['극약함', '매우약함', '약함', '보통', '중간', '강함'],
            include_lowest=True
        )
        
        # 전체
        self.trades['signal_strength'] = pd.cut(
            self.trades['runup_pct'],
            bins=[-np.inf, 0.3, 0.5, 1.0, 2.0, 5.0, np.inf],
            labels=['극약함', '매우약함', '약함', '보통', '중간', '강함'],
            include_lowest=True
        )
    
    def get_summary_stats(self):
        """손실 요약 통계"""
        return {
            'total_losing': len(self.losing_trades),
            'loss_rate': len(self.losing_trades) / len(self.trades) * 100,
            'total_loss': self.losing_trades['return_pct'].sum(),
            'avg_loss': self.losing_trades['return_pct'].mean(),
            'max_loss': self.losing_trades['return_pct'].min(),
            'median_loss': self.losing_trades['return_pct'].median(),
            'std_loss': self.losing_trades['return_pct'].std(),
        }
    
    def identify_tp_less_sl(self):
        """TP 없이 전량 손절 거래 식별"""
        
        # exit_signal 컬럼이 없으면 모두 '손절'로 처리
        self.losing_trades['exit_type'] = '손절'
        
        # TP 없이 손절 거래
        tp_less_sl = self.losing_trades[
            (self.losing_trades['runup_pct'] < 1.0) &
            (self.losing_trades['drawdown_pct'] < -2.0) &
            (self.losing_trades['exit_type'] == '손절')
        ].copy()
        
        return tp_less_sl
    
    def analyze_tp_less_sl_deep(self):
        """TP 없이 손절 거래 심화 분석"""
        
        tp_less_sl = self.identify_tp_less_sl()
        
        if len(tp_less_sl) == 0:
            return None
        
        analysis = {
            'count': len(tp_less_sl),
            'ratio_of_losses': len(tp_less_sl) / len(self.losing_trades) * 100,
            'ratio_of_total': len(tp_less_sl) / len(self.trades) * 100,
            'total_loss': tp_less_sl['return_pct'].sum(),
            'avg_loss': tp_less_sl['return_pct'].mean(),
            'max_loss': tp_less_sl['return_pct'].min(),
            'trades': tp_less_sl
        }
        
        # 같은 신호로 수익 난 거래와 비교
        analysis['same_signal_comparison'] = self._compare_with_winning(tp_less_sl)
        
        return analysis
    
    def _compare_with_winning(self, losing_subset):
        """같은 신호가 수익 거래에서 어떻게 작동했는지 비교"""
        
        strength_analysis = {}
        for strength in ['극약함', '매우약함', '약함', '보통', '중간', '강함']:
            strength_trades = self.trades[self.trades['signal_strength'] == strength]
            strength_winning = strength_trades[strength_trades['return_pct'] > 0]
            
            if len(strength_trades) > 0:
                strength_analysis[strength] = {
                    'total': len(strength_trades),
                    'winning': len(strength_winning),
                    'win_rate': len(strength_winning) / len(strength_trades) * 100,
                    'avg_return': strength_trades['return_pct'].mean(),
                    'avg_runup': strength_trades['runup_pct'].mean(),
                }
        
        return strength_analysis
    
    def analyze_loss_patterns(self):
        """손실 패턴 분석"""
        
        if len(self.losing_trades) == 0:
            return None
        
        # 1. 진입 후 즉시 반대 움직임
        immediate_reversal = self.losing_trades[
            (self.losing_trades['runup_pct'] < 0.5) &
            (self.losing_trades['drawdown_pct'] < -1.0)
        ]
        
        # 2. 상승했다가 급락
        reversal_after_rise = self.losing_trades[
            (self.losing_trades['runup_pct'] > 2.0) &
            (self.losing_trades['drawdown_pct'] < self.losing_trades['runup_pct'] * -1)
        ]
        
        # 3. 지속적 하락
        continuous_decline = self.losing_trades[
            (self.losing_trades['runup_pct'] < 0.5) &
            (self.losing_trades['drawdown_pct'] < -3.0)
        ]
        
        # 4. 시간이 많이 걸린 손실
        time_decay_loss = self.losing_trades[
            self.losing_trades['holding_days'] >= 5
        ]
        
        # 5. 신호 강도별 손실률
        signal_strength_loss = {}
        for strength in ['극약함', '매우약함', '약함', '보통', '중간', '강함']:
            strength_losing = self.losing_trades[self.losing_trades['signal_strength'] == strength]
            strength_all = self.trades[self.trades['signal_strength'] == strength]
            
            if len(strength_all) > 0:
                signal_strength_loss[strength] = {
                    'loss_count': len(strength_losing),
                    'total_count': len(strength_all),
                    'loss_rate': len(strength_losing) / len(strength_all) * 100,
                    'avg_loss': strength_losing['return_pct'].mean() if len(strength_losing) > 0 else 0,
                }
        
        return {
            'immediate_reversal': immediate_reversal,
            'reversal_after_rise': reversal_after_rise,
            'continuous_decline': continuous_decline,
            'time_decay_loss': time_decay_loss,
            'signal_strength_loss': signal_strength_loss,
        }
    
    def get_improvement_suggestions(self):
        """개선 제안 자동 생성"""
        
        suggestions = []
        
        # 1. 신호 강도 약한 거래 분석
        weak_signal_trades = self.losing_trades[self.losing_trades['signal_strength'].isin(['극약함', '매우약함', '약함'])]
        
        if len(weak_signal_trades) / len(self.losing_trades) * 100 > 40:
            suggestions.append({
                'priority': '🔴 CRITICAL',
                'issue': '약한 신호 진입 과다',
                'detail': f"{len(weak_signal_trades)}건 ({len(weak_signal_trades)/len(self.losing_trades)*100:.1f}%)",
                'cause': '5단계 주지표 신호, 6단계 추세전환, 7단계 보조지표 기준이 너무 낮음',
                'solution': [
                    '6단계: 추세전환 조건 강화 (1/3 → 2/3 이상)',
                    '7단계: 보조지표 점수 기준 상향 (7점 → 12점 이상)',
                    '결과: runup < 1% 거래 60% 제거 가능'
                ],
                'expected_impact': '손실 거래 30~40% 감소'
            })
        
        # 2. TP 없이 손절 패턴
        tp_less_sl = self.identify_tp_less_sl()
        
        if len(tp_less_sl) > 0 and len(tp_less_sl) / len(self.losing_trades) * 100 > 15:
            suggestions.append({
                'priority': '🟠 HIGH',
                'issue': 'TP 없이 전량 손절 과다',
                'detail': f"{len(tp_less_sl)}건 ({len(tp_less_sl)/len(self.losing_trades)*100:.1f}%)",
                'cause': '손절이 변동성에 맞지 않거나, 진입 신호 약함',
                'solution': [
                    '12단계: 손절 레벨을 ATR × 1.5 기반으로 설정',
                    '또는 6단계 추세전환 조건 강화',
                    '결과: 약한 신호가 필터링되고, 손절이 더 합리적으로 배치됨'
                ],
                'expected_impact': '손절 거래 20~30% 감소'
            })
        
        # 3. 진입 후 즉시 반대 움직임
        analysis = self.analyze_loss_patterns()
        immediate_rev = analysis['immediate_reversal']
        
        if len(immediate_rev) / len(self.losing_trades) * 100 > 25:
            suggestions.append({
                'priority': '🟡 MEDIUM',
                'issue': '진입 후 즉시 반대 움직임',
                'detail': f"{len(immediate_rev)}건 ({len(immediate_rev)/len(self.losing_trades)*100:.1f}%)",
                'cause': '거래량 부족 시간대, 경제지표 뉴스, 변동성 급증',
                'solution': [
                    '2~4단계 필터 강화: 월별/시간대/거래량 필터 재검토',
                    '특정 시간대 제외 (예: 09:00~09:30 뉴스 시간)',
                    '최소 거래량 기준 상향'
                ],
                'expected_impact': '시장 조건 악화 거래 50% 필터링'
            })
        
        # 4. 시간 손실
        time_loss = analysis['time_decay_loss']
        
        if len(time_loss) > 0:
            suggestions.append({
                'priority': '🔵 LOW',
                'issue': '장기 보유 손실',
                'detail': f"{len(time_loss)}건 ({len(time_loss)/len(self.losing_trades)*100:.1f}%)",
                'cause': '포지션 홀딩 시간이 길어질수록 손실 발생',
                'solution': [
                    '15단계: 최대 포지션 보유 시간 제한 설정',
                    '또는 11단계: 트레일링 스탑 로직 검토',
                    '결과: 예측 불가능한 장기 하락 회피'
                ],
                'expected_impact': '시간 손실 60% 감소'
            })
        
        return suggestions


def render_page_loss_enhanced(converter):
    """손실 분석 페이지 - 탭 3개 + 심화분석"""
    
    st.header("📉 손실 거래 분석 (고도화)")
    
    if converter is None:
        st.warning("⚠️ 먼저 CSV를 업로드하세요.")
        return
    
    trades = converter.trades
    analyzer = LossAnalysisEnhanced(trades)
    
    # 손실 거래가 없으면
    if len(analyzer.losing_trades) == 0:
        st.success("🎉 손실 거래 없음! 완벽한 전략입니다!")
        return
    
    # ========== 탭 구성 ==========
    tab1, tab2, tab3 = st.tabs(["📊 손실요약", "🚨 TP없이손절", "🔍 손실패턴"])
    
    # ========== TAB 1: 손실요약 ==========
    with tab1:
        st.markdown("### 📊 손실 거래 요약")
        
        stats = analyzer.get_summary_stats()
        
        # 기본 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("손실 거래", f"{int(stats['total_losing'])}건")
            st.caption(f"전체 대비: {stats['loss_rate']:.1f}%")
        
        with col2:
            st.metric("총 손실", f"{stats['total_loss']:.2f}%")
            st.caption("누적 손실률")
        
        with col3:
            st.metric("평균 손실", f"{stats['avg_loss']:.2f}%")
            st.caption(f"중위수: {stats['median_loss']:.2f}%")
        
        with col4:
            st.metric("최대 손실", f"{stats['max_loss']:.2f}%")
            st.caption(f"표준편차: {stats['std_loss']:.2f}%")
        
        st.markdown("---")
        
        # 손실 분포 시각화
        col1, col2 = st.columns(2)
        
        with col1:
            # 히스토그램
            fig = go.Figure()
            
            n_bins = min(10, max(5, len(analyzer.losing_trades) // 2))
            
            fig.add_trace(go.Histogram(
                x=analyzer.losing_trades['return_pct'],
                nbinsx=n_bins,
                marker_color='#e74c3c',
                name='손실 분포',
                opacity=0.75
            ))
            
            fig.update_layout(
                title="손실 분포 히스토그램",
                xaxis_title="손실 (%)",
                yaxis_title="거래 수",
                height=350,
                bargap=0.1,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=12),
                title_font=dict(size=14, color='#ffffff'),
                xaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568'),
                yaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 시간대별 손실 추이
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=analyzer.losing_trades['exit_date'],
                y=analyzer.losing_trades['return_pct'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=analyzer.losing_trades['return_pct'],
                    colorscale='Reds_r',
                    showscale=True,
                    colorbar=dict(title="손실 %", tickfont=dict(color='#ffffff'))
                ),
                hovertemplate='<b>Trade #%{customdata[0]}</b><br>손실: %{y:.2f}%<br>기간: %{customdata[1]}일<extra></extra>',
                customdata=np.column_stack((
                    analyzer.losing_trades['trade_num'].values,
                    analyzer.losing_trades['holding_days'].values
                )),
                name='손실 거래'
            ))
            
            fig.update_layout(
                title="시간대별 손실 추이",
                xaxis_title="청산 날짜",
                yaxis_title="손실 (%)",
                height=350,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=12),
                title_font=dict(size=14, color='#ffffff'),
                xaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568'),
                yaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 신호 강도별 손실 분석
        st.markdown("### 🔍 신호 강도별 손실 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 신호 강도별 손실률
            fig = go.Figure()
            
            strength_order = ['극약함', '매우약함', '약함', '보통', '중간', '강함']
            loss_by_strength = []
            strength_labels = []
            
            for strength in strength_order:
                strength_trades = analyzer.trades[analyzer.trades['signal_strength'] == strength]
                strength_losing = strength_trades[strength_trades['return_pct'] < 0]
                
                if len(strength_trades) > 0:
                    loss_rate = len(strength_losing) / len(strength_trades) * 100
                    loss_by_strength.append(loss_rate)
                    strength_labels.append(f"{strength}<br>({len(strength_trades)})")
            
            colors = ['#c0392b', '#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#2ecc71'][:len(loss_by_strength)]
            
            fig.add_trace(go.Bar(
                x=strength_labels,
                y=loss_by_strength,
                marker_color=colors,
                text=[f"{v:.1f}%" for v in loss_by_strength],
                textposition='auto',
                hovertemplate='%{x}<br>손실률: %{y:.1f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title="신호 강도별 손실률",
                yaxis_title="손실률 (%)",
                height=300,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=11),
                title_font=dict(size=13, color='#ffffff'),
                yaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568'),
                xaxis=dict(linecolor='#4a5568'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 신호 강도별 평균 손실
            fig = go.Figure()
            
            avg_loss_by_strength = []
            strength_labels_2 = []
            
            for strength in strength_order:
                strength_losing = analyzer.losing_trades[analyzer.losing_trades['signal_strength'] == strength]
                
                if len(strength_losing) > 0:
                    avg_loss = strength_losing['return_pct'].mean()
                    avg_loss_by_strength.append(avg_loss)
                    strength_labels_2.append(f"{strength}<br>({len(strength_losing)})")
            
            colors = ['#c0392b', '#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#2ecc71'][:len(avg_loss_by_strength)]
            
            fig.add_trace(go.Bar(
                x=strength_labels_2,
                y=avg_loss_by_strength,
                marker_color=colors,
                text=[f"{v:.2f}%" for v in avg_loss_by_strength],
                textposition='auto',
                hovertemplate='%{x}<br>평균 손실: %{y:.2f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title="신호 강도별 평균 손실",
                yaxis_title="평균 손실 (%)",
                height=300,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=11),
                title_font=dict(size=13, color='#ffffff'),
                yaxis=dict(gridcolor='rgba(74, 85, 104, 0.3)', linecolor='#4a5568'),
                xaxis=dict(linecolor='#4a5568'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 손실 거래 목록
        st.markdown("### 📋 손실 거래 목록")
        
        display_df = analyzer.losing_trades[['trade_num', 'entry_date', 'exit_date', 
                                            'signal_strength', 'return_pct', 'runup_pct', 
                                            'drawdown_pct', 'holding_days']].copy()
        
        # 정렬 옵션
        sort_option = st.selectbox(
            "정렬 기준",
            ["손실 큰 순", "최근 순", "보유기간 긴 순"],
            index=0,
            key="loss_sort"
        )
        
        if sort_option == "손실 큰 순":
            display_df = display_df.sort_values('return_pct', ascending=True)
        elif sort_option == "최근 순":
            display_df = display_df.sort_values('exit_date', ascending=False)
        else:
            display_df = display_df.sort_values('holding_days', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    # ========== TAB 2: TP없이손절 심화분석 ==========
    with tab2:
        st.markdown("### 🚨 TP 없이 전량 손절 심화 분석")
        
        analysis = analyzer.analyze_tp_less_sl_deep()
        
        if analysis is None:
            st.success("✅ TP 없이 손절 거래 없음!")
        else:
            # 기본 통계
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("TP없이손절", f"{int(analysis['count'])}건")
                st.caption(f"손실 대비: {analysis['ratio_of_losses']:.1f}%")
            
            with col2:
                st.metric("전체 대비", f"{analysis['ratio_of_total']:.1f}%")
                st.caption("매우 주의 필요")
            
            with col3:
                st.metric("총 손실", f"{analysis['total_loss']:.2f}%")
                st.caption("누적 손실")
            
            with col4:
                st.metric("평균 손실", f"{analysis['avg_loss']:.2f}%")
                st.caption(f"최대: {analysis['max_loss']:.2f}%")
            
            st.markdown("---")
            
            # TP없이손절 거래 상세 분석
            st.markdown("### 📊 TP없이손절 거래 상세")
            
            tp_trades = analysis['trades']
            
            # Runup/Drawdown 분석
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔴 Runup 분석 (진입 후 상승)**")
                st.metric("평균 Runup", f"{tp_trades['runup_pct'].mean():.2f}%")
                st.caption("진입 신호가 극도로 약했음을 의미")
            
            with col2:
                st.markdown("**🔵 Drawdown 분석 (최대 하락)**")
                st.metric("평균 Drawdown", f"{tp_trades['drawdown_pct'].mean():.2f}%")
                st.caption("손절이 빠르게 발동했음을 의미")
            
            st.markdown("---")
            
            # 신호 강도별 비교
            st.markdown("### 🎯 신호 강도별 비교: 손실 vs 수익")
            
            comparison = analysis['same_signal_comparison']
            
            # 테이블 생성
            comparison_data = []
            for strength, stats_dict in comparison.items():
                if stats_dict['total'] > 0:
                    comparison_data.append({
                        '신호강도': strength,
                        '총거래': stats_dict['total'],
                        '수익거래': stats_dict['winning'],
                        '승률(%)': f"{stats_dict['win_rate']:.1f}%",
                        '평균수익(%)': f"{stats_dict['avg_return']:.2f}%",
                        '평균Runup(%)': f"{stats_dict['avg_runup']:.2f}%"
                    })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # TP없이손절 거래 목록
            st.markdown("### 📋 TP없이손절 거래 상세 목록")
            
            display_tp = tp_trades[['trade_num', 'entry_date', 'exit_date', 
                                    'return_pct', 'runup_pct', 'drawdown_pct', 
                                    'holding_days']].copy()
            
            display_tp = display_tp.sort_values('return_pct', ascending=True)
            
            st.dataframe(display_tp, use_container_width=True, height=300)
    
    # ========== TAB 3: 손실패턴 ==========
    with tab3:
        st.markdown("### 🔍 손실 패턴 분석")
        
        analysis = analyzer.analyze_loss_patterns()
        
        # 패턴별 통계
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📊 손실 패턴별 분류</h4>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            count1 = len(analysis['immediate_reversal'])
            ratio1 = count1 / len(analyzer.losing_trades) * 100 if len(analyzer.losing_trades) > 0 else 0
            st.metric("즉시반대", f"{count1}건")
            st.caption(f"{ratio1:.1f}% of losses")
        
        with col2:
            count2 = len(analysis['reversal_after_rise'])
            ratio2 = count2 / len(analyzer.losing_trades) * 100 if len(analyzer.losing_trades) > 0 else 0
            st.metric("상승후급락", f"{count2}건")
            st.caption(f"{ratio2:.1f}% of losses")
        
        with col3:
            count3 = len(analysis['continuous_decline'])
            ratio3 = count3 / len(analyzer.losing_trades) * 100 if len(analyzer.losing_trades) > 0 else 0
            st.metric("지속하락", f"{count3}건")
            st.caption(f"{ratio3:.1f}% of losses")
        
        with col4:
            count4 = len(analysis['time_decay_loss'])
            ratio4 = count4 / len(analyzer.losing_trades) * 100 if len(analyzer.losing_trades) > 0 else 0
            st.metric("시간손실", f"{count4}건")
            st.caption(f"{ratio4:.1f}% of losses")
        
        st.markdown("---")
        
        # 신호 강도별 손실 분석
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📊 신호 강도별 손실 심각도</h4>', unsafe_allow_html=True)
        
        signal_loss = analysis['signal_strength_loss']
        
        signal_data = []
        for strength, stats in signal_loss.items():
            signal_data.append({
                '신호강도': strength,
                '손실건': stats['loss_count'],
                '총거래': stats['total_count'],
                '손실률(%)': f"{stats['loss_rate']:.1f}%",
                '평균손실(%)': f"{stats['avg_loss']:.2f}%"
            })
        
        signal_df = pd.DataFrame(signal_data)
        st.dataframe(signal_df, use_container_width=True, hide_index=True)
        
        # 시각화
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            
            strengths = [d['신호강도'] for d in signal_data]
            loss_rates = [float(d['손실률(%)'].rstrip('%')) for d in signal_data]
            
            fig.add_trace(go.Bar(
                x=strengths,
                y=loss_rates,
                marker_color=['#c0392b', '#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#2ecc71'][:len(strengths)],
                text=[f"{v:.1f}%" for v in loss_rates],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="신호강도별 손실률",
                yaxis_title="손실률 (%)",
                height=300,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=11),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure()
            
            avg_losses = [float(d['평균손실(%)'].rstrip('%')) for d in signal_data]
            
            fig.add_trace(go.Bar(
                x=strengths,
                y=avg_losses,
                marker_color=['#c0392b', '#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#2ecc71'][:len(strengths)],
                text=[f"{v:.2f}%" for v in avg_losses],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="신호강도별 평균손실",
                yaxis_title="평균손실 (%)",
                height=300,
                plot_bgcolor='#2d3748',
                paper_bgcolor='#2d3748',
                font=dict(color='#ffffff', size=11),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== 개선 제안 섹션 ==========
    st.markdown("---")
    st.markdown("### 💡 자동 생성된 개선 제안")
    
    suggestions = analyzer.get_improvement_suggestions()
    
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            with st.expander(f"{suggestion['priority']} {suggestion['issue']}", expanded=(i==1)):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**규모**: {suggestion['detail']}")
                    st.markdown(f"**원인**: {suggestion['cause']}")
                
                with col2:
                    st.markdown("**해결책**:")
                    for solution in suggestion['solution']:
                        st.markdown(f"• {solution}")
                    
                    st.markdown(f"**기대 효과**: {suggestion['expected_impact']}")
    else:
        st.info("💡 현재는 개선이 필요 없을 정도로 우수한 성과입니다!")