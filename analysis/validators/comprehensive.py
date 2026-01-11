"""
comprehensive.py - 종합평가 시스템

16개 검증 시스템을 통합하여:
1. 모든 분석 결과 수집
2. 배제 조건 (Tier 1/2/3) 검사
3. 최종 점수 계산 (8개 카테고리)
4. 종합 판정
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime

from .timeseries import TimeSeriesAnalyzer
from .statistics import StatisticalTester
from .trade_analysis import TradeAnalyzer
from .extreme_scenario import ExtremeScenarioAnalyzer
from .position_sizing import PositionSizer
from .advanced_stats import AdvancedStatistics


class ComprehensiveEvaluator:
    """16개 검증 시스템을 통합하는 평가자"""
    
    def __init__(
        self,
        trades_df: pd.DataFrame,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        initial_capital: float = 50.0
    ):
        """
        초기화
        
        Parameters:
        -----------
        trades_df : pd.DataFrame
            거래 데이터프레임
        start_date : pd.Timestamp
            백테스트 시작일
        end_date : pd.Timestamp
            백테스트 종료일
        initial_capital : float
            초기 자본금 (기본값: 50달러)
        """
        self.trades_df = trades_df.copy()
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.total_days = (end_date - start_date).days
        self.total_trades = len(trades_df)
        
        # 계산된 기본 통계
        self.win_rate = (trades_df['return_pct'] > 0).sum() / len(trades_df) if len(trades_df) > 0 else 0
        self.total_return = trades_df['return_pct'].sum()
        
        # 종료일 기반 계산
        if 'exit_date' in trades_df.columns:
            trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
            trading_days = trades_df['exit_date'].nunique()
        else:
            trading_days = self.total_days
        
        self.trading_days = trading_days
    
    # ========== 1단계: 모든 검증 시스템 실행 ==========
    def run_all_validators(self) -> Dict[str, Any]:
        """
        16개 검증 시스템 모두 실행
        
        Returns:
        --------
        dict
            모든 검증 결과
        """
        results = {}
        
        try:
            # 1. 시계열 분석 (5개)
            ts_analyzer = TimeSeriesAnalyzer(
                self.trades_df,
                self.start_date,
                self.end_date
            )
            results['timeseries'] = ts_analyzer.run_all()
        except Exception as e:
            print(f"⚠️ 시계열 분석 실패: {e}")
            results['timeseries'] = {}
        
        try:
            # 2. 통계 검정 (4개)
            stat_tester = StatisticalTester(self.trades_df)
            results['statistics'] = stat_tester.run_all()
        except Exception as e:
            print(f"⚠️ 통계 검정 실패: {e}")
            results['statistics'] = {}
        
        try:
            # 3. 거래 분석 (2개)
            trade_analyzer = TradeAnalyzer(self.trades_df)
            results['trade_analysis'] = trade_analyzer.run_all()
        except Exception as e:
            print(f"⚠️ 거래 분석 실패: {e}")
            results['trade_analysis'] = {}
        
        try:
            # 4. 극한 상황 (5개)
            extreme_analyzer = ExtremeScenarioAnalyzer(
                self.trades_df,
                self.initial_capital
            )
            results['extreme_scenario'] = extreme_analyzer.run_all()
        except Exception as e:
            print(f"⚠️ 극한 상황 분석 실패: {e}")
            results['extreme_scenario'] = {}
        
        try:
            # 5. 포지션 최적화 (3개)
            position_sizer = PositionSizer(self.trades_df)
            results['position_sizing'] = position_sizer.run_all()
        except Exception as e:
            print(f"⚠️ 포지션 최적화 실패: {e}")
            results['position_sizing'] = {}
        
        try:
            # 6. 고급 통계 (3개)
            advanced_stats = AdvancedStatistics(self.trades_df)
            results['advanced_stats'] = advanced_stats.run_all()
        except Exception as e:
            print(f"⚠️ 고급 통계 실패: {e}")
            results['advanced_stats'] = {}
        
        self.validator_results = results
        return results
    
    # ========== 2단계: 배제 조건 검사 ==========
    def check_disqualification_criteria(self) -> Dict[str, Any]:
        """
        배제 조건 검사 (Tier 1/2/3)
        
        Returns:
        --------
        dict
            배제 조건 판정 결과
        """
        tier1_reasons = []
        tier2_reasons = []
        tier3_warnings = []
        
        # ===== Tier 1: 즉시 중단 =====
        
        # 1-1. 거래 수 < 30
        if self.total_trades < 30:
            tier1_reasons.append(f"거래 수 < 30 ({self.total_trades}건)")
        
        # 1-2. Walk-Forward 점수 (기존 분석에서 가져옴, 현재는 생략)
        # 1-3. 승률 < 50%
        if self.win_rate < 0.5:
            tier1_reasons.append(f"승률 < 50% ({self.win_rate*100:.1f}%)")

        # 1-4. 최대 드로우다운 > -50%
        # 올바른 드로우다운 계산: 자본금 곡선 기준
        if '누적 손익 %' in self.trades_df.columns:
            # 누적 손익 %를 자본금 곡선으로 변환
            cumulative_pct = self.trades_df['누적 손익 %'].values
            capital_curve = self.initial_capital * (1 + cumulative_pct / 100)
        else:
            # 없으면 개별 수익률로 계산
            returns = self.trades_df['return_pct'].values / 100
            capital_curve = self.initial_capital * np.cumprod(1 + returns)
        
        # Running max (자본금 기준)
        running_max = np.maximum.accumulate(capital_curve)
        
        # 드로우다운 계산
        drawdown = np.zeros_like(capital_curve)
        mask = running_max > 0
        drawdown[mask] = (capital_curve[mask] - running_max[mask]) / running_max[mask]
        
        max_drawdown = drawdown.min()
        print(f"DEBUG: capital_curve[-1] = {capital_curve[-1]:.2f}, max = {capital_curve.max():.2f}")
        print(f"DEBUG: max_drawdown = {max_drawdown:.6f} ({max_drawdown*100:.2f}%)")
        
        if max_drawdown < -0.5:
            tier1_reasons.append(f"최대 드로우다운 > -50% ({max_drawdown*100:.1f}%)")
        
        # 1-5. 거래 기간 < 6개월
        if self.total_days < 180:
            tier1_reasons.append(f"거래 기간 < 6개월 ({self.total_days}일)")
        
        # ===== Tier 2: 높은 위험 =====
        
        # 2-1. p-value ≥ 0.05
        if 'statistics' in self.validator_results:
            stat_results = self.validator_results['statistics']
            if '2-1_win_rate' in stat_results:
                p_value = stat_results['2-1_win_rate'].get('p_value', 0)
                if p_value >= 0.05:
                    tier2_reasons.append(f"p-value ≥ 0.05 ({p_value:.4f})")
        
        # 2-2. Sharpe < 1.0
        if 'position_sizing' in self.validator_results:
            pos_results = self.validator_results['position_sizing']
            if '7-3_risk_adjusted' in pos_results:
                sharpe = pos_results['7-3_risk_adjusted'].get('sharpe_ratio', 0)
                if sharpe < 1.0:
                    tier2_reasons.append(f"Sharpe < 1.0 ({sharpe:.2f})")
        
        # 2-3. 손실 월 ≥ 5개월 → Tier 3로 이동
        # (삭제됨)
        
        # 2-4. 최대 연속 손실 ≥ 7일
        if 'timeseries' in self.validator_results:
            ts_results = self.validator_results['timeseries']
            if '1-2_consecutive' in ts_results:
                max_consec_loss = ts_results['1-2_consecutive'].get('max_consecutive_losses', 0)
                if max_consec_loss >= 7:
                    tier2_reasons.append(f"최대 연속 손실 ≥ 7일 ({max_consec_loss}일)")
        
        # 2-5. 월별 편차 > 200% → Tier 3로 이동
        # (삭제됨)
        
        # 2-6. 평균 손실/거래 > 3%
        if 'trade_analysis' in self.validator_results:
            trade_results = self.validator_results['trade_analysis']
            if '3-1_win_loss_comparison' in trade_results:
                trade_data = trade_results['3-1_win_loss_comparison']
                if 'losing_trades' in trade_data:
                    avg_loss = trade_data['losing_trades'].get('avg_return', 0)
                    if abs(avg_loss) > 3:
                        tier2_reasons.append(f"평균 손실/거래 > 3% ({abs(avg_loss):.2f}%)")
        
        # ===== Tier 3: 경고 =====
        
        # 3-1. 일일 거래 > 1건
        daily_avg = self.total_trades / self.total_days if self.total_days > 0 else 0
        if daily_avg > 1.0:
            tier3_warnings.append(f"⚠️ 일일 거래 > 1건 ({daily_avg:.2f})")
        
        # 3-2. 월 거래 < 2건
        monthly_avg = self.total_trades / (self.total_days / 30) if self.total_days > 0 else 0
        if monthly_avg < 2:
            tier3_warnings.append(f"⚠️ 월 거래 < 2건 ({monthly_avg:.1f})")
        
        # 3-3. 승/패 비율 < 1.5
        if 'trade_analysis' in self.validator_results:
            trade_results = self.validator_results['trade_analysis']
            if '3-1_win_loss_comparison' in trade_results:
                trade_data = trade_results['3-1_win_loss_comparison']
                if isinstance(trade_data, dict):
                    rr_ratio = trade_data.get('risk_reward_ratio', 0)
                    if rr_ratio < 1.5 and rr_ratio > 0:
                        tier3_warnings.append(f"⚠️ 승/패 비율 < 1.5 ({rr_ratio:.2f})")
        
        # 3-4. 손실 월 ≥ 5개월 (Tier 2에서 이동)
        if 'timeseries' in self.validator_results:
            ts_results = self.validator_results['timeseries']
            if '1-1_monthly' in ts_results:
                negative_months = ts_results['1-1_monthly'].get('negative_months', 0)
                if negative_months >= 5:
                    tier3_warnings.append(f"⚠️ 손실 월 ≥ 5개월 ({negative_months}개월)")
        
        # 3-5. 월별 편차 > 200% (Tier 2에서 이동)
        if 'timeseries' in self.validator_results:
            ts_results = self.validator_results['timeseries']
            if '1-1_monthly' in ts_results:
                monthly_cv = ts_results['1-1_monthly'].get('monthly_consistency', 0)
                if monthly_cv > 2.0:
                    tier3_warnings.append(f"⚠️ 월별 편차 > 200% (CV={monthly_cv:.2f})")
        
        # ===== 최종 판정 =====
        if tier1_reasons:
            status = '❌ NO-GO'
            tier = 'Tier 1'
            reasons = tier1_reasons
        elif tier2_reasons:
            status = '❌ NO-GO'
            tier = 'Tier 2'
            reasons = tier2_reasons
        elif tier3_warnings:
            status = '✅ GO (조건부)'
            tier = 'Tier 3'
            reasons = tier3_warnings
        else:
            status = '✅ GO (강력 추천)'
            tier = 'All Clear'
            reasons = []
        
        disqualification = {
            'status': status,
            'tier': tier,
            'reasons': reasons,
            'total_trades': self.total_trades,
            'win_rate': float(self.win_rate * 100),
            'max_drawdown': float(max_drawdown),
            'trading_period_days': self.total_days
        }
        
        self.disqualification = disqualification
        return disqualification
    
    # ========== 3단계: 최종 점수 계산 ==========
    def generate_final_score(self) -> Dict[str, Any]:
        """
        최종 점수 계산 (8개 카테고리)
        
        Returns:
        --------
        dict
            최종 점수 및 등급
        """
        scores = {}
        
        # 1. 백테스트 성과 (100점 기준)
        # = 승률 × 50 + 수익률/40 × 50
        win_rate_score = min(self.win_rate * 100, 100)  # 0-100
        return_score = min((self.total_return / 40) * 100, 100) if self.total_return > 0 else 0  # 0-100
        backtest_score = (win_rate_score * 0.5) + (return_score * 0.5)
        scores['백테스트 성과'] = min(backtest_score, 100)
        
        # 2. Walk-Forward (기존 분석에서 가져옴, 현재는 기본값)
        scores['Walk-Forward'] = 75  # 기존 분석 필요
        
        # 3. 시계열 안정성
        if 'timeseries' in self.validator_results and '1-1_monthly' in self.validator_results['timeseries']:
            ts_results = self.validator_results['timeseries']['1-1_monthly']
            monthly_cv = ts_results.get('monthly_consistency', 1)
            # CV가 작을수록 좋음 (일관성)
            stability_score = max(0, 100 * (1 - min(monthly_cv, 1)))
            scores['시계열 안정성'] = stability_score
        else:
            scores['시계열 안정성'] = 50
        
        # 4. 통계 신뢰도
        if 'statistics' in self.validator_results and '2-1_win_rate' in self.validator_results['statistics']:
            stat_results = self.validator_results['statistics']['2-1_win_rate']
            p_value = stat_results.get('p_value', 0.5)
            # p-value가 작을수록 좋음
            if p_value < 0.001:
                confidence_score = 100
            elif p_value < 0.01:
                confidence_score = 90
            elif p_value < 0.05:
                confidence_score = 80
            elif p_value < 0.1:
                confidence_score = 60
            else:
                confidence_score = 30
            scores['통계 신뢰도'] = confidence_score
        else:
            scores['통계 신뢰도'] = 50
        
        # 5. 거래 특성
        if 'trade_analysis' in self.validator_results and '3-1_win_loss_comparison' in self.validator_results['trade_analysis']:
            trade_results = self.validator_results['trade_analysis']['3-1_win_loss_comparison']
            pf = trade_results.get('profit_factor', 1)
            # Profit Factor > 2.0이면 100점
            trade_score = min(pf * 50, 100)
            scores['거래 특성'] = trade_score
        else:
            scores['거래 특성'] = 50
        
        # 6. 극한 상황 (생존성)
        if 'extreme_scenario' in self.validator_results and '4-4_capital_shortage' in self.validator_results['extreme_scenario']:
            extreme_results = self.validator_results['extreme_scenario']['4-4_capital_shortage']
            survived = extreme_results.get('survived', False)
            if survived:
                # 생존했으면, 마진 기반 점수
                margin = extreme_results.get('margin_of_safety', self.initial_capital)
                extreme_score = min((margin / self.initial_capital) * 100, 100)
            else:
                extreme_score = 0
            scores['극한 상황'] = extreme_score
        else:
            scores['극한 상황'] = 50
        
        # 7. 포지션 최적화
        if 'position_sizing' in self.validator_results and '7-3_risk_adjusted' in self.validator_results['position_sizing']:
            pos_results = self.validator_results['position_sizing']['7-3_risk_adjusted']
            sharpe = pos_results.get('sharpe_ratio', 0)
            # Sharpe > 2.0이면 100점
            pos_score = min((sharpe / 2.0) * 100, 100)
            scores['포지션 최적화'] = pos_score
        else:
            scores['포지션 최적화'] = 50
        
        # 8. 고급 통계
        if 'advanced_stats' in self.validator_results and '8-1_profit_slope' in self.validator_results['advanced_stats']:
            adv_results = self.validator_results['advanced_stats']['8-1_profit_slope']
            r_squared = adv_results.get('r_squared', 0)
            # R² > 0.8이면 100점
            adv_score = min(r_squared * 125, 100)
            scores['고급 통계'] = adv_score
        else:
            scores['고급 통계'] = 50
        
        # 최종 점수 계산
        final_score = np.mean(list(scores.values()))
        
        # 등급 판정
        if final_score >= 85:
            rating = '우수'
        elif final_score >= 75:
            rating = '양호'
        elif final_score >= 60:
            rating = '보통'
        else:
            rating = '개선필요'
        
        result = {
            'scores': scores,
            'final_score': float(final_score),
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        }
        
        self.final_score = result
        return result
    
    # ========== 4단계: 최종 종합 평가 ==========
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        최종 종합 평가 리포트
        
        Returns:
        --------
        dict
            모든 평가 결과를 포함한 종합 리포트
        """
        # 아직 실행하지 않았으면 실행
        if not hasattr(self, 'validator_results'):
            self.run_all_validators()
        
        if not hasattr(self, 'disqualification'):
            self.check_disqualification_criteria()
        
        if not hasattr(self, 'final_score'):
            self.generate_final_score()
        
        report = {
            'metadata': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'total_trades': self.total_trades,
                'trading_days': self.trading_days,
                'initial_capital': self.initial_capital,
                'timestamp': datetime.now().isoformat()
            },
            'disqualification': self.disqualification,
            'final_score': self.final_score,
            'validators': self.validator_results
        }
        
        return report
    
    # ========== 5단계: 한글 요약 ==========
    def get_summary(self) -> str:
        """
        종합 평가 한글 요약
        
        Returns:
        --------
        str
            읽기 쉬운 한글 요약
        """
        if not hasattr(self, 'final_score'):
            self.generate_final_score()
        
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║              종합평가 최종 리포트                               ║
╚════════════════════════════════════════════════════════════════╝

