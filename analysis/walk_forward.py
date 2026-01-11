"""
Walk-Forward Analysis
Train/Test 분할 및 과적합 검증

핵심 기능:
1. Train/Test 분할 (시간 순서 유지)
2. 각 구간 성과 지표 계산
3. Train vs Test 비교
4. 과적합 점수 산출
5. 실전 투입 판정
"""

import pandas as pd
import numpy as np

class WalkForwardAnalyzer:
    """Walk-Forward 분석"""
    
    def __init__(self, trades_df, train_ratio=0.7):
        """
        Parameters:
        -----------
        trades_df : DataFrame
            거래 데이터 (exit_date 순 정렬 필수)
        train_ratio : float
            Train 비율 (기본 70%)
        """
        self.trades = trades_df.sort_values('exit_date').reset_index(drop=True)
        self.train_ratio = train_ratio
        self.split_idx = None
        self.train_trades = None
        self.test_trades = None
        
    def split(self):
        """Train/Test 분할"""
        total_trades = len(self.trades)
        self.split_idx = int(total_trades * self.train_ratio)
        
        self.train_trades = self.trades.iloc[:self.split_idx].copy()
        self.test_trades = self.trades.iloc[self.split_idx:].copy()
        
        return self.train_trades, self.test_trades
    
    def calculate_metrics(self, trades_df):
        """성과 지표 계산"""
        if len(trades_df) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_return': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_win': 0,
                'max_loss': 0,
                'max_drawdown': 0,
                'profit_factor': 0,
                'start_date': None,
                'end_date': None
            }
        
        total = len(trades_df)
        wins = len(trades_df[trades_df['return_pct'] > 0])
        losses = len(trades_df[trades_df['return_pct'] < 0])
        
        win_rate = wins / total * 100 if total > 0 else 0
        
        total_return = trades_df['return_pct'].sum()
        avg_return = trades_df['return_pct'].mean()
        
        win_trades = trades_df[trades_df['return_pct'] > 0]['return_pct']
        loss_trades = trades_df[trades_df['return_pct'] < 0]['return_pct']
        
        avg_win = win_trades.mean() if len(win_trades) > 0 else 0
        avg_loss = loss_trades.mean() if len(loss_trades) > 0 else 0
        
        max_win = trades_df['return_pct'].max()
        max_loss = trades_df['return_pct'].min()
        
        # Profit Factor
        gross_profit = win_trades.sum() if len(win_trades) > 0 else 0
        gross_loss = abs(loss_trades.sum()) if len(loss_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 최대 낙폭 계산
        cumulative = (1 + trades_df['return_pct'] / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_dd = drawdown.min()
        
        return {
            'total_trades': total,
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_return': avg_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'max_drawdown': max_dd,
            'profit_factor': profit_factor,
            'start_date': trades_df['entry_date'].min(),
            'end_date': trades_df['exit_date'].max()
        }
    
    def compare_metrics(self, train_metrics, test_metrics):
        """Train vs Test 비교"""
        
        # 승률 차이
        win_rate_diff = test_metrics['win_rate'] - train_metrics['win_rate']
        
        # 수익률 차이 (%)
        if train_metrics['avg_return'] != 0:
            return_diff_pct = (test_metrics['avg_return'] - train_metrics['avg_return']) / abs(train_metrics['avg_return']) * 100
        else:
            return_diff_pct = 0
        
        # 낙폭 비율
        if train_metrics['max_drawdown'] != 0:
            dd_ratio = abs(test_metrics['max_drawdown'] / train_metrics['max_drawdown'])
        else:
            dd_ratio = 1.0
        
        # Profit Factor 차이
        pf_diff = test_metrics['profit_factor'] - train_metrics['profit_factor']
        
        return {
            'win_rate_diff': win_rate_diff,
            'return_diff_pct': return_diff_pct,
            'dd_ratio': dd_ratio,
            'pf_diff': pf_diff
        }
    
    def judge_overfit(self, comparison):
        """과적합 판정"""
        score = 0
        judgments = {}
        
        # 1. 승률 차이 판정 (30점)
        win_rate_diff = abs(comparison['win_rate_diff'])
        
        if win_rate_diff < 5:
            judgments['win_rate'] = "✅ 우수 (차이 < 5%)"
            score += 30
        elif win_rate_diff < 10:
            judgments['win_rate'] = "⚠️ 보통 (차이 5~10%)"
            score += 20
        else:
            judgments['win_rate'] = "❌ 불안정 (차이 > 10%)"
            score += 0
        
        # 2. 수익률 차이 판정 (30점)
        return_diff = abs(comparison['return_diff_pct'])
        
        if return_diff < 20:
            judgments['return'] = "✅ 우수 (차이 < 20%)"
            score += 30
        elif return_diff < 50:
            judgments['return'] = "⚠️ 보통 (차이 20~50%)"
            score += 20
        else:
            judgments['return'] = "❌ 불안정 (차이 > 50%)"
            score += 0
        
        # 3. 낙폭 비율 판정 (40점)
        dd_ratio = comparison['dd_ratio']
        
        if dd_ratio < 2.0:
            judgments['drawdown'] = "✅ 우수 (비율 < 2배)"
            score += 40
        elif dd_ratio < 3.0:
            judgments['drawdown'] = "⚠️ 보통 (비율 2~3배)"
            score += 25
        else:
            judgments['drawdown'] = "❌ 불안정 (비율 > 3배)"
            score += 0
        
        return score, judgments
    
    def analyze(self):
        """전체 분석 실행"""
        # 분할
        self.split()
        
        # 메트릭 계산
        train_metrics = self.calculate_metrics(self.train_trades)
        test_metrics = self.calculate_metrics(self.test_trades)
        
        # 비교
        comparison = self.compare_metrics(train_metrics, test_metrics)
        
        # 판정
        overfit_score, judgments = self.judge_overfit(comparison)
        
        # 최종 판정
        if overfit_score >= 80:
            final_judgment = "✅ 실전 투입 가능 (과적합 낮음)"
        elif overfit_score >= 60:
            final_judgment = "⚠️ 조건부 승인 (주의 필요)"
        else:
            final_judgment = "❌ 재최적화 필요 (과적합 높음)"
        
        return {
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'comparison': comparison,
            'overfit_score': overfit_score,
            'judgments': judgments,
            'final_judgment': final_judgment
        }


if __name__ == "__main__":
    print("✅ WalkForwardAnalyzer 모듈 로드 완료")