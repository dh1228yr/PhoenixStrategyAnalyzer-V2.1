"""
Quantstats 통합 래퍼
HTML 리포트 생성 및 주요 지표 추출
"""
import pandas as pd
import numpy as np

class QuantstatsAnalyzer:
    """Quantstats 분석 래퍼"""
    
    def __init__(self, returns):
        """
        Parameters:
        -----------
        returns : pd.Series
            일별 수익률 (decimal)
        """
        self.returns = returns
        self.metrics = {}
        self.last_error = None  # ← 추가: 마지막 에러 저장
        
    def generate_html_report(self, output_path='output/reports/quantstats_report.html'):
        """
        HTML 리포트 생성
        
        Parameters:
        -----------
        output_path : str
            저장 경로
            
        Returns:
        --------
        str : 저장된 파일 경로
        """
        try:
            import quantstats as qs
            
            # 리포트 생성
            qs.reports.html(
                self.returns,
                output=output_path,
                title='Phoenix KAMA Strategy Analysis'
            )
            
            print(f"✅ Quantstats 리포트 생성: {output_path}")
            return output_path
            
        except ImportError as e:
            self.last_error = f"ImportError: {e}"
            print(f"❌ Quantstats 미설치: pip install quantstats --break-system-packages")
            return None
        except Exception as e:
            self.last_error = str(e)
            print(f"❌ 리포트 생성 실패: {e}")
            return None
    
    def get_metrics(self):
        """
        주요 지표 추출
        
        Returns:
        --------
        dict : 주요 지표 딕셔너리 (에러 시 {'error': '에러메시지'})
        """
        try:
            import quantstats as qs
            
            # 데이터 검증
            if len(self.returns) == 0:
                self.last_error = "수익률 데이터가 비어있습니다"
                return {'error': self.last_error}
            
            if not isinstance(self.returns, pd.Series):
                self.last_error = f"returns 타입 오류: {type(self.returns)} (pd.Series 필요)"
                return {'error': self.last_error}
            
            # 지표 추출 (각각 try-except로 보호)
            self.metrics = {}
            
            try:
                self.metrics['cagr'] = qs.stats.cagr(self.returns)
            except Exception as e:
                self.metrics['cagr'] = None
                print(f"CAGR 계산 실패: {e}")
            
            try:
                self.metrics['sharpe'] = qs.stats.sharpe(self.returns)
            except Exception as e:
                self.metrics['sharpe'] = None
                print(f"Sharpe 계산 실패: {e}")
            
            try:
                self.metrics['sortino'] = qs.stats.sortino(self.returns)
            except Exception as e:
                self.metrics['sortino'] = None
                print(f"Sortino 계산 실패: {e}")
            
            try:
                self.metrics['calmar'] = qs.stats.calmar(self.returns)
            except Exception as e:
                self.metrics['calmar'] = None
                print(f"Calmar 계산 실패: {e}")
            
            try:
                self.metrics['max_drawdown'] = qs.stats.max_drawdown(self.returns)
            except Exception as e:
                self.metrics['max_drawdown'] = None
                print(f"Max Drawdown 계산 실패: {e}")
            
            try:
                self.metrics['volatility'] = qs.stats.volatility(self.returns)
            except Exception as e:
                self.metrics['volatility'] = None
                print(f"Volatility 계산 실패: {e}")
            
            try:
                self.metrics['var'] = qs.stats.var(self.returns)
            except Exception as e:
                self.metrics['var'] = None
                print(f"VaR 계산 실패: {e}")
            
            try:
                self.metrics['cvar'] = qs.stats.cvar(self.returns)
            except Exception as e:
                self.metrics['cvar'] = None
                print(f"CVaR 계산 실패: {e}")
            
            try:
                self.metrics['risk_of_ruin'] = qs.stats.risk_of_ruin(self.returns)
            except Exception as e:
                self.metrics['risk_of_ruin'] = None
                print(f"Risk of Ruin 계산 실패: {e}")
            
            try:
                self.metrics['ulcer_index'] = qs.stats.ulcer_index(self.returns)
            except Exception as e:
                self.metrics['ulcer_index'] = None
                print(f"Ulcer Index 계산 실패: {e}")
            
            try:
                self.metrics['serenity_index'] = qs.stats.serenity_index(self.returns)
            except Exception as e:
                self.metrics['serenity_index'] = None
                print(f"Serenity Index 계산 실패: {e}")
            
            try:
                self.metrics['gain_pain_ratio'] = qs.stats.gain_to_pain_ratio(self.returns)
            except Exception as e:
                self.metrics['gain_pain_ratio'] = None
                print(f"Gain/Pain Ratio 계산 실패: {e}")
            
            try:
                self.metrics['recovery_factor'] = qs.stats.recovery_factor(self.returns)
            except Exception as e:
                self.metrics['recovery_factor'] = None
                print(f"Recovery Factor 계산 실패: {e}")
            
            # 모든 지표가 None이면 에러
            if all(v is None for v in self.metrics.values()):
                self.last_error = "모든 지표 계산 실패"
                return {'error': self.last_error}
            
            return self.metrics
            
        except ImportError as e:
            self.last_error = f"Quantstats 미설치: {e}"
            print(f"❌ {self.last_error}")
            return {'error': self.last_error}
        except Exception as e:
            self.last_error = f"지표 추출 실패: {e}"
            print(f"❌ {self.last_error}")
            import traceback
            print(traceback.format_exc())
            return {'error': self.last_error}
    
    def get_drawdown_table(self, top=5):
        """
        Top Drawdown 목록
        
        Parameters:
        -----------
        top : int
            상위 N개
            
        Returns:
        --------
        pd.DataFrame : Drawdown 테이블
        """
        try:
            import quantstats as qs
            
            drawdowns = qs.stats.drawdown_details(self.returns)
            return drawdowns.head(top)
            
        except Exception as e:
            self.last_error = str(e)
            print(f"❌ Drawdown 테이블 생성 실패: {e}")
            return pd.DataFrame()
    
    def get_monthly_returns(self):
        """
        월별 수익률 테이블
        
        Returns:
        --------
        pd.DataFrame : 월별 수익률
        """
        try:
            import quantstats as qs
            
            monthly = qs.stats.monthly_returns(self.returns)
            return monthly
            
        except Exception as e:
            self.last_error = str(e)
            print(f"❌ 월별 수익률 생성 실패: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    print("✅ QuantstatsAnalyzer 모듈 로드 완료")