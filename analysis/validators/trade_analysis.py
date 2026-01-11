"""
03_trade_analysis.py - 거래 분석 모듈

거래 분석 (2개 항목):
3-1. 승리/손실 거래 비교
3-2. 거래 특성별 분류
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from scipy import stats


class TradeAnalyzer:
    """거래 분석 클래스"""
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
            필수 컬럼: return_pct, entry_date, exit_date, runup_pct, drawdown_pct
        """
        self.trades_df = trades_df.copy()
        self._normalize_columns()
    
    def _normalize_columns(self):
        """컬럼명 정규화"""
        column_mapping = {
            '거래 반환': 'return_pct',
            'Return': 'return_pct',
            '수익률': 'return_pct',
            'return_pct': 'return_pct',
            '날짜/시간': 'entry_date',
            'Date/Time': 'entry_date',
            'entry_date': 'entry_date',
            '종료일': 'exit_date',
            'exit_date': 'exit_date',
            'Runup': 'runup_pct',
            'runup_pct': 'runup_pct',
            'Drawdown': 'drawdown_pct',
            'drawdown_pct': 'drawdown_pct'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in self.trades_df.columns and new_col not in self.trades_df.columns:
                self.trades_df[new_col] = self.trades_df[old_col]
        
        # 날짜 변환
        if 'entry_date' in self.trades_df.columns:
            self.trades_df['entry_date'] = pd.to_datetime(self.trades_df['entry_date'])
        if 'exit_date' in self.trades_df.columns:
            self.trades_df['exit_date'] = pd.to_datetime(self.trades_df['exit_date'])
    
    # ========== 3-1. 승리/손실 거래 비교 ==========
    def compare_win_loss(self) -> Dict[str, Any]:
        """
        승리 거래와 손실 거래의 특성 비교
        
        Returns:
        --------
        dict
            승리/손실 거래 비교 통계
        """
        try:
            winning_trades = self.trades_df[self.trades_df['return_pct'] > 0]
            losing_trades = self.trades_df[self.trades_df['return_pct'] <= 0]
            
            # 보유기간 계산
            if 'entry_date' in self.trades_df.columns and 'exit_date' in self.trades_df.columns:
                self.trades_df['holding_hours'] = (
                    (self.trades_df['exit_date'] - self.trades_df['entry_date']).dt.total_seconds() / 3600
                )
            
            comparison_stats = {
                'winning_trades': {
                    'count': len(winning_trades),
                    'ratio': float(len(winning_trades) / len(self.trades_df)) if len(self.trades_df) > 0 else 0,
                    'avg_return': float(winning_trades['return_pct'].mean()) if len(winning_trades) > 0 else 0,
                    'median_return': float(winning_trades['return_pct'].median()) if len(winning_trades) > 0 else 0,
                    'min_return': float(winning_trades['return_pct'].min()) if len(winning_trades) > 0 else 0,
                    'max_return': float(winning_trades['return_pct'].max()) if len(winning_trades) > 0 else 0,
                    'std_return': float(winning_trades['return_pct'].std()) if len(winning_trades) > 0 else 0,
                },
                'losing_trades': {
                    'count': len(losing_trades),
                    'ratio': float(len(losing_trades) / len(self.trades_df)) if len(self.trades_df) > 0 else 0,
                    'avg_return': float(losing_trades['return_pct'].mean()) if len(losing_trades) > 0 else 0,
                    'median_return': float(losing_trades['return_pct'].median()) if len(losing_trades) > 0 else 0,
                    'min_return': float(losing_trades['return_pct'].min()) if len(losing_trades) > 0 else 0,
                    'max_return': float(losing_trades['return_pct'].max()) if len(losing_trades) > 0 else 0,
                    'std_return': float(losing_trades['return_pct'].std()) if len(losing_trades) > 0 else 0,
                }
            }
            
            # Runup/Drawdown 비교
            if 'runup_pct' in self.trades_df.columns:
                comparison_stats['winning_trades']['avg_runup'] = float(
                    winning_trades['runup_pct'].mean() if len(winning_trades) > 0 else 0
                )
                comparison_stats['losing_trades']['avg_runup'] = float(
                    losing_trades['runup_pct'].mean() if len(losing_trades) > 0 else 0
                )
            
            if 'drawdown_pct' in self.trades_df.columns:
                comparison_stats['winning_trades']['avg_drawdown'] = float(
                    winning_trades['drawdown_pct'].mean() if len(winning_trades) > 0 else 0
                )
                comparison_stats['losing_trades']['avg_drawdown'] = float(
                    losing_trades['drawdown_pct'].mean() if len(losing_trades) > 0 else 0
                )
            
            # 보유기간 비교
            if 'holding_hours' in self.trades_df.columns:
                comparison_stats['winning_trades']['avg_holding_hours'] = float(
                    winning_trades['holding_hours'].mean() if len(winning_trades) > 0 else 0
                )
                comparison_stats['losing_trades']['avg_holding_hours'] = float(
                    losing_trades['holding_hours'].mean() if len(losing_trades) > 0 else 0
                )
            
            # Risk-Reward 비율
            avg_win = abs(comparison_stats['winning_trades']['avg_return'])
            avg_loss = abs(comparison_stats['losing_trades']['avg_return'])
            
            comparison_stats['risk_reward_ratio'] = float(
                avg_win / avg_loss if avg_loss > 0 else 0
            )
            comparison_stats['profit_factor'] = float(
                (avg_win * len(winning_trades)) / (avg_loss * len(losing_trades))
                if len(losing_trades) > 0 and avg_loss > 0 else 0
            )
            
            return comparison_stats
        
        except Exception as e:
            print(f"⚠️ 승/패 비교 분석 실패: {e}")
            return {}
    
    # ========== 3-2. 거래 특성별 분류 ==========
    def classify_trades(self) -> Dict[str, Any]:
        """
        거래를 특성별로 분류
        
        - 수익/손실 규모별
        - 보유기간별
        - 수익률 범위별
        
        Returns:
        --------
        dict
            거래 분류 통계
        """
        try:
            returns = self.trades_df['return_pct'].values
            
            # 수익/손실 규모별 분류
            tiny_profit = (returns > 0) & (returns <= 1)
            small_profit = (returns > 1) & (returns <= 3)
            medium_profit = (returns > 3) & (returns <= 10)
            large_profit = (returns > 10)
            
            tiny_loss = (returns < 0) & (returns >= -1)
            small_loss = (returns < -1) & (returns >= -3)
            large_loss = (returns < -3)
            
            size_classification = {
                'tiny_profit_0_1': {
                    'count': int(tiny_profit.sum()),
                    'ratio': float(tiny_profit.sum() / len(returns)),
                    'avg_return': float(returns[tiny_profit].mean()) if tiny_profit.sum() > 0 else 0
                },
                'small_profit_1_3': {
                    'count': int(small_profit.sum()),
                    'ratio': float(small_profit.sum() / len(returns)),
                    'avg_return': float(returns[small_profit].mean()) if small_profit.sum() > 0 else 0
                },
                'medium_profit_3_10': {
                    'count': int(medium_profit.sum()),
                    'ratio': float(medium_profit.sum() / len(returns)),
                    'avg_return': float(returns[medium_profit].mean()) if medium_profit.sum() > 0 else 0
                },
                'large_profit_10_plus': {
                    'count': int(large_profit.sum()),
                    'ratio': float(large_profit.sum() / len(returns)),
                    'avg_return': float(returns[large_profit].mean()) if large_profit.sum() > 0 else 0
                },
                'tiny_loss_0_1': {
                    'count': int(tiny_loss.sum()),
                    'ratio': float(tiny_loss.sum() / len(returns)),
                    'avg_return': float(returns[tiny_loss].mean()) if tiny_loss.sum() > 0 else 0
                },
                'small_loss_1_3': {
                    'count': int(small_loss.sum()),
                    'ratio': float(small_loss.sum() / len(returns)),
                    'avg_return': float(returns[small_loss].mean()) if small_loss.sum() > 0 else 0
                },
                'large_loss_3_plus': {
                    'count': int(large_loss.sum()),
                    'ratio': float(large_loss.sum() / len(returns)),
                    'avg_return': float(returns[large_loss].mean()) if large_loss.sum() > 0 else 0
                }
            }
            
            # 보유기간별 분류
            if 'holding_hours' in self.trades_df.columns:
                holding = self.trades_df['holding_hours'].values
                
                scalp = holding < 1  # 1시간 미만
                short_term = (holding >= 1) & (holding < 24)  # 1~24시간
                medium_term = (holding >= 24) & (holding < 168)  # 1~7일
                long_term = holding >= 168  # 7일 이상
                
                holding_classification = {
                    'scalp_lt1h': {
                        'count': int(scalp.sum()),
                        'ratio': float(scalp.sum() / len(holding)),
                        'avg_return': float(returns[scalp].mean()) if scalp.sum() > 0 else 0
                    },
                    'short_1h_24h': {
                        'count': int(short_term.sum()),
                        'ratio': float(short_term.sum() / len(holding)),
                        'avg_return': float(returns[short_term].mean()) if short_term.sum() > 0 else 0
                    },
                    'medium_1d_7d': {
                        'count': int(medium_term.sum()),
                        'ratio': float(medium_term.sum() / len(holding)),
                        'avg_return': float(returns[medium_term].mean()) if medium_term.sum() > 0 else 0
                    },
                    'long_7d_plus': {
                        'count': int(long_term.sum()),
                        'ratio': float(long_term.sum() / len(holding)),
                        'avg_return': float(returns[long_term].mean()) if long_term.sum() > 0 else 0
                    }
                }
            else:
                holding_classification = {}
            
            classification = {
                'size_classification': size_classification,
                'holding_classification': holding_classification
            }
            
            return classification
        
        except Exception as e:
            print(f"⚠️ 거래 분류 분석 실패: {e}")
            return {}
    
    # ========== 추가: 거래 특성 요약 ==========
    def get_trade_summary(self) -> Dict[str, Any]:
        """
        거래 특성 요약
        
        Returns:
        --------
        dict
            거래 특성 요약
        """
        comparison = self.compare_win_loss()
        classification = self.classify_trades()
        
        summary = {
            'total_trades': len(self.trades_df),
            'win_rate': float((self.trades_df['return_pct'] > 0).sum() / len(self.trades_df)),
            'profit_factor': comparison.get('profit_factor', 0),
            'risk_reward_ratio': comparison.get('risk_reward_ratio', 0),
            'winning_trades': comparison['winning_trades']['count'],
            'losing_trades': comparison['losing_trades']['count'],
            'avg_win': comparison['winning_trades']['avg_return'],
            'avg_loss': comparison['losing_trades']['avg_return'],
            'largest_win': comparison['winning_trades']['max_return'],
            'largest_loss': comparison['losing_trades']['min_return'],
            'classification': classification
        }
        
        return summary
    
    # ========== 모든 분석 통합 실행 ==========
    def run_all(self) -> Dict[str, Any]:
        """
        거래 분석 2개 항목 모두 실행
        
        Returns:
        --------
        dict
            모든 분석 결과
        """
        results = {
            '3-1_win_loss_comparison': self.compare_win_loss(),
            '3-2_classification': self.classify_trades(),
            'trade_summary': self.get_trade_summary()
        }
        
        return results


# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1,
        'entry_date': pd.date_range('2024-01-01', periods=100),
        'exit_date': pd.date_range('2024-01-02', periods=100),
        'runup_pct': np.random.randn(100) * 1 + 2,
        'drawdown_pct': np.random.randn(100) * 1 - 1
    })
    
    analyzer = TradeAnalyzer(dummy_df)
    results = analyzer.run_all()
    
    import json
    print(json.dumps(results, indent=2, default=str))