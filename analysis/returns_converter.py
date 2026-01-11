"""
ReturnsConverter - TradingView CSV 파싱 (한글/영문 자동 인식)
한글 헤더를 자동으로 영문으로 변환하여 처리
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ReturnsConverter:
    """TradingView 백테스트 CSV → 거래 데이터 변환"""
    
    def __init__(self, csv_data):
        """
        Args:
            csv_data: pandas DataFrame 또는 파일 경로
        """
        if isinstance(csv_data, str):
            # 파일 경로인 경우
            self.df = self._load_csv(csv_data)
        elif isinstance(csv_data, pd.DataFrame):
            # DataFrame인 경우
            self.df = csv_data.copy()
        else:
            raise ValueError("csv_data는 파일 경로 또는 DataFrame이어야 합니다.")
        
        # 거래 데이터 파싱
        self.trades = self._parse_trades_korean()
    
    def _load_csv(self, file_path):
        """CSV 파일 로드 (한글 인코딩 자동 감지)"""
        try:
            # UTF-8 with BOM 시도
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            return df
        except:
            try:
                # UTF-8 시도
                df = pd.read_csv(file_path, encoding='utf-8')
                return df
            except:
                # EUC-KR 시도
                df = pd.read_csv(file_path, encoding='euc-kr')
                return df
    
    def parse_trades(self):
        """거래 파싱 (공개 메서드)"""
        return self._parse_trades_korean()
    
    def _parse_trades_korean(self):
        """한글 TradingView CSV 파싱 (정확한 컬럼명 기반)"""
        trades = []
        
        df = self.df.copy()
        
        # ========== 날짜 컬럼 자동 감지 (추가!) ==========
        date_col = None
        for col in df.columns:
            if '날짜' in col and ('시간' in col or '및' in col):
                date_col = col
                break
        
        if date_col is None:
            raise ValueError("날짜 컬럼을 찾을 수 없습니다. '날짜/시간' 또는 '날짜 및 시간' 컬럼이 필요합니다.")
        # ========== 추가 끝 ==========
        
        # 거래 번호로 그룹핑
        for trade_num, group in df.groupby('거래 #'):
            # 시간순 정렬 (Entry가 먼저 오도록)
            group = group.sort_values(date_col)  # ← 여기 수정
            
            # Entry 행 찾기 (진입)
            entry_rows = group[group['타입'].str.contains('진입', na=False)]
            exit_rows = group[group['타입'].str.contains('청산', na=False)]
            
            if len(entry_rows) == 0 or len(exit_rows) == 0:
                continue
            
            # Entry는 가장 처음 것 (보통 1개)
            entry = entry_rows.iloc[0]
            
            # Direction 판정
            direction = 'LONG' if '매수' in entry['타입'] else 'SHORT'
            
            # Entry 정보
            entry_datetime = pd.to_datetime(entry[date_col], format='%Y-%m-%d %H:%M')  # ← 수정
            entry_date = entry_datetime.date()
            entry_price = float(entry['가격 USDT'])
            
            # 각 Exit에 대해 거래 기록
            for _, exit_row in exit_rows.iterrows():
                try:
                    exit_datetime = pd.to_datetime(exit_row[date_col], format='%Y-%m-%d %H:%M')  # ← 수정
                    exit_date = exit_datetime.date()
                    exit_price = float(exit_row['가격 USDT'])
                    
                    # 수익률
                    return_pct = float(exit_row['순손익 %'])
                    
                    # NaN 체크
                    if pd.isna(return_pct):
                        continue
                    
                    # 보유 일수
                    holding_days = (exit_datetime - entry_datetime).days
                    if holding_days < 0:
                        holding_days = 0
                    
                    # ========== 런업/드로다운 컬럼명 자동 감지 (추가!) ==========
                    runup_col = None
                    drawdown_col = None
                    
                    for col in exit_row.index:
                        if '런업' in col or '순행' in col:
                            if '%' in col:
                                runup_col = col
                        if '드로다운' in col or '역행' in col:
                            if '%' in col:
                                drawdown_col = col
                    
                    runup_pct = float(exit_row[runup_col]) if runup_col and not pd.isna(exit_row[runup_col]) else 0.0
                    drawdown_pct = float(exit_row[drawdown_col]) if drawdown_col and not pd.isna(exit_row[drawdown_col]) else 0.0
                    # ========== 추가 끝 ==========
                    
                    # 누적 손익
                    cumulative_pct = float(exit_row['누적 손익 %']) if '누적 손익 %' in exit_row.index else return_pct
                    
                    trade = {
                        'trade_num': int(trade_num),
                        'direction': direction,
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'entry_time': entry_datetime,
                        'exit_time': exit_datetime,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'return_pct': return_pct,
                        'cumulative_return_pct': cumulative_pct,
                        'runup_pct': runup_pct,
                        'drawdown_pct': drawdown_pct,
                        'holding_days': holding_days,
                        'signal': str(exit_row.get('신호', '')),
                    }
                    
                    trades.append(trade)
                    
                except Exception as e:
                    continue
        
        if len(trades) == 0:
            # 빈 DataFrame 반환
            trades_df = pd.DataFrame(columns=[
                'trade_num', 'direction', 'entry_date', 'exit_date',
                'entry_time', 'exit_time', 'entry_price', 'exit_price',
                'return_pct', 'cumulative_return_pct', 'runup_pct', 
                'drawdown_pct', 'holding_days', 'signal'
            ])
        else:
            trades_df = pd.DataFrame(trades)
            # Exit 날짜 기준 정렬
            trades_df = trades_df.sort_values('exit_date').reset_index(drop=True)
        
        return trades_df
    
    def to_daily_returns(self):
        """일일 수익률 계산 (Quantstats용)"""
        if len(self.trades) == 0:
            return pd.Series(dtype=float)
        
        # 날짜별 손익 합계
        daily_returns = self.trades.groupby('exit_date')['return_pct'].sum() / 100.0
        
        # 날짜 범위 생성
        date_range = pd.date_range(
            start=self.trades['entry_date'].min(),
            end=self.trades['exit_date'].max(),
            freq='D'
        )
        
        # 누락된 날짜는 0으로 채우기
        daily_returns = daily_returns.reindex(pd.DatetimeIndex(date_range), fill_value=0.0)
        
        return daily_returns
    
    def to_trade_returns(self):
        """거래별 수익률 (시간 순서)"""
        if len(self.trades) == 0:
            return pd.Series(dtype=float)
        
        # Exit 날짜 기준 정렬
        sorted_trades = self.trades.sort_values('exit_date').reset_index(drop=True)
        
        # 거래별 수익률 Series
        trade_returns = pd.Series(
            sorted_trades['return_pct'].values / 100.0,
            index=sorted_trades['exit_date']
        )
        
        return trade_returns
    
    def get_statistics(self):
        """기본 통계"""
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_return': 0,
                'avg_return': 0,
                'max_drawdown': 0,
                'period_days': 0,
                'start_date': None,
                'end_date': None,
            }
        
        trades = self.trades
        
        total_trades = len(trades)
        winning_trades = len(trades[trades['return_pct'] > 0])
        losing_trades = len(trades[trades['return_pct'] < 0])
        
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        wins = trades[trades['return_pct'] > 0]['return_pct']
        losses = trades[trades['return_pct'] < 0]['return_pct']
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        # 누적 손익 사용
        if 'cumulative_return_pct' in trades.columns:
            total_return = trades['cumulative_return_pct'].iloc[-1]
        else:
            total_return = trades['return_pct'].sum()
        
        avg_return = trades['return_pct'].mean()
        
        # 최대 낙폭
        max_drawdown = trades['drawdown_pct'].min() if len(trades) > 0 else 0
        
        # 기간 (Timestamp와 date 타입 통일)
        if len(trades) > 0:
            exit_max = pd.Timestamp(trades['exit_date'].max())
            entry_min = pd.Timestamp(trades['entry_date'].min())
            period_days = (exit_max - entry_min).days
            start_date = entry_min.date() if hasattr(entry_min, 'date') else entry_min
            end_date = exit_max.date() if hasattr(exit_max, 'date') else exit_max
        else:
            period_days = 0
            start_date = None
            end_date = None
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_return': total_return,
            'avg_return': avg_return,
            'max_drawdown': max_drawdown,
            'period_days': period_days,
            'start_date': start_date,
            'end_date': end_date,
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        converter = ReturnsConverter(csv_file)
        
        print("✅ CSV 파싱 완료!")
        print(f"📊 거래 수: {len(converter.trades)}건")
        
        if len(converter.trades) > 0:
            stats = converter.get_statistics()
            print(f"📈 승률: {stats['win_rate']:.2f}%")
            print(f"💰 총 수익률: {stats['total_return']:.2f}%")
            print(f"📅 기간: {stats['period_days']}일")