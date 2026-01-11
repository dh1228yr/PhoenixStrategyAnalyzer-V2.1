"""
analysis_bridge.py - 기존 Phoenix와 16개 검증 시스템 통합

역할:
1. ReturnsConverter → validators 입력 변환
2. 16개 검증 실행 오케스트레이션
3. 결과 통합 및 캐싱
4. 에러 처리 및 대체 경로
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import json
import warnings

warnings.filterwarnings('ignore')


class AnalysisBridge:
    """기존 Phoenix와 16개 검증 시스템 브릿지"""
    
    def __init__(self, converter_instance, initial_capital: float = 50.0):
        """
        초기화
        
        Parameters:
        -----------
        converter_instance : ReturnsConverter
            기존 Phoenix의 ReturnsConverter 인스턴스
        initial_capital : float
            초기 자본금 (기본값: 50달러)
        """
        self.converter = converter_instance
        self.trades_df = converter_instance.trades
        self.initial_capital = initial_capital
        
        # 기본 통계
        self.start_date = self.trades_df['entry_date'].min()
        self.end_date = self.trades_df['exit_date'].max()
        
        # 결과 저장소
        self.results_cache = {}
    
    # ========== 16개 검증 로직 동적 로드 ==========
    def load_validators(self) -> Dict[str, Any]:
        """
        16개 검증 모듈 동적 로드
        
        Returns:
        --------
        dict
            로드된 검증 모듈
        """
        validators = {}
        
        try:
            from analysis.validators.timeseries import TimeSeriesAnalyzer
            validators['timeseries'] = TimeSeriesAnalyzer
        except ImportError:
            print("⚠️ TimeSeriesAnalyzer 로드 실패")
        
        try:
            from analysis.validators.statistics import StatisticalTester
            validators['statistics'] = StatisticalTester
        except ImportError:
            print("⚠️ StatisticalTester 로드 실패")
        
        try:
            from analysis.validators.trade_analysis import TradeAnalyzer
            validators['trade_analysis'] = TradeAnalyzer
        except ImportError:
            print("⚠️ TradeAnalyzer 로드 실패")
        
        try:
            from analysis.validators.extreme_scenario import ExtremeScenarioAnalyzer
            validators['extreme_scenario'] = ExtremeScenarioAnalyzer
        except ImportError:
            print("⚠️ ExtremeScenarioAnalyzer 로드 실패")
        
        try:
            from analysis.validators.position_sizing import PositionSizer
            validators['position_sizing'] = PositionSizer
        except ImportError:
            print("⚠️ PositionSizer 로드 실패")
        
        try:
            from analysis.validators.advanced_stats import AdvancedStatistics
            validators['advanced_stats'] = AdvancedStatistics
        except ImportError:
            print("⚠️ AdvancedStatistics 로드 실패")
        
        try:
            from analysis.validators.comprehensive import ComprehensiveEvaluator
            validators['comprehensive'] = ComprehensiveEvaluator
        except ImportError:
            print("⚠️ ComprehensiveEvaluator 로드 실패")
        
        return validators
    
    # ========== 16개 검증 실행 ==========
    def run_all_16_validators(self) -> Dict[str, Any]:
        """
        16개 검증 시스템 모두 실행
        
        Returns:
        --------
        dict
            모든 검증 결과
        """
        print("🔄 16개 검증 시스템 실행 중...\n")
        
        validators = self.load_validators()
        
        if not validators:
            print("❌ 검증 모듈을 로드할 수 없습니다.")
            return {'error': 'No validators loaded'}
        
        all_results = {}
        
        # 1. 시계열 분석 (5개)
        if 'timeseries' in validators:
            try:
                print("1️⃣ 시계열 분석 (1-1~1-5)...")
                ts = validators['timeseries'](
                    self.trades_df,
                    self.start_date,
                    self.end_date
                )
                all_results['1_timeseries'] = ts.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['1_timeseries'] = {}
        
        # 2. 통계 검정 (4개)
        if 'statistics' in validators:
            try:
                print("2️⃣ 통계 검정 (2-1~2-4)...")
                stat = validators['statistics'](self.trades_df)
                all_results['2_statistics'] = stat.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['2_statistics'] = {}
        
        # 3. 거래 분석 (2개)
        if 'trade_analysis' in validators:
            try:
                print("3️⃣ 거래 분석 (3-1~3-2)...")
                trade = validators['trade_analysis'](self.trades_df)
                all_results['3_trade_analysis'] = trade.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['3_trade_analysis'] = {}
        
        # 4. 극한 상황 (5개)
        if 'extreme_scenario' in validators:
            try:
                print("4️⃣ 극한 상황 분석 (4-4, 5-2~5-3, 6-2~6-3)...")
                extreme = validators['extreme_scenario'](
                    self.trades_df,
                    self.initial_capital
                )
                all_results['4_extreme_scenario'] = extreme.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['4_extreme_scenario'] = {}
        
        # 5. 포지션 최적화 (3개)
        if 'position_sizing' in validators:
            try:
                print("5️⃣ 포지션 최적화 (7-3, 9-1, 9-3)...")
                pos = validators['position_sizing'](self.trades_df)
                all_results['5_position_sizing'] = pos.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['5_position_sizing'] = {}
        
        # 6. 고급 통계 (3개)
        if 'advanced_stats' in validators:
            try:
                print("6️⃣ 고급 통계 (8-1~8-3)...")
                adv = validators['advanced_stats'](self.trades_df)
                all_results['6_advanced_stats'] = adv.run_all()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['6_advanced_stats'] = {}
        
        # 7. 종합평가
        if 'comprehensive' in validators:
            try:
                print("7️⃣ 종합평가 시스템...")
                comp = validators['comprehensive'](
                    self.trades_df,
                    self.start_date,
                    self.end_date,
                    self.initial_capital
                )
                comp.run_all_validators()
                comp.check_disqualification_criteria()
                comp.generate_final_score()
                all_results['7_comprehensive'] = comp.get_comprehensive_report()
                print("   ✅ 완료\n")
            except Exception as e:
                print(f"   ❌ 실패: {e}\n")
                all_results['7_comprehensive'] = {}
        
        self.results_cache = all_results
        return all_results
    
    # ========== 결과 요약 생성 ==========
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        16개 검증 결과 요약 리포트
        
        Returns:
        --------
        dict
            요약 리포트
        """
        if not self.results_cache:
            return {'error': '검증이 실행되지 않았습니다.'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': len(self.trades_df),
            'analysis_status': self._get_analysis_status(),
            'key_findings': self._extract_key_findings(),
            'risk_assessment': self._assess_risks(),
            'recommendation': self._get_recommendation(),
            'detailed_results': self.results_cache
        }
        
        return summary
    
    def _get_analysis_status(self) -> Dict[str, bool]:
        """분석 상태 확인"""
        return {
            'timeseries': '1_timeseries' in self.results_cache and bool(self.results_cache['1_timeseries']),
            'statistics': '2_statistics' in self.results_cache and bool(self.results_cache['2_statistics']),
            'trade_analysis': '3_trade_analysis' in self.results_cache and bool(self.results_cache['3_trade_analysis']),
            'extreme_scenario': '4_extreme_scenario' in self.results_cache and bool(self.results_cache['4_extreme_scenario']),
            'position_sizing': '5_position_sizing' in self.results_cache and bool(self.results_cache['5_position_sizing']),
            'advanced_stats': '6_advanced_stats' in self.results_cache and bool(self.results_cache['6_advanced_stats']),
            'comprehensive': '7_comprehensive' in self.results_cache and bool(self.results_cache['7_comprehensive'])
        }
    
    def _extract_key_findings(self) -> Dict[str, Any]:
        """핵심 발견사항 추출"""
        findings = {}
        
        # 승률 (통계에서)
        if '2_statistics' in self.results_cache:
            stat_data = self.results_cache['2_statistics']
            if '2-1_win_rate' in stat_data:
                findings['win_rate'] = stat_data['2-1_win_rate'].get('observed_win_rate_pct', 0)
        
        # 수익성 (거래 분석에서)
        if '3_trade_analysis' in self.results_cache:
            trade_data = self.results_cache['3_trade_analysis']
            if '3-1_win_loss_comparison' in trade_data:
                comparison = trade_data['3-1_win_loss_comparison']
                findings['profit_factor'] = comparison.get('profit_factor', 0)
                findings['risk_reward_ratio'] = comparison.get('risk_reward_ratio', 0)
        
        # Sharpe Ratio (포지션 최적화에서)
        if '5_position_sizing' in self.results_cache:
            pos_data = self.results_cache['5_position_sizing']
            if '7-3_risk_adjusted' in pos_data:
                findings['sharpe_ratio'] = pos_data['7-3_risk_adjusted'].get('sharpe_ratio', 0)
        
        # 자본 생존성 (극한 상황에서)
        if '4_extreme_scenario' in self.results_cache:
            extreme_data = self.results_cache['4_extreme_scenario']
            if '4-4_capital_shortage' in extreme_data:
                shortage = extreme_data['4-4_capital_shortage']
                findings['capital_survival'] = shortage.get('survival_status', '불명')
                findings['margin_of_safety'] = shortage.get('margin_of_safety', 0)
        
        return findings
    
    def _assess_risks(self) -> Dict[str, Any]:
        """리스크 평가"""
        risks = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # 극한 상황 확인
        if '4_extreme_scenario' in self.results_cache:
            extreme = self.results_cache['4_extreme_scenario']
            if '4-4_capital_shortage' in extreme:
                if not extreme['4-4_capital_shortage'].get('survived', False):
                    risks['critical'].append("자본 부족: 50달러 초기자본으로 생존 불가능")
        
        # 통계 유의성 확인
        if '2_statistics' in self.results_cache:
            stat = self.results_cache['2_statistics']
            if '2-1_win_rate' in stat:
                if stat['2-1_win_rate'].get('p_value', 1) >= 0.05:
                    risks['high'].append("통계 신뢰도: 승률이 통계적으로 유의미하지 않음")
        
        return risks
    
    def _get_recommendation(self) -> str:
        """최종 권장사항"""
        findings = self._extract_key_findings()
        risks = self._assess_risks()
        
        if risks['critical']:
            return "❌ 현재 상태로 실전 투입 불가능. 전략 재검토 필요."
        elif risks['high']:
            return "⚠️ 높은 위험. 소액 테스트 후 진행 권장."
        elif findings.get('profit_factor', 0) > 2.0 and findings.get('win_rate', 0) > 55:
            return "✅ 실전 투입 강력 추천."
        else:
            return "🔄 추가 최적화 후 재평가 필요."
    
    # ========== Streamlit 통합용 함수 ==========
    def get_streamlit_data(self) -> Dict[str, Any]:
        """
        Streamlit에서 사용할 데이터 형식
        
        Returns:
        --------
        dict
            Streamlit 호환 데이터
        """
        summary = self.generate_summary_report()
        
        return {
            'summary': summary,
            'metrics': {
                'win_rate': summary['key_findings'].get('win_rate', 0),
                'profit_factor': summary['key_findings'].get('profit_factor', 0),
                'sharpe_ratio': summary['key_findings'].get('sharpe_ratio', 0),
                'capital_survival': summary['key_findings'].get('capital_survival', '불명'),
                'margin_of_safety': summary['key_findings'].get('margin_of_safety', 0)
            },
            'risks': summary['risk_assessment'],
            'recommendation': summary['recommendation'],
            'status': summary['analysis_status']
        }


# 테스트 코드
if __name__ == "__main__":
    print("AnalysisBridge 모듈 테스트")
    print("이 모듈은 app.py에서 사용됩니다.\n")
