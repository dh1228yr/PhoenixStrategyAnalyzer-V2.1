"""
06_advanced_stats.py - 고급 통계 모듈

고급 통계 (3개 항목):
8-1. 수익 기울기 검정
8-2. 자기상관 검정
8-3. 이분산성 검정
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy import stats
from scipy.stats import f_oneway


class AdvancedStatistics:
    """고급 통계 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
        """
        self.trades_df = trades_df.copy()
        self.returns = trades_df['return_pct'].values
    
    # ========== 8-1. 수익 기울기 검정 ==========
    def test_profit_slope(self) -> Dict[str, Any]:
        """
        누적 수익 곡선의 기울기가 유의미한가?
        
        선형 회귀를 통해 수익 곡선의 추세를 검정
        
        Returns:
        --------
        dict
            수익 기울기 검정 결과
        """
        # 누적 수익률
        cumulative_returns = (1 + self.returns / 100).cumprod() - 1
        cumulative_returns_pct = cumulative_returns * 100
        
        # x축: 거래 번호
        x = np.arange(len(cumulative_returns_pct))
        y = cumulative_returns_pct
        
        # 선형 회귀
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        slope = z[0]
        intercept = z[1]
        
        # R² 계산
        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # t-검정 (기울기 ≠ 0)
        t_stat, p_value = self._regression_t_test(x, y, slope)
        
        # 표준오차
        mse = np.sum((y - y_pred) ** 2) / (len(y) - 2) if len(y) > 2 else 0
        ss_x = np.sum((x - x.mean()) ** 2)
        se_slope = np.sqrt(mse / ss_x) if ss_x > 0 else 0
        
        # 신뢰 구간 (95%)
        t_critical = stats.t.ppf(0.975, len(y) - 2)
        ci_lower = slope - t_critical * se_slope
        ci_upper = slope + t_critical * se_slope
        
        slope_stats = {
            'slope': float(slope),
            'slope_per_trade': float(slope),
            'annual_slope': float(slope * 252),
            'intercept': float(intercept),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'p_value_significant': p_value < 0.05,
            'r_squared': float(r_squared),
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'standard_error': float(se_slope),
            'trend_direction': '우상향' if slope > 0 else '하향',
            'trend_strength': self._interpret_slope(r_squared),
            'expected_total_return': float(slope * len(y))
        }
        
        return slope_stats
    
    @staticmethod
    def _regression_t_test(x: np.ndarray, y: np.ndarray, slope: float) -> Tuple[float, float]:
        """회귀선 기울기 t-검정"""
        n = len(x)
        
        if n < 3:
            return 0.0, 1.0
        
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        ss_x = np.sum((x - x_mean) ** 2)
        ss_y = np.sum((y - y_mean) ** 2)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        
        # 예측값
        y_pred = slope * x + (y_mean - slope * x_mean)
        
        # 잔차
        residuals = y - y_pred
        mse = np.sum(residuals ** 2) / (n - 2) if n > 2 else 0
        
        # 기울기 표준오차
        se_slope = np.sqrt(mse / ss_x) if ss_x > 0 else 0
        
        # t-통계량
        t_stat = slope / se_slope if se_slope > 0 else 0
        
        # p-value (양측)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
        return t_stat, p_value
    
    @staticmethod
    def _interpret_slope(r_squared: float) -> str:
        """추세 강도 해석"""
        if r_squared >= 0.8:
            return "매우 강한 상향 추세"
        elif r_squared >= 0.6:
            return "강한 상향 추세"
        elif r_squared >= 0.4:
            return "중간 정도 추세"
        elif r_squared >= 0.2:
            return "약한 추세"
        else:
            return "추세 불명확"
    
    # ========== 8-2. 자기상관 검정 ==========
    def test_autocorrelation(self, lags: int = 10) -> Dict[str, Any]:
        """
        거래 수익률의 자기상관 검정
        
        Durbin-Watson 검정과 ACF 계산
        
        Parameters:
        -----------
        lags : int
            검정할 래그 수
        
        Returns:
        --------
        dict
            자기상관 검정 결과
        """
        returns = self.returns / 100  # 소수로 변환
        
        # Durbin-Watson 검정
        dw_stat = self._durbin_watson(returns)
        
        # 자기상관계수 (ACF)
        acf_values = self._calculate_acf(returns, lags)
        
        # Ljung-Box 검정
        lb_stat, lb_pvalue = self._ljung_box_test(returns, lags)
        
        autocorr_stats = {
            'durbin_watson_stat': float(dw_stat),
            'dw_interpretation': self._interpret_dw(dw_stat),
            'ljung_box_stat': float(lb_stat),
            'ljung_box_pvalue': float(lb_pvalue),
            'autocorrelation_significant': lb_pvalue < 0.05,
            'acf_values': [float(x) for x in acf_values],
            'acf_lags': list(range(lags + 1)),
            'significant_lags': [i for i in range(lags + 1) if abs(acf_values[i]) > 1.96 / np.sqrt(len(returns))],
            'independence_assessment': 'Yes' if lb_pvalue > 0.05 else 'No',
            'meaning': '거래 수익이 독립적이면 좋음 (시스템이 일관적)'
        }
        
        return autocorr_stats
    
    @staticmethod
    def _durbin_watson(residuals: np.ndarray) -> float:
        """Durbin-Watson 통계량 계산"""
        diff = np.diff(residuals)
        dw = np.sum(diff ** 2) / np.sum(residuals ** 2) if np.sum(residuals ** 2) > 0 else 0
        return dw
    
    @staticmethod
    def _calculate_acf(series: np.ndarray, nlags: int) -> np.ndarray:
        """자기상관계수 (ACF) 계산"""
        c0 = np.mean((series - np.mean(series)) ** 2)
        acf = np.zeros(nlags + 1)
        acf[0] = 1.0
        
        for k in range(1, nlags + 1):
            c_k = np.mean((series[:-k] - np.mean(series)) * (series[k:] - np.mean(series)))
            acf[k] = c_k / c0 if c0 > 0 else 0
        
        return acf
    
    @staticmethod
    def _ljung_box_test(series: np.ndarray, lags: int) -> Tuple[float, float]:
        """Ljung-Box 검정"""
        n = len(series)
        acf = AdvancedStatistics._calculate_acf(series, lags)
        
        # Ljung-Box 통계량
        lb = n * (n + 2) * np.sum((acf[1:] ** 2) / (n - np.arange(1, lags + 1)))
        
        # p-value
        p_value = 1 - stats.chi2.cdf(lb, lags)
        
        return lb, p_value
    
    @staticmethod
    def _interpret_dw(dw_stat: float) -> str:
        """Durbin-Watson 해석"""
        if dw_stat < 1.5:
            return "양의 자기상관 (의존성 있음)"
        elif dw_stat < 2.5:
            return "자기상관 없음 (독립적)"
        else:
            return "음의 자기상관 (반대 의존성)"
    
    # ========== 8-3. 이분산성 검정 ==========
    def test_heteroscedasticity(self) -> Dict[str, Any]:
        """
        이분산성 검정 (변동성이 시간에 따라 변하는가?)
        
        Breusch-Pagan 검정 사용
        
        Returns:
        --------
        dict
            이분산성 검정 결과
        """
        returns = self.returns / 100  # 소수로 변환
        
        # 누적 수익
        cumulative_returns = (1 + returns).cumprod() - 1
        
        # 회귀: 수익 ~ 누적 수익
        x = cumulative_returns.reshape(-1, 1)
        y = returns
        
        # 최소제곱 회귀
        x_with_const = np.column_stack([np.ones(len(x)), x])
        beta = np.linalg.lstsq(x_with_const, y, rcond=None)[0]
        
        # 잔차
        residuals = y - (beta[0] + beta[1] * cumulative_returns)
        squared_residuals = residuals ** 2
        
        # Breusch-Pagan 검정
        bp_stat, bp_pvalue = self._breusch_pagan(cumulative_returns, squared_residuals)
        
        # 변동성 변화 분석 (rolling std)
        window = min(10, len(returns) // 5)
        rolling_std = pd.Series(returns).rolling(window=window).std()
        
        std_of_std = rolling_std.std()
        mean_std = rolling_std.mean()
        volatility_change_ratio = std_of_std / mean_std if mean_std > 0 else 0
        
        hetero_stats = {
            'breusch_pagan_stat': float(bp_stat),
            'breusch_pagan_pvalue': float(bp_pvalue),
            'heteroscedasticity_significant': bp_pvalue < 0.05,
            'volatility_change_ratio': float(volatility_change_ratio),
            'volatility_stable': bp_pvalue > 0.05,
            'rolling_std_mean': float(mean_std),
            'rolling_std_std': float(std_of_std),
            'interpretation': '변동성이 일정' if bp_pvalue > 0.05 else '변동성이 변함',
            'meaning': '변동성이 일정하면 포지션 사이징이 일관적으로 적용 가능'
        }
        
        return hetero_stats
    
    @staticmethod
    def _breusch_pagan(x: np.ndarray, squared_residuals: np.ndarray) -> Tuple[float, float]:
        """Breusch-Pagan 검정"""
        n = len(x)
        
        # 잔차 제곱을 x에 회귀
        x_with_const = np.column_stack([np.ones(n), x])
        
        beta = np.linalg.lstsq(x_with_const, squared_residuals, rcond=None)[0]
        fitted = beta[0] + beta[1] * x.flatten()
        
        # SSR과 SST
        mean_sq_res = squared_residuals.mean()
        ssr = np.sum((fitted - mean_sq_res) ** 2)
        sst = np.sum((squared_residuals - mean_sq_res) ** 2)
        
        # LM 통계량
        lm_stat = (ssr / sst) * (n / 2) if sst > 0 else 0
        
        # p-value
        p_value = 1 - stats.chi2.cdf(lm_stat, 1)
        
        return lm_stat, p_value
    
    # ========== 모든 검정 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        고급 통계 3개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 검정 결과
        """
        results = {
            '8-1_profit_slope': self.test_profit_slope(),
            '8-2_autocorrelation': self.test_autocorrelation(),
            '8-3_heteroscedasticity': self.test_heteroscedasticity()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1
    })
    
    stats_analyzer = AdvancedStatistics(dummy_df)
    results = stats_analyzer.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))