📊 기본 통계
═════════════════════════════════════════════════════════════════
  거래 수: {self.total_trades}건
  승률: {self.win_rate*100:.1f}%
  총 수익률: {self.total_return:.2f}%
  거래 기간: {self.total_days}일

🎯 자동매매 실전 투입 판정
═════════════════════════════════════════════════════════════════
  상태: {self.disqualification['status']}
  기준: {self.disqualification['tier']}
  {('이유: ' + ', '.join(self.disqualification['reasons'])) if self.disqualification['reasons'] else ''}

📈 최종 종합 점수
═════════════════════════════════════════════════════════════════
  최종 점수: {self.final_score['final_score']:.1f}점
  등급: {self.final_score['rating']}
  
  카테고리별 점수:
"""
        for category, score in self.final_score['scores'].items():
            summary += f"    • {category:15} : {score:6.1f}점\n"
        
        summary += "\n🚀 다음 단계\n"
        summary += "═" * 61 + "\n"
        
        if self.disqualification['status'] == '✅ GO (강력 추천)':
            summary += "  ✅ 실전 자동매매 강력 추천\n"
            summary += "  → 거래소 설정 → 자동매매 시작\n"
        elif '✅' in self.disqualification['status']:
            summary += "  ⚠️ 조건부 추천\n"
            summary += "  → 경고 항목 주의 후 진행\n"
        else:
            summary += "  ❌ 재검토 필요\n"
            summary += "  → 전략 개선 후 재분석\n"
        
        summary += "\n"
        return summary


# 테스트 코드
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    
    # 더미 데이터
    dummy_df = pd.DataFrame({
        'return_pct': np.random.randn(100) * 2 + 1.5,
        'entry_date': pd.date_range('2024-01-01', periods=100),
        'exit_date': pd.date_range('2024-01-02', periods=100),
        'runup_pct': np.random.randn(100) * 1 + 2,
        'drawdown_pct': np.random.randn(100) * 1 - 1
    })
    
    evaluator = ComprehensiveEvaluator(
        dummy_df,
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-12-31')
    )
    
    # 실행
    print("🔄 종합평가 실행 중...")
    evaluator.run_all_validators()
    evaluator.check_disqualification_criteria()
    evaluator.generate_final_score()
    
    # 출력
    print(evaluator.get_summary())