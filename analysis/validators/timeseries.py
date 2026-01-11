"""
01_timeseries.py - 시계열 분석 모듈

시계열 분석 (5개 항목):
1-1. 월별/분기별/년도별 성과 분석
1-2. 연속성 분석 (최대 연속 승/패)
1-3. 보유기간 분석
1-4. 거래 밀도 분석
1-5. Equity Curve 분석
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any


class TimeSeriesAnalyzer:
    """시계열 분석 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
            필수 컬럼: entry_date, exit_date, return_pct (또는 profit_loss)
        start_date : pd.Timestamp
            백테스트 시작일
        end_date : pd.Timestamp
            백테스트 종료일
        """
        self.trades_df = trades_df.copy()
        self.start_date = start_date
        self.end_date = end_date
        self.total_days = (end_date - start_date).days
        
        # 컬럼명 정규화
        self._normalize_columns()
    
    def _normalize_columns(self):
        """컬럼명 정규화 (한글/영문)"""
        column_mapping = {
            '종료일': 'exit_date',
            'exit_date': 'exit_date',
            '날짜/시간': 'exit_date',
            '일자': 'exit_date',
            '거래 반환': 'return_pct',
            'Return': 'return_pct',
            '수익률': 'return_pct',
            'return_pct': 'return_pct'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in self.trades_df.columns and new_col not in self.trades_df.columns:
                self.trades_df[new_col] = self.trades_df[old_col]
        
        # exit_date를 datetime으로 변환
        if 'exit_date' in self.trades_df.columns:
            try:
                self.trades_df['exit_date'] = pd.to_datetime(self.trades_df['exit_date'])
            except Exception as e:
                print(f"⚠️ exit_date 변환 실패: {e}")
    
    # ========== 1-1. 월별/분기별/년도별 성과 분석 ==========
    def analyze_monthly_performance(self) -> Dict[str, Any]:
        """
        월별 성과 분석
        
        Returns:
        --------
        dict
            월별 성과 통계
        """
        try:
            # exit_date 컬럼 확인
            if 'exit_date' not in self.trades_df.columns:
                return {}
            
            # 월별 그룹화
            self.trades_df['year_month'] = self.trades_df['exit_date'].dt.to_period('M')
            monthly_data = self.trades_df.groupby('year_month').agg({
                'return_pct': ['sum', 'mean', 'count', 'min', 'max', 'std']
            }).round(4)
            
            monthly_data.columns = ['total_return', 'avg_return', 'trade_count', 
                                    'min_return', 'max_return', 'std_return']
            
            # 통계
            months = monthly_data.index.tolist()
            total_returns = monthly_data['total_return'].values
            
            monthly_stats = {
                'months': len(months),
                'total_months': len(months),
                'positive_months': int((total_returns > 0).sum()),
                'negative_months': int((total_returns < 0).sum()),
                'zero_months': int((total_returns == 0).sum()),
                'avg_monthly_return': float(monthly_data['total_return'].mean()),
                'std_monthly_return': float(monthly_data['total_return'].std()),
                'max_monthly_return': float(monthly_data['total_return'].max()),
                'min_monthly_return': float(monthly_data['total_return'].min()),
                'monthly_consistency': float(monthly_data['total_return'].std() / abs(monthly_data['total_return'].mean() + 0.0001))
                if monthly_data['total_return'].mean() != 0 else float('inf')
            }
            
            return monthly_stats
        
        except Exception as e:
            print(f"⚠️ 월별 성과 분석 실패: {e}")
            return {}
    
    def analyze_quarterly_performance(self) -> Dict[str, Any]:
        """
        분기별 성과 분석
        
        Returns:
        --------
        dict
            분기별 성과 통계
        """
        # 분기별 그룹화
        self.trades_df['year_quarter'] = self.trades_df['exit_date'].dt.to_period('Q')
        quarterly_data = self.trades_df.groupby('year_quarter').agg({
            'return_pct': ['sum', 'mean', 'count']
        }).round(4)
        
        quarterly_data.columns = ['total_return', 'avg_return', 'trade_count']
        
        quarterly_stats = {
            'quarters': len(quarterly_data),
            'positive_quarters': int((quarterly_data['total_return'] > 0).sum()),
            'negative_quarters': int((quarterly_data['total_return'] < 0).sum()),
            'avg_quarterly_return': float(quarterly_data['total_return'].mean()),
            'max_quarterly_return': float(quarterly_data['total_return'].max()),
            'min_quarterly_return': float(quarterly_data['total_return'].min())
        }
        
        return quarterly_stats
    
    def analyze_yearly_performance(self) -> Dict[str, Any]:
        """
        연도별 성과 분석
        
        Returns:
        --------
        dict
            연도별 성과 통계
        """
        # 연도별 그룹화
        self.trades_df['year'] = self.trades_df['exit_date'].dt.year
        yearly_data = self.trades_df.groupby('year').agg({
            'return_pct': ['sum', 'mean', 'count']
        }).round(4)
        
        yearly_data.columns = ['total_return', 'avg_return', 'trade_count']
        
        yearly_stats = {
            'years': len(yearly_data),
            'positive_years': int((yearly_data['total_return'] > 0).sum()),
            'negative_years': int((yearly_data['total_return'] < 0).sum()),
            'avg_yearly_return': float(yearly_data['total_return'].mean()),
            'max_yearly_return': float(yearly_data['total_return'].max()),
            'min_yearly_return': float(yearly_data['total_return'].min())
        }
        
        return yearly_stats
    
    # ========== 1-2. 연속성 분석 ==========
    def analyze_consecutive_trades(self) -> Dict[str, Any]:
        """
        연속 승/패 분석
        
        Returns:
        --------
        dict
            연속성 통계
        """
        # 거래 결과 (승/패)
        trades_list = self.trades_df['return_pct'].values
        
        # 연속 승리 찾기
        max_consecutive_wins = self._get_max_consecutive(trades_list > 0)
        max_consecutive_losses = self._get_max_consecutive(trades_list <= 0)
        
        # 연속 승리의 평균 길이
        consecutive_wins_lengths = self._get_all_consecutive_lengths(trades_list > 0)
        consecutive_losses_lengths = self._get_all_consecutive_lengths(trades_list <= 0)
        
        consecutive_stats = {
            'max_consecutive_wins': int(max_consecutive_wins),
            'max_consecutive_losses': int(max_consecutive_losses),
            'avg_consecutive_wins': float(np.mean(consecutive_wins_lengths)) if consecutive_wins_lengths else 0,
            'avg_consecutive_losses': float(np.mean(consecutive_losses_lengths)) if consecutive_losses_lengths else 0,
            'psychological_pressure': float(max_consecutive_losses),  # 심리 압박도
            'psychological_pressure_score': self._calculate_psychological_pressure(
                max_consecutive_losses, 
                len(trades_list)
            )
        }
        
        return consecutive_stats
    
    @staticmethod
    def _get_max_consecutive(condition: np.ndarray) -> int:
        """연속된 True의 최대 길이"""
        if len(condition) == 0:
            return 0
        
        max_count = 0
        current_count = 0
        
        for item in condition:
            if item:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    @staticmethod
    def _get_all_consecutive_lengths(condition: np.ndarray) -> List[int]:
        """모든 연속된 구간의 길이"""
        lengths = []
        current_count = 0
        
        for item in condition:
            if item:
                current_count += 1
            else:
                if current_count > 0:
                    lengths.append(current_count)
                current_count = 0
        
        if current_count > 0:
            lengths.append(current_count)
        
        return lengths
    
    @staticmethod
    def _calculate_psychological_pressure(max_consecutive_losses: int, total_trades: int) -> float:
        """
        심리 압박도 계산 (0~100점)
        
        max_consecutive_losses가 많을수록 높은 점수
        """
        if total_trades == 0:
            return 0.0
        
        # 비율
        ratio = max_consecutive_losses / total_trades
        
        # 심리 압박도 = 비율 × 100
        pressure_score = min(ratio * 100, 100)
        
        return pressure_score
    
    # ========== 1-3. 보유기간 분석 ==========
    def analyze_holding_period(self) -> Dict[str, Any]:
        """
        보유기간 분석
        
        Returns:
        --------
        dict
            보유기간 통계
        """
        # entry_date, exit_date 필요
        if 'entry_date' not in self.trades_df.columns:
            return {'error': 'entry_date 컬럼 없음'}
        
        self.trades_df['entry_date'] = pd.to_datetime(self.trades_df['entry_date'])
        self.trades_df['holding_period_hours'] = (
            (self.trades_df['exit_date'] - self.trades_df['entry_date']).dt.total_seconds() / 3600
        )
        
        holding_periods = self.trades_df['holding_period_hours'].values
        
        holding_stats = {
            'avg_holding_hours': float(holding_periods.mean()),
            'median_holding_hours': float(np.median(holding_periods)),
            'min_holding_hours': float(holding_periods.min()),
            'max_holding_hours': float(holding_periods.max()),
            'std_holding_hours': float(holding_periods.std()),
            'holding_consistency': float(1 - (holding_periods.std() / (holding_periods.mean() + 0.0001)))
        }
        
        # 보유기간별 수익률
        holding_stats['correlation_holding_profit'] = float(
            self.trades_df['holding_period_hours'].corr(self.trades_df['return_pct'])
        )
        
        return holding_stats
    
    # ========== 1-4. 거래 밀도 분석 ==========
    def analyze_trade_density(self) -> Dict[str, Any]:
        """
        거래 밀도 분석
        
        Returns:
        --------
        dict
            거래 밀도 통계
        """
        total_trades = len(self.trades_df)
        
        # 일일 평균
        daily_avg = total_trades / self.total_days if self.total_days > 0 else 0
        
        # 월별 평균
        monthly_avg = total_trades / (self.total_days / 30) if self.total_days > 0 else 0
        
        # 주별 평균
        weekly_avg = total_trades / (self.total_days / 7) if self.total_days > 0 else 0
        
        # 일별 거래 분포
        self.trades_df['trade_date'] = self.trades_df['exit_date'].dt.date
        daily_counts = self.trades_df.groupby('trade_date').size()
        
        density_stats = {
            'daily_avg_trades': float(daily_avg),
            'monthly_avg_trades': float(monthly_avg),
            'weekly_avg_trades': float(weekly_avg),
            'max_trades_per_day': int(daily_counts.max()),
            'min_trades_per_day': int(daily_counts.min()),
            'avg_trades_per_day': float(daily_counts.mean()),
            'std_trades_per_day': float(daily_counts.std()),
            'overtrading_status': self._classify_overtrading(daily_avg),
            'total_trades': total_trades,
            'trading_days': len(daily_counts)
        }
        
        return density_stats
    
    @staticmethod
    def _classify_overtrading(daily_avg: float) -> str:
        """과매매 여부 판정"""
        if daily_avg > 2.0:
            return "🚫 극도의 과매매"
        elif daily_avg > 1.0:
            return "⚠️ 과매매 경고"
        elif daily_avg >= 0.1:
            return "✅ 정상 범위"
        elif daily_avg > 0.05:
            return "⚠️ 거래 부족 경고"
        else:
            return "🚫 거래 부족"
    
    # ========== 1-5. Equity Curve 분석 ==========
    # 1-5. Equity Curve 분석
    def analyze_equity_curve(self) -> Dict[str, Any]:
        """
        누적 수익 곡선 분석
        
        Returns:
        --------
        dict
            Equity Curve 통계
        """
        # 누적 수익률 계산
        cumulative_returns = (1 + self.trades_df['return_pct'] / 100).cumprod() - 1
        equity_curve = cumulative_returns * 100  # 백분율로 변환
        
        # 기본 통계
        equity_stats = {
            'final_return': float(equity_curve.iloc[-1]) if len(equity_curve) > 0 else 0,
            'max_equity': float(equity_curve.max()),
            'min_equity': float(equity_curve.min()),
            'mean_equity': float(equity_curve.mean()),
            'std_equity': float(equity_curve.std()),
            'smoothness_ratio': self._calculate_smoothness(equity_curve)
        }
        
        # 상승/하락/횡보 구간 분석
        daily_changes = equity_curve.diff()
        
        uptrend_days = (daily_changes > 0).sum()
        downtrend_days = (daily_changes < 0).sum()
        sideways_days = (daily_changes == 0).sum()
        
        equity_stats['uptrend_days'] = int(uptrend_days)
        equity_stats['downtrend_days'] = int(downtrend_days)
        equity_stats['sideways_days'] = int(sideways_days)
        equity_stats['uptrend_ratio'] = float(uptrend_days / len(daily_changes)) if len(daily_changes) > 0 else 0
        
        # 드로우다운 분석 (올바른 공식)
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / (running_max + 0.0001)  # 소수로 계산
        
        equity_stats['max_drawdown_pct'] = float(drawdown.min() * 100)  # 여기서만 × 100
        equity_stats['avg_drawdown_pct'] = float(drawdown.mean() * 100)
        equity_stats['drawdown_days'] = int((drawdown < 0).sum())
        
        return equity_stats
    
    @staticmethod
    def _calculate_smoothness(equity_curve: pd.Series) -> float:
        """
        Equity Curve의 부드러움 정도 (0~1)
        
        값이 클수록 부드러움 (변동성 낮음)
        """
        if len(equity_curve) < 2:
            return 0.0
        
        # 일일 변화
        daily_changes = equity_curve.diff().dropna()
        
        if len(daily_changes) == 0 or daily_changes.std() == 0:
            return 1.0
        
        # 부드러움 = 1 - (표준편차 / 평균절대값)
        smoothness = 1 - (daily_changes.std() / (daily_changes.abs().mean() + 0.0001))
        
        return max(0.0, min(1.0, smoothness))
    
    # ========== 모든 분석 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        시계열 분석 5개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 분석 결과
        """
        results = {
            '1-1_monthly': self.analyze_monthly_performance(),
            '1-2_consecutive': self.analyze_consecutive_trades(),
            '1-3_holding_period': self.analyze_holding_period(),
            '1-4_trade_density': self.analyze_trade_density(),
            '1-5_equity_curve': self.analyze_equity_curve()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    dummy_df = pd.DataFrame({
        'entry_date': dates,
        'exit_date': dates + pd.Timedelta(days=1),
        'return_pct': np.random.randn(100) * 2 + 1
    })
    
    analyzer = TimeSeriesAnalyzer(
        dummy_df,
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-12-31')
    )
    
    results = analyzer.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))