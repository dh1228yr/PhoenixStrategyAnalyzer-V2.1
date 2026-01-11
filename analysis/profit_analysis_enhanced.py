import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


class ProfitAnalysisEnhanced:
    """수익 분석 고도화 모듈"""
    
    def __init__(self, converter):
        self.converter = converter
        self.trades = converter.trades.copy()
        self.winning_trades = self.trades[self.trades['return_pct'] > 0].copy()
        self.losing_trades = self.trades[self.trades['return_pct'] < 0].copy()
    
    # ========================================
    # 신호 강도 분류
    # ========================================
    
    def _classify_signal_strength(self, runup):
        """Runup 기반 신호 강도 분류"""
        if runup < 0.3:
            return '극강함'
        elif runup < 0.5:
            return '매우강함'
        elif runup < 1.0:
            return '강함'
        elif runup < 2.0:
            return '보통'
        elif runup < 5.0:
            return '약함'
        else:
            return '매우약함'
    
    # ========================================
    # 수익요약 분석
    # ========================================
    
    def get_profit_summary_stats(self):
        """수익 거래 요약 통계"""
        if len(self.winning_trades) == 0:
            return None
        
        stats = {
            'total_winning': len(self.winning_trades),
            'total_profit': self.winning_trades['return_pct'].sum(),
            'avg_profit': self.winning_trades['return_pct'].mean(),
            'median_profit': self.winning_trades['return_pct'].median(),
            'max_profit': self.winning_trades['return_pct'].max(),
            'min_profit': self.winning_trades['return_pct'].min(),
            'std_profit': self.winning_trades['return_pct'].std(),
            'avg_holding_days': self.winning_trades['holding_days'].mean(),
            'avg_runup': self.winning_trades['runup_pct'].mean(),
            'avg_drawdown': self.winning_trades['drawdown_pct'].mean(),
        }
        
        return stats
    
    def get_signal_strength_analysis(self):
        """신호 강도별 수익 분석"""
        self.winning_trades['signal_strength'] = self.winning_trades['runup_pct'].apply(
            self._classify_signal_strength
        )
        
        analysis = self.winning_trades.groupby('signal_strength').agg({
            'return_pct': ['count', 'mean', 'sum', 'std'],
            'runup_pct': 'mean',
            'holding_days': 'mean'
        }).round(2)
        
        # 신호 강도 순서 정렬
        strength_order = ['극강함', '매우강함', '강함', '보통', '약함', '매우약함']
        analysis = analysis.reindex([s for s in strength_order if s in analysis.index])
        
        return analysis
    
    # ========================================
    # 고수익 거래 분석
    # ========================================
    
    def get_top_profit_trades(self, top_n=10):
        """상위 수익 거래"""
        top_trades = self.winning_trades.nlargest(top_n, 'return_pct')[
            ['trade_num', 'entry_date', 'exit_date', 'return_pct', 'runup_pct', 'drawdown_pct', 'holding_days']
        ].copy()
        
        top_trades['signal_strength'] = top_trades['runup_pct'].apply(self._classify_signal_strength)
        
        return top_trades
    
    def analyze_top_profit_patterns(self):
        """상위 수익 거래 패턴 분석"""
        top_trades = self.winning_trades.nlargest(20, 'return_pct')
        
        if len(top_trades) == 0:
            return None
        
        top_trades['signal_strength'] = top_trades['runup_pct'].apply(self._classify_signal_strength)
        
        pattern_analysis = {
            'avg_return': top_trades['return_pct'].mean(),
            'avg_runup': top_trades['runup_pct'].mean(),
            'avg_holding': top_trades['holding_days'].mean(),
            'dominant_signal': top_trades['signal_strength'].mode()[0] if len(top_trades) > 0 else 'N/A',
            'holding_pattern': 'Long' if top_trades['holding_days'].mean() > 5 else 'Short',
        }
        
        return pattern_analysis
    
    # ========================================
    # 수익 패턴 분석
    # ========================================
    
    def classify_profit_patterns(self):
        """수익 거래 패턴 분류 (4가지)"""
        patterns = []
        
        for _, trade in self.winning_trades.iterrows():
            runup = trade['runup_pct']
            drawdown = trade['drawdown_pct']
            profit = trade['return_pct']
            holding = trade['holding_days']
            
            # Pattern 1: 빠른상승 (진입 직후 크게 상승)
            if runup >= 5.0 and profit >= runup * 0.8:
                pattern = 'Pattern 1: 빠른상승'
            
            # Pattern 2: 지속상승 (계속 올라감)
            elif runup >= 2.0 and drawdown >= -1.0 and profit >= 2.0:
                pattern = 'Pattern 2: 지속상승'
            
            # Pattern 3: 변동성높음 (오르락내리락 하지만 수익)
            elif runup >= 3.0 and drawdown <= -2.0 and profit >= 1.0:
                pattern = 'Pattern 3: 변동성높음'
            
            # Pattern 4: 시간 수익 (천천히 올라감)
            elif holding >= 5 and profit >= 1.0:
                pattern = 'Pattern 4: 시간수익'
            
            else:
                pattern = 'Pattern 5: 기타'
            
            patterns.append(pattern)
        
        self.winning_trades['profit_pattern'] = patterns
        
        # 패턴별 분류
        pattern_summary = self.winning_trades.groupby('profit_pattern').agg({
            'return_pct': ['count', 'mean', 'sum'],
            'runup_pct': 'mean',
            'holding_days': 'mean'
        }).round(2)
        
        return pattern_summary
    
    def analyze_vs_losing_trades(self):
        """수익 vs 손실 거래 비교"""
        if len(self.losing_trades) == 0:
            return None
        
        winning_trades = self.winning_trades.copy()
        winning_trades['signal_strength'] = winning_trades['runup_pct'].apply(self._classify_signal_strength)
        
        losing_trades = self.losing_trades.copy()
        losing_trades['signal_strength'] = losing_trades['runup_pct'].apply(self._classify_signal_strength)
        
        comparison = pd.DataFrame({
            'Signal Strength': ['극강함', '매우강함', '강함', '보통', '약함', '매우약함']
        })
        
        # 수익 거래 승률 계산
        win_rate = []
        for signal in comparison['Signal Strength']:
            total = len(winning_trades[winning_trades['signal_strength'] == signal]) + \
                    len(losing_trades[losing_trades['signal_strength'] == signal])
            wins = len(winning_trades[winning_trades['signal_strength'] == signal])
            win_rate.append((wins / total * 100) if total > 0 else 0)
        
        comparison['Win Rate %'] = win_rate
        comparison['Avg Win'] = [
            winning_trades[winning_trades['signal_strength'] == signal]['return_pct'].mean()
            for signal in comparison['Signal Strength']
        ]
        comparison['Avg Loss'] = [
            losing_trades[losing_trades['signal_strength'] == signal]['return_pct'].mean()
            for signal in comparison['Signal Strength']
        ]
        
        return comparison
    
    # ========================================
    # 시각화
    # ========================================
    
    def plot_profit_distribution(self):
        """수익 분포 히스토그램"""
        fig = go.Figure()
        
        n_bins = min(10, max(5, len(self.winning_trades) // 2))
        
        fig.add_trace(go.Histogram(
            x=self.winning_trades['return_pct'],
            nbinsx=n_bins,
            marker_color='#27ae60',
            name='수익 분포',
            opacity=0.75
        ))
        
        fig.update_layout(
            title="수익 분포 히스토그램",
            xaxis_title="수익 (%)",
            yaxis_title="거래 수",
            height=350,
            bargap=0.1,
            plot_bgcolor='#2d3748',
            paper_bgcolor='#2d3748',
            font=dict(color='#ffffff', size=13, family="Arial, sans-serif"),
            title_font=dict(size=16, color='#ffffff', family="Arial, sans-serif"),
            xaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            ),
            yaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            )
        )
        
        return fig
    
    def plot_profit_timeline(self):
        """시간대별 수익 추이"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=self.winning_trades['exit_date'],
            y=self.winning_trades['return_pct'],
            mode='markers',
            marker=dict(
                size=10,
                color=self.winning_trades['return_pct'],
                colorscale='Greens',
                showscale=True,
                colorbar=dict(title="수익 %", tickfont=dict(color='#ffffff'))
            ),
            text=[f"Trade #{row['trade_num']}<br>수익: {row['return_pct']:.2f}%<br>기간: {row['holding_days']}일" 
                  for _, row in self.winning_trades.iterrows()],
            hoverinfo='text',
            name='수익 거래'
        ))
        
        fig.update_layout(
            title="시간대별 수익 추이",
            xaxis_title="청산 날짜",
            yaxis_title="수익 (%)",
            height=350,
            plot_bgcolor='#2d3748',
            paper_bgcolor='#2d3748',
            font=dict(color='#ffffff', size=13, family="Arial, sans-serif"),
            title_font=dict(size=16, color='#ffffff', family="Arial, sans-serif"),
            xaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            ),
            yaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            )
        )
        
        return fig
    
    def plot_signal_strength_profit(self):
        """신호 강도별 수익률 막대 차트"""
        analysis = self.get_signal_strength_analysis()
        
        if analysis is None or len(analysis) == 0:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=analysis.index,
            y=analysis[('return_pct', 'mean')],
            marker_color='#27ae60',
            name='평균 수익',
            text=[f"{v:.2f}%" for v in analysis[('return_pct', 'mean')]],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="신호 강도별 평균 수익률",
            xaxis_title="신호 강도",
            yaxis_title="수익 (%)",
            height=350,
            plot_bgcolor='#2d3748',
            paper_bgcolor='#2d3748',
            font=dict(color='#ffffff', size=13, family="Arial, sans-serif"),
            title_font=dict(size=16, color='#ffffff', family="Arial, sans-serif"),
            xaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            ),
            yaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            )
        )
        
        return fig
    
    def plot_win_loss_comparison(self):
        """수익 vs 손실 신호 강도 비교"""
        comparison = self.analyze_vs_losing_trades()
        
        if comparison is None:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=comparison['Signal Strength'],
            y=comparison['Win Rate %'],
            marker_color='#27ae60',
            name='승률',
            text=[f"{v:.1f}%" for v in comparison['Win Rate %']],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="신호 강도별 승률",
            xaxis_title="신호 강도",
            yaxis_title="승률 (%)",
            height=350,
            plot_bgcolor='#2d3748',
            paper_bgcolor='#2d3748',
            font=dict(color='#ffffff', size=13, family="Arial, sans-serif"),
            title_font=dict(size=16, color='#ffffff', family="Arial, sans-serif"),
            xaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            ),
            yaxis=dict(
                gridcolor='rgba(74, 85, 104, 0.3)',
                linecolor='#4a5568',
                tickfont=dict(color='#ffffff', size=12)
            )
        )
        
        return fig


# ========================================
# Streamlit 렌더링 함수
# ========================================

def render_page_profit_enhanced(converter):
    """수익 분석 페이지 렌더링"""
    
    st.header("💰 수익 거래 분석")
    
    if converter is None:
        st.warning("⚠️ 먼저 CSV를 업로드하세요.")
        return
    
    analyzer = ProfitAnalysisEnhanced(converter)
    
    if len(analyzer.winning_trades) == 0:
        st.warning("📊 수익 거래가 없습니다.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["📊 수익요약", "💎 고수익거래", "📈 수익패턴"])
    
    # ========================================
    # Tab 1: 수익요약
    # ========================================
    with tab1:
        st.markdown("### 📊 수익 요약")
        
        stats = analyzer.get_profit_summary_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("수익 거래", f"{stats['total_winning']:.0f}건")
        
        with col2:
            st.metric("총 수익", f"{stats['total_profit']:.2f}%")
        
        with col3:
            st.metric("평균 수익", f"{stats['avg_profit']:.2f}%")
        
        with col4:
            st.metric("최대 수익", f"{stats['max_profit']:.2f}%")
        
        st.markdown("---")
        
        # 수익 분포 시각화
        st.markdown("### 📈 수익 분포")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = analyzer.plot_profit_distribution()
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = analyzer.plot_profit_timeline()
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 신호 강도별 분석
        st.markdown("### 🎯 신호 강도별 수익 분석")
        
        signal_analysis = analyzer.get_signal_strength_analysis()
        
        if signal_analysis is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = analyzer.plot_signal_strength_profit()
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(signal_analysis, use_container_width=True)
        
        st.markdown("---")
        
        # 수익 거래 목록
        st.markdown("### 📋 수익 거래 상세")
        
        display_df = analyzer.winning_trades[[
            'trade_num', 'entry_date', 'exit_date', 'return_pct', 'runup_pct', 'drawdown_pct', 'holding_days'
        ]].copy()
        
        sort_option = st.selectbox(
            "정렬 기준",
            ["수익 큰 순", "최근 순", "보유기간 긴 순"],
            index=0,
            key="profit_tab1_sort"
        )
        
        if sort_option == "수익 큰 순":
            display_df = display_df.sort_values('return_pct', ascending=False)
        elif sort_option == "최근 순":
            display_df = display_df.sort_values('exit_date', ascending=False)
        else:
            display_df = display_df.sort_values('holding_days', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    # ========================================
    # Tab 2: 고수익거래
    # ========================================
    with tab2:
        st.markdown("### 💎 상위 수익 거래 분석")
        
        top_n = st.slider("상위 N개 거래", min_value=5, max_value=30, value=10, step=5)
        
        top_trades = analyzer.get_top_profit_trades(top_n=top_n)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("평균 수익", f"{top_trades['return_pct'].mean():.2f}%")
        
        with col2:
            st.metric("평균 Runup", f"{top_trades['runup_pct'].mean():.2f}%")
        
        with col3:
            st.metric("평균 보유기간", f"{top_trades['holding_days'].mean():.1f}일")
        
        st.markdown("---")
        
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📋 상위 거래 목록</h4>', unsafe_allow_html=True)
        st.dataframe(top_trades, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # 패턴 분석
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">🔍 상위 거래 성공 패턴</h4>', unsafe_allow_html=True)
        
        pattern_analysis = analyzer.analyze_top_profit_patterns()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **성공 거래의 특징:**
            - 평균 수익: {pattern_analysis['avg_return']:.2f}%
            - 평균 Runup: {pattern_analysis['avg_runup']:.2f}%
            - 평균 보유기간: {pattern_analysis['avg_holding']:.1f}일
            - 주요 신호 강도: {pattern_analysis['dominant_signal']}
            - 거래 특성: {pattern_analysis['holding_pattern']}
            """)
        
        with col2:
            st.success("""
            **💡 성공 거래의 조건:**
            1. 진입 신호가 강함 (높은 Runup)
            2. 신호 강도가 높을수록 성공률 높음
            3. 빠른 상승 후 지속 수익
            4. 변동성 관리 중요
            """)
        
        st.markdown("---")
        
        # 신호 강도별 비교
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📊 신호 강도별 비교</h4>', unsafe_allow_html=True)
        
        comparison = analyzer.analyze_vs_losing_trades()
        
        if comparison is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = analyzer.plot_win_loss_comparison()
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(comparison, use_container_width=True)
    
    # ========================================
    # Tab 3: 수익패턴
    # ========================================
    with tab3:
        st.markdown("### 📈 수익 패턴 분석")
        
        pattern_summary = analyzer.classify_profit_patterns()
        
        col1, col2, col3, col4 = st.columns(4)
        
        for idx, pattern in enumerate(['Pattern 1: 빠른상승', 'Pattern 2: 지속상승', 'Pattern 3: 변동성높음', 'Pattern 4: 시간수익']):
            if pattern in pattern_summary.index:
                count = pattern_summary.loc[pattern, ('return_pct', 'count')]
                avg_return = pattern_summary.loc[pattern, ('return_pct', 'mean')]
                
                cols = [col1, col2, col3, col4]
                with cols[idx]:
                    st.metric(
                        pattern.replace(': ', '\n'),
                        f"{count:.0f}건",
                        f"평균 {avg_return:.2f}%"
                    )
        
        st.markdown("---")
        
        # 패턴별 상세 분석
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📌 패턴별 상세</h4>', unsafe_allow_html=True)
        
        for pattern in ['Pattern 1: 빠른상승', 'Pattern 2: 지속상승', 'Pattern 3: 변동성높음', 'Pattern 4: 시간수익']:
            if pattern in pattern_summary.index:
                with st.expander(f"📌 {pattern}"):
                    col1, col2, col3 = st.columns(3)
                    
                    count = pattern_summary.loc[pattern, ('return_pct', 'count')]
                    avg_return = pattern_summary.loc[pattern, ('return_pct', 'mean')]
                    total_return = pattern_summary.loc[pattern, ('return_pct', 'sum')]
                    
                    with col1:
                        st.metric("거래 수", f"{count:.0f}건")
                    
                    with col2:
                        st.metric("평균 수익", f"{avg_return:.2f}%")
                    
                    with col3:
                        st.metric("총 수익", f"{total_return:.2f}%")
                    
                    # 패턴 설명
                    pattern_desc = {
                        'Pattern 1: 빠른상승': '진입 후 즉시 크게 상승하는 거래 - 강한 추세전환 신호',
                        'Pattern 2: 지속상승': '계속 올라가는 거래 - 안정적인 추세 거래',
                        'Pattern 3: 변동성높음': '오르락내리락 하지만 수익 - 변동성 활용 거래',
                        'Pattern 4: 시간수익': '천천히 올라가는 거래 - 장기 홀딩 거래'
                    }
                    
                    st.info(pattern_desc.get(pattern, ''))
        
        st.markdown("---")
        
        # 수익 vs 손실 비교
        st.markdown('<h4 style="color: #ffffff; font-weight: bold;">📊 수익 vs 손실 거래 비교</h4>', unsafe_allow_html=True)
        
        comparison = analyzer.analyze_vs_losing_trades()
        
        if comparison is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**신호 강도별 승률 비교:**")
                st.dataframe(comparison, use_container_width=True)
            
            with col2:
                st.markdown("**💡 핵심 인사이트:**")
                
                max_win_rate = comparison['Win Rate %'].max()
                max_signal = comparison[comparison['Win Rate %'] == max_win_rate]['Signal Strength'].values[0]
                
                st.success(f"""
                **가장 높은 승률:**
                - 신호 강도: {max_signal}
                - 승률: {max_win_rate:.1f}%
                
                **개선 방향:**
                - 이 신호 강도의 거래만 집중
                - 약한 신호 거래 제거
                - 신호 기준 강화 추천
                """)