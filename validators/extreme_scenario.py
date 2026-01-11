"""
04_extreme_scenario.py - 극한 상황 분석 모듈

극한 상황 분석 (5개 항목):
4-4. 자본 부족 시나리오 (50달러 생존성)
5-2. 부트스트랩 재샘플링
5-3. 극단값 분포
6-2. 자본 성장 경로 시뮬레이션
6-3. 자본 회귀선 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


class ExtremeScenarioAnalyzer:
    """극한 상황 분석 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame, initial_capital: float = 50.0):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
        initial_capital : float
            초기 자본금 (기본값: 50달러)
        """
        self.trades_df = trades_df.copy()
        self.initial_capital = initial_capital
        self.returns = trades_df['return_pct'].values / 100  # 소수로 변환
    
    # ========== 4-4. 자본 부족 시나리오 ==========
    def analyze_capital_shortage(self, fixed_lot_pct: float = 1.0) -> Dict[str, Any]:
        """
        자본 부족 시나리오: 50달러로 생존 가능한가?
        
        Parameters:
        -----------
        fixed_lot_pct : float
            고정 로트 (자본의 %)
        
        Returns:
        --------
        dict
            자본 생존성 분석
        """
        capital = self.initial_capital
        capital_history = [capital]
        
        for ret in self.returns:
            trade_size = capital * (fixed_lot_pct / 100)
            pnl = trade_size * ret
            capital += pnl
            capital_history.append(capital)
        
        capital_history = np.array(capital_history)
        
        shortage_stats = {
            'initial_capital': float(self.initial_capital),
            'final_capital': float(capital_history[-1]),
            'total_return_pct': float((capital_history[-1] - self.initial_capital) / self.initial_capital * 100),
            'min_capital': float(capital_history.min()),
            'max_capital': float(capital_history.max()),
            'capital_depletion': float(self.initial_capital - capital_history.min()),
            'capital_depletion_pct': float((self.initial_capital - capital_history.min()) / self.initial_capital * 100),
            'survived': capital_history.min() > 0,
            'survival_status': '✅ 생존' if capital_history.min() > 0 else '❌ 파산',
            'drawdown_from_initial': float((capital_history.min() - self.initial_capital) / self.initial_capital * 100),
            'trades_to_ruin': self._find_trades_to_ruin(capital_history),
            'margin_of_safety': float(capital_history.min())
        }
        
        return shortage_stats
    
    @staticmethod
    def _find_trades_to_ruin(capital_history: np.ndarray) -> int:
        """자산이 0 이하가 되는 거래 번호"""
        for i, capital in enumerate(capital_history):
            if capital <= 0:
                return i
        return -1  # 파산하지 않음
    
    # ========== 5-2. 부트스트랩 재샘플링 ==========
    def bootstrap_resampling(self, n_iterations: int = 1000, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        부트스트랩 재샘플링으로 수익률 신뢰 구간 계산
        
        Parameters:
        -----------
        n_iterations : int
            부트스트랩 반복 횟수
        confidence_level : float
            신뢰 수준
        
        Returns:
        --------
        dict
            부트스트랩 통계
        """
        bootstrap_means = []
        
        for _ in range(n_iterations):
            # 복원 추출
            sample = np.random.choice(self.returns, size=len(self.returns), replace=True)
            sample_mean = sample.mean()
            bootstrap_means.append(sample_mean * 100)  # 백분율
        
        bootstrap_means = np.array(bootstrap_means)
        
        # 신뢰 구간
        alpha = 1 - confidence_level
        lower_percentile = alpha / 2 * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_means, lower_percentile)
        ci_upper = np.percentile(bootstrap_means, upper_percentile)
        
        bootstrap_stats = {
            'n_iterations': n_iterations,
            'mean_return': float(np.mean(self.returns) * 100),
            'bootstrap_mean': float(bootstrap_means.mean()),
            'bootstrap_std': float(bootstrap_means.std()),
            'confidence_level': confidence_level,
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'ci_range': float(ci_upper - ci_lower),
            'standard_error': float(bootstrap_means.std()),
            'probability_positive_return': float((bootstrap_means > 0).sum() / n_iterations)
        }
        
        return bootstrap_stats
    
    # ========== 5-3. 극단값 분포 ==========
    def analyze_extreme_values(self, percentile: int = 10) -> Dict[str, Any]:
        """
        극단값 분포 분석 (최악/최고 10%)
        
        Parameters:
        -----------
        percentile : int
            분석할 상하 백분위수
        
        Returns:
        --------
        dict
            극단값 분석
        """
        returns_pct = self.returns * 100
        
        # 상위/하위 거래
        lower_bound = np.percentile(returns_pct, percentile)
        upper_bound = np.percentile(returns_pct, 100 - percentile)
        
        worst_trades = returns_pct[returns_pct <= lower_bound]
        best_trades = returns_pct[returns_pct >= upper_bound]
        
        extreme_stats = {
            'percentile': percentile,
            'worst_trades_count': len(worst_trades),
            'worst_trades_ratio': float(len(worst_trades) / len(returns_pct)),
            'worst_trades_avg': float(worst_trades.mean()),
            'worst_trades_min': float(worst_trades.min()),
            'worst_trades_max': float(worst_trades.max()),
            'worst_trades_std': float(worst_trades.std()),
            'best_trades_count': len(best_trades),
            'best_trades_ratio': float(len(best_trades) / len(returns_pct)),
            'best_trades_avg': float(best_trades.mean()),
            'best_trades_min': float(best_trades.min()),
            'best_trades_max': float(best_trades.max()),
            'best_trades_std': float(best_trades.std()),
            'extreme_ratio': float(best_trades.mean() / abs(worst_trades.mean())) if worst_trades.mean() != 0 else 0
        }
        
        return extreme_stats
    
    # ========== 6-2. 자본 성장 경로 시뮬레이션 ==========
    def simulate_capital_growth(self, fixed_lot_pct: float = 1.0, months_ahead: int = 12) -> Dict[str, Any]:
        """
        미래 자본 성장 경로 시뮬레이션
        
        Parameters:
        -----------
        fixed_lot_pct : float
            고정 로트 비율
        months_ahead : int
            몇 개월 앞을 시뮬레이션할지
        
        Returns:
        --------
        dict
            자본 성장 예측
        """
        # 월별 수익률 계산
        trades_per_month = len(self.returns) / 12 if len(self.returns) > 0 else 1
        monthly_return = np.mean(self.returns) * trades_per_month
        
        # 시뮬레이션
        simulated_capitals = [self.initial_capital]
        
        for month in range(months_ahead):
            current_capital = simulated_capitals[-1]
            
            # 해당 월의 수익
            month_pnl = current_capital * monthly_return
            new_capital = current_capital + month_pnl
            
            simulated_capitals.append(new_capital)
        
        simulated_capitals = np.array(simulated_capitals)
        
        # 95% 신뢰도 범위 (표준편차 기반)
        monthly_std = np.std(self.returns) * np.sqrt(trades_per_month)
        
        growth_stats = {
            'initial_capital': float(self.initial_capital),
            'expected_monthly_return': float(monthly_return * 100),
            'trades_per_month': float(trades_per_month),
            'simulated_months': months_ahead,
            'expected_final_capital': float(simulated_capitals[-1]),
            'expected_growth_pct': float((simulated_capitals[-1] - self.initial_capital) / self.initial_capital * 100),
            'monthly_progression': [float(c) for c in simulated_capitals],
            'confidence_upper_bound': float(simulated_capitals[-1] * (1 + monthly_std)),
            'confidence_lower_bound': float(simulated_capitals[-1] * (1 - monthly_std))
        }
        
        return growth_stats
    
    # ========== 6-3. 자본 회귀선 분석 ==========
    def analyze_capital_regression(self, fixed_lot_pct: float = 1.0) -> Dict[str, Any]:
        """
        자본 누적 곡선에 대한 회귀선 분석
        
        Parameters:
        -----------
        fixed_lot_pct : float
            고정 로트 비율
        
        Returns:
        --------
        dict
            회귀선 분석
        """
        # 자본 누적 곡선
        capital = self.initial_capital
        capital_history = [capital]
        
        for ret in self.returns:
            trade_size = capital * (fixed_lot_pct / 100)
            pnl = trade_size * ret
            capital += pnl
            capital_history.append(capital)
        
        capital_history = np.array(capital_history)
        
        # 회귀선
        x = np.arange(len(capital_history))
        y = capital_history
        
        # 선형 회귀
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        # R² 계산
        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # 기울기와 절편
        slope = z[0]
        intercept = z[1]
        
        # 기울기의 유의성 검정
        slope_pvalue = self._calculate_slope_pvalue(x, y, slope)
        
        regression_stats = {
            'slope': float(slope),
            'intercept': float(intercept),
            'slope_pvalue': float(slope_pvalue),
            'slope_significant': slope_pvalue < 0.05,
            'r_squared': float(r_squared),
            'r_value': float(np.sqrt(abs(r_squared))),
            'trend': '우상향' if slope > 0 else '하향',
            'trend_strength': self._interpret_r_squared(r_squared),
            'daily_expected_growth': float(slope),
            'annual_expected_growth': float(slope * 252)  # 거래일 기준
        }
        
        return regression_stats
    
    @staticmethod
    def _calculate_slope_pvalue(x: np.ndarray, y: np.ndarray, slope: float) -> float:
        """회귀선 기울기의 p-value 계산"""
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        ss_x = np.sum((x - x_mean) ** 2)
        ss_y = np.sum((y - y_mean) ** 2)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        
        # 회귀 표준오차
        residuals = y - (slope * x + np.mean(y) - slope * x_mean)
        mse = np.sum(residuals ** 2) / (n - 2)
        
        # 기울기 표준오차
        se_slope = np.sqrt(mse / ss_x) if ss_x > 0 else 0
        
        # t-통계량
        t_stat = slope / se_slope if se_slope > 0 else 0
        
        # p-value (양측)
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
        
        return p_value
    
    @staticmethod
    def _interpret_r_squared(r_squared: float) -> str:
        """R² 해석"""
        if r_squared >= 0.9:
            return "매우 강함 (선형 추세 명확)"
        elif r_squared >= 0.7:
            return "강함 (명확한 추세)"
        elif r_squared >= 0.5:
            return "중간 (어느 정도 추세)"
        elif r_squared >= 0.3:
            return "약함 (약한 추세)"
        else:
            return "매우 약함 (추세 불명확)"
    
    # ========== 모든 분석 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        극한 상황 분석 5개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 분석 결과
        """
        results = {
            '4-4_capital_shortage': self.analyze_capital_shortage(),
            '5-2_bootstrap': self.bootstrap_resampling(),
            '5-3_extreme_values': self.analyze_extreme_values(),
            '6-2_capital_growth': self.simulate_capital_growth(),
            '6-3_capital_regression': self.analyze_capital_regression()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1
    })
    
    analyzer = ExtremeScenarioAnalyzer(dummy_df, initial_capital=50)
    results = analyzer.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))
