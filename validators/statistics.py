"""
02_statistics.py - 통계 검정 모듈

통계 검정 (4개 항목):
2-1. 승률 통계 신뢰도 (이항분포 검정)
2-2. 수익률 유의성 (t-검정)
2-3. 분포 분석 (정규성, 왜도, 첨도)
2-4. 손실 꼬리 리스크 (VaR, CVaR)
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Any
from scipy.stats import binom, t


class StatisticalTester:
    """통계 검정 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
            필수 컬럼: return_pct (또는 profit_loss)
        """
        self.trades_df = trades_df.copy()
        self._normalize_columns()
        
        self.returns = self.trades_df['return_pct'].values
        self.n_trades = len(self.returns)
        self.win_rate = (self.returns > 0).sum() / self.n_trades if self.n_trades > 0 else 0
    
    def _normalize_columns(self):
        """컬럼명 정규화"""
        column_mapping = {
            '거래 반환': 'return_pct',
            'Return': 'return_pct',
            '수익률': 'return_pct',
            'return_pct': 'return_pct',
            'profit_loss': 'return_pct'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in self.trades_df.columns and new_col not in self.trades_df.columns:
                self.trades_df[new_col] = self.trades_df[old_col]
    
    # ========== 2-1. 승률 통계 신뢰도 ==========
    def test_win_rate_confidence(self, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        승률의 통계적 신뢰도 검정
        
        이항분포 검정을 사용하여 관측된 승률이 통계적으로 유의미한지 판정
        
        Parameters:
        -----------
        confidence_level : float
            신뢰 수준 (기본값: 95%)
        
        Returns:
        --------
        dict
            승률 신뢰도 통계
        """
        wins = (self.returns > 0).sum()
        losses = (self.returns <= 0).sum()
        
        # 이항분포 검정 (귀무가설: p = 0.5)
        # H0: 승률 = 50% (동전 던지기와 동일)
        # H1: 승률 ≠ 50% (동전 던지기와 다름)
        
        p_value = binom.sf(wins - 1, self.n_trades, 0.5) * 2  # 양측 검정
        
        # 신뢰 구간 계산 (Wilson Score)
        ci_lower, ci_upper = self._wilson_ci(wins, self.n_trades, confidence_level)
        
        # Z-score 계산
        p_null = 0.5
        std_error = np.sqrt(p_null * (1 - p_null) / self.n_trades)
        z_score = (self.win_rate - p_null) / std_error if std_error > 0 else 0
        
        # 필요 표본 수 (50% 승률 vs 관측 승률)
        required_trades = self._calculate_required_sample_size(self.win_rate, 0.5)
        
        win_rate_stats = {
            'observed_win_rate': float(self.win_rate),
            'observed_win_rate_pct': float(self.win_rate * 100),
            'wins': int(wins),
            'losses': int(losses),
            'total_trades': self.n_trades,
            'p_value': float(p_value),
            'p_value_significant': p_value < 0.05,
            'confidence_level': confidence_level,
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'ci_range_pct': float((ci_upper - ci_lower) * 100),
            'z_score': float(z_score),
            'confidence_assessment': self._assess_confidence(p_value),
            'required_trades_for_significance': int(required_trades)
        }
        
        return win_rate_stats
    
    @staticmethod
    def _wilson_ci(wins: int, n: int, confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Wilson Score 신뢰 구간 계산
        
        이항분포의 신뢰 구간을 더 정확하게 계산
        """
        p_hat = wins / n if n > 0 else 0
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2*n)) / denominator
        spread = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4*n**2)) / denominator
        
        return max(0, center - spread), min(1, center + spread)
    
    @staticmethod
    def _calculate_required_sample_size(p1: float, p2: float, alpha: float = 0.05, beta: float = 0.20) -> float:
        """
        필요 표본 수 계산 (두 비율 비교)
        
        Parameters:
        -----------
        p1 : float
            그룹 1의 비율
        p2 : float
            그룹 2의 비율
        alpha : float
            유의 수준
        beta : float
            검정력 (1 - beta)
        """
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(1 - beta)
        
        p_pool = (p1 + p2) / 2
        
        n = (z_alpha + z_beta)**2 * (2 * p_pool * (1 - p_pool)) / (p1 - p2)**2
        
        return max(0, n)
    
    @staticmethod
    def _assess_confidence(p_value: float) -> str:
        """신뢰도 평가"""
        if p_value < 0.001:
            return "매우 높음 (***)"
        elif p_value < 0.01:
            return "높음 (**)"
        elif p_value < 0.05:
            return "중간 (*)"
        else:
            return "낮음"
    
    # ========== 2-2. 수익률 유의성 ==========
    def test_profit_significance(self) -> Dict[str, Any]:
        """
        수익률의 통계적 유의성 검정
        
        일일 수익률이 0보다 크다는 것을 검정
        
        Returns:
        --------
        dict
            수익률 유의성 통계
        """
        # 일일 수익률
        daily_returns = self.returns
        
        # t-검정 (귀무가설: 평균 = 0)
        t_stat, p_value = stats.ttest_1samp(daily_returns, 0)
        
        # 평균과 표준편차
        mean_return = daily_returns.mean()
        std_return = daily_returns.std()
        se_return = std_return / np.sqrt(len(daily_returns)) if len(daily_returns) > 0 else 0
        
        # 신뢰 구간 (95%)
        ci_lower = mean_return - 1.96 * se_return
        ci_upper = mean_return + 1.96 * se_return
        
        # 효과 크기 (Cohen's d)
        cohens_d = mean_return / std_return if std_return > 0 else 0
        
        profit_stats = {
            'mean_return': float(mean_return),
            'std_return': float(std_return),
            'std_error': float(se_return),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'p_value_significant': p_value < 0.05,
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'cohens_d': float(cohens_d),
            'effect_size': self._interpret_cohens_d(cohens_d),
            'daily_positive_returns': int((daily_returns > 0).sum()),
            'daily_negative_returns': int((daily_returns < 0).sum()),
            'daily_neutral_returns': int((daily_returns == 0).sum())
        }
        
        return profit_stats
    
    @staticmethod
    def _interpret_cohens_d(d: float) -> str:
        """Cohen's d 해석"""
        d_abs = abs(d)
        if d_abs < 0.2:
            return "무시할 수 있는 수준"
        elif d_abs < 0.5:
            return "작은 효과"
        elif d_abs < 0.8:
            return "중간 효과"
        else:
            return "큰 효과"
    
    # ========== 2-3. 분포 분석 ==========
    def analyze_distribution(self) -> Dict[str, Any]:
        """
        수익률 분포 분석
        
        정규성, 왜도, 첨도 등
        
        Returns:
        --------
        dict
            분포 분석 통계
        """
        returns = self.returns
        
        # 기본 통계
        mean = returns.mean()
        median = np.median(returns)
        mode = stats.mode(returns, keepdims=True).mode[0]
        
        # 왜도 (Skewness)
        skewness = stats.skew(returns)
        
        # 첨도 (Kurtosis)
        kurtosis = stats.kurtosis(returns)
        
        # 정규성 검정 (Shapiro-Wilk)
        if len(returns) > 5000:
            # 데이터가 너무 크면 표본 추출
            sample = np.random.choice(returns, 5000, replace=False)
            shapiro_stat, shapiro_p = stats.shapiro(sample)
        else:
            shapiro_stat, shapiro_p = stats.shapiro(returns)
        
        # 정규성 검정 (Kolmogorov-Smirnov)
        ks_stat, ks_p = stats.kstest(returns, 'norm', args=(mean, returns.std()))
        
        # 분위수
        q1 = np.percentile(returns, 25)
        q3 = np.percentile(returns, 75)
        iqr = q3 - q1
        
        distribution_stats = {
            'mean': float(mean),
            'median': float(median),
            'mode': float(mode),
            'skewness': float(skewness),
            'skewness_interpretation': self._interpret_skewness(skewness),
            'kurtosis': float(kurtosis),
            'kurtosis_interpretation': self._interpret_kurtosis(kurtosis),
            'shapiro_wilk_stat': float(shapiro_stat),
            'shapiro_wilk_p': float(shapiro_p),
            'shapiro_wilk_normal': shapiro_p > 0.05,
            'kolmogorov_smirnov_stat': float(ks_stat),
            'kolmogorov_smirnov_p': float(ks_p),
            'q1': float(q1),
            'q3': float(q3),
            'iqr': float(iqr),
            'normality_assessment': self._assess_normality(shapiro_p, ks_p)
        }
        
        return distribution_stats
    
    @staticmethod
    def _interpret_skewness(skewness: float) -> str:
        """왜도 해석"""
        if abs(skewness) < 0.5:
            return "대칭"
        elif skewness > 0:
            return "우향 (우측 꼬리 길음)"
        else:
            return "좌향 (좌측 꼬리 길음)"
    
    @staticmethod
    def _interpret_kurtosis(kurtosis: float) -> str:
        """첨도 해석"""
        if kurtosis < -1:
            return "편평함 (극단값 적음)"
        elif kurtosis < 1:
            return "정규분포와 유사"
        else:
            return "뾰족함 (극단값 많음, Fat Tail)"
    
    @staticmethod
    def _assess_normality(shapiro_p: float, ks_p: float) -> str:
        """정규성 평가"""
        if shapiro_p > 0.05 and ks_p > 0.05:
            return "정규분포 (양쪽 검정 통과)"
        elif shapiro_p > 0.05 or ks_p > 0.05:
            return "부분적 정규분포"
        else:
            return "정규분포 아님"
    
    # ========== 2-4. 손실 꼬리 리스크 ==========
    def analyze_tail_risk(self, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        손실의 꼬리 리스크 분석
        
        VaR, CVaR, 극단 손실 등
        
        Parameters:
        -----------
        confidence_level : float
            신뢰 수준 (기본값: 95%)
        
        Returns:
        --------
        dict
            꼬리 리스크 통계
        """
        returns = self.returns
        losses = returns[returns < 0]
        
        # VaR (Value at Risk)
        var_percentile = 1 - confidence_level
        var_95 = np.percentile(returns, var_percentile * 100)
        
        # CVaR (Conditional VaR, Expected Shortfall)
        cvar_95 = losses[losses <= var_95].mean() if len(losses[losses <= var_95]) > 0 else losses.mean()
        
        # 극단 손실 통계
        worst_10_pct = np.percentile(returns, 10)
        worst_trades = returns[returns <= worst_10_pct]
        
        best_10_pct = np.percentile(returns, 90)
        best_trades = returns[returns >= best_10_pct]
        
        # Fat Tail 분석
        extreme_losses = losses[losses < returns.mean() - 2 * returns.std()]
        
        tail_risk_stats = {
            'var_95': float(var_95),
            'cvar_95': float(cvar_95),
            'worst_10_pct_return': float(worst_10_pct),
            'worst_10_pct_avg': float(worst_trades.mean()),
            'worst_10_pct_count': len(worst_trades),
            'best_10_pct_return': float(best_10_pct),
            'best_10_pct_avg': float(best_trades.mean()),
            'best_10_pct_count': len(best_trades),
            'extreme_loss_count': len(extreme_losses),
            'extreme_loss_avg': float(extreme_losses.mean()) if len(extreme_losses) > 0 else 0,
            'largest_loss': float(returns.min()),
            'loss_frequency': float((returns < 0).sum() / len(returns)),
            'fat_tail_ratio': float(len(extreme_losses) / len(losses)) if len(losses) > 0 else 0
        }
        
        return tail_risk_stats
    
    # ========== 모든 검정 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        통계 검정 4개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 검정 결과
        """
        results = {
            '2-1_win_rate': self.test_win_rate_confidence(),
            '2-2_profit': self.test_profit_significance(),
            '2-3_distribution': self.analyze_distribution(),
            '2-4_tail_risk': self.analyze_tail_risk()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1
    })
    
    tester = StatisticalTester(dummy_df)
    results = tester.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))
