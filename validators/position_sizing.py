"""
05_position_sizing.py - 포지션 최적화 모듈

포지션 최적화 (3개 항목):
7-3. 위험 조정 성과 순위 (Sharpe/Sortino/Calmar)
9-1. Kelly Criterion 계산
9-3. Sharpe 기반 동적 로트
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy import stats


class PositionSizer:
    """포지션 사이징 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame, risk_free_rate: float = 0.02):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
        risk_free_rate : float
            무위험 수익률 (연간, 기본값: 2%)
        """
        self.trades_df = trades_df.copy()
        self.risk_free_rate = risk_free_rate
        self.returns = trades_df['return_pct'].values / 100  # 소수로 변환
    
    # ========== 7-3. 위험 조정 성과 순위 ==========
    def rank_risk_adjusted_returns(self) -> Dict[str, Any]:
        """
        위험 조정 성과 지표 계산
        
        - Sharpe Ratio
        - Sortino Ratio
        - Calmar Ratio
        
        Returns:
        --------
        dict
            위험 조정 성과 지표
        """
        returns = self.returns
        
        # 기본 통계
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Sharpe Ratio = (평균 수익 - 무위험율) / 표준편차
        # 연간 기준으로 정규화
        annual_return = mean_return * 252  # 거래일 기준
        annual_std = std_return * np.sqrt(252)
        
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_std if annual_std > 0 else 0
        
        # Sortino Ratio = (평균 수익 - 무위험율) / 하락 표준편차
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        annual_downside_std = downside_std * np.sqrt(252)
        
        sortino_ratio = (annual_return - self.risk_free_rate) / annual_downside_std if annual_downside_std > 0 else 0
        
        # Calmar Ratio = 연간 수익 / 최대 드로우다운
        cumulative_returns = (1 + returns).cumprod() - 1
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (running_max + 0.0001)
        max_drawdown = abs(drawdown.min())
        
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        risk_adjusted_stats = {
            'sharpe_ratio': float(sharpe_ratio),
            'sortino_ratio': float(sortino_ratio),
            'calmar_ratio': float(calmar_ratio),
            'mean_return': float(mean_return * 100),
            'std_return': float(std_return * 100),
            'annual_return': float(annual_return * 100),
            'annual_volatility': float(annual_std * 100),
            'max_drawdown': float(max_drawdown * 100),
            'rank': self._rank_performance(sharpe_ratio, sortino_ratio, calmar_ratio)
        }
        
        return risk_adjusted_stats
    
    @staticmethod
    def _rank_performance(sharpe: float, sortino: float, calmar: float) -> Dict[str, Any]:
        """성과 순위 판정"""
        scores = [sharpe, sortino, calmar]
        avg_score = np.mean(scores)
        
        if avg_score > 2.0:
            rank = "상위 10% (매우 우수)"
        elif avg_score > 1.5:
            rank = "상위 25% (우수)"
        elif avg_score > 1.0:
            rank = "상위 50% (양호)"
        elif avg_score > 0.5:
            rank = "평균 (보통)"
        else:
            rank = "하위 25% (개선 필요)"
        
        return {
            'average_score': float(avg_score),
            'rank': rank
        }
    
    # ========== 9-1. Kelly Criterion ==========
    def calculate_kelly(self) -> Dict[str, Any]:
        """
        Kelly Criterion 계산
        
        최적 로트 비율 = (승률 × 평균승 + 패율 × 평균패) / 평균승
        
        Returns:
        --------
        dict
            Kelly Criterion 통계
        """
        returns = self.returns * 100  # 백분율로 변환
        
        # 승리/손실 거래
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        win_rate = len(wins) / len(returns) if len(returns) > 0 else 0
        loss_rate = len(losses) / len(returns) if len(returns) > 0 else 0
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        
        # Kelly Criterion
        # f = (p × b - q) / b
        # p = 승률, q = 패율, b = 평균승/평균패
        
        if avg_loss > 0:
            b = avg_win / avg_loss
            kelly_pct = (win_rate * b - loss_rate) / b if b > 0 else 0
        else:
            kelly_pct = 0
        
        # 보수적 Kelly (fractional Kelly)
        fractional_kelly = kelly_pct / 2  # 절반 Kelly
        
        # 필요 최소 거래 수
        required_trades = self._calculate_required_trades_for_kelly(win_rate)
        
        kelly_stats = {
            'full_kelly_pct': float(max(0, kelly_pct * 100)),
            'fractional_kelly_pct': float(max(0, fractional_kelly * 100)),
            'recommended_kelly_pct': float(max(0, fractional_kelly * 100)),
            'win_rate': float(win_rate * 100),
            'loss_rate': float(loss_rate * 100),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'win_loss_ratio': float(avg_win / avg_loss) if avg_loss > 0 else 0,
            'total_trades': len(returns),
            'required_trades_for_significance': int(required_trades),
            'kelly_feasibility': 'OK' if len(returns) >= required_trades else 'Not Enough Trades',
            'caution': 'Full Kelly는 과도한 변동성. Fractional Kelly 권장'
        }
        
        return kelly_stats
    
    @staticmethod
    def _calculate_required_trades_for_kelly(win_rate: float) -> float:
        """Kelly Criterion 적용을 위한 필요 거래 수"""
        # 최소 30-50 거래 필요 (표본 크기)
        # win_rate가 0.5에 가까울수록 더 많은 거래 필요
        
        min_trades = 30
        adjustment = abs(win_rate - 0.5) * 20  # win_rate가 극단적일수록 적음
        
        required = max(min_trades, min_trades - adjustment)
        
        return required
    
    # ========== 9-3. Sharpe 기반 동적 로트 ==========
    def calculate_dynamic_lot(self, base_lot_pct: float = 1.0, period_days: int = 20) -> Dict[str, Any]:
        """
        Sharpe Ratio 기반 동적 로트 계산
        
        Sharpe가 높은 기간에는 로트를 증가, 낮은 기간에는 감소
        
        Parameters:
        -----------
        base_lot_pct : float
            기본 로트 비율
        period_days : int
            로트 조정 기간 (거래 수 기준)
        
        Returns:
        --------
        dict
            동적 로트 통계
        """
        returns = self.returns * 100
        
        # 기간별로 나누기
        total_trades = len(returns)
        n_periods = max(1, total_trades // period_days)
        
        period_sharpes = []
        period_lot_multipliers = []
        
        for i in range(n_periods):
            start_idx = i * period_days
            end_idx = min((i + 1) * period_days, total_trades)
            
            period_returns = returns[start_idx:end_idx]
            
            if len(period_returns) > 0:
                period_mean = period_returns.mean()
                period_std = period_returns.std()
                
                # Sharpe 계산
                annual_return = period_mean * 252 / len(period_returns)
                annual_std = period_std * np.sqrt(252)
                
                period_sharpe = (annual_return - self.risk_free_rate) / annual_std if annual_std > 0 else 0
                period_sharpes.append(period_sharpe)
                
                # 로트 멀티플라이어 결정
                if period_sharpe > 2.0:
                    multiplier = 1.0  # 정상
                elif period_sharpe > 1.5:
                    multiplier = 0.8  # 감소
                elif period_sharpe > 1.0:
                    multiplier = 0.6  # 감소
                elif period_sharpe > 0.5:
                    multiplier = 0.4  # 크게 감소
                else:
                    multiplier = 0.2  # 극도로 감소
                
                period_lot_multipliers.append(multiplier)
        
        period_sharpes = np.array(period_sharpes)
        period_lot_multipliers = np.array(period_lot_multipliers)
        
        dynamic_stats = {
            'base_lot_pct': float(base_lot_pct),
            'period_days': period_days,
            'n_periods': n_periods,
            'avg_period_sharpe': float(period_sharpes.mean()) if len(period_sharpes) > 0 else 0,
            'period_sharpes': [float(x) for x in period_sharpes],
            'period_lot_multipliers': [float(x) for x in period_lot_multipliers],
            'avg_multiplier': float(period_lot_multipliers.mean()) if len(period_lot_multipliers) > 0 else 0,
            'max_lot_pct': float(base_lot_pct * period_lot_multipliers.max()) if len(period_lot_multipliers) > 0 else 0,
            'min_lot_pct': float(base_lot_pct * period_lot_multipliers.min()) if len(period_lot_multipliers) > 0 else 0,
            'recommended_lot_pct': float(base_lot_pct * period_lot_multipliers.mean()) if len(period_lot_multipliers) > 0 else base_lot_pct
        }
        
        return dynamic_stats
    
    # ========== 모든 분석 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        포지션 최적화 3개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 분석 결과
        """
        results = {
            '7-3_risk_adjusted': self.rank_risk_adjusted_returns(),
            '9-1_kelly': self.calculate_kelly(),
            '9-3_dynamic_lot': self.calculate_dynamic_lot()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1
    })
    
    sizer = PositionSizer(dummy_df)
    results = sizer.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))
