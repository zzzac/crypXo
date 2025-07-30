import talib
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from pathlib import Path
from lightgbm import LGBMRegressor, LGBMClassifier
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

def get_df_from_local_path(data_dir):
    parquet_files = sorted(Path(data_dir).glob('*.parquet'))

    df_list = []
    for file in parquet_files:
        df_day = pd.read_parquet(file)
        df_list.append(df_day)

    df = pd.concat(df_list).reset_index(drop=True)

    df = df.sort_values('timestamp').reset_index(drop=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    df['tradingDay'] = df['timestamp'].dt.date.astype(str)
    df['mod'] = df['timestamp'].dt.hour * 60 + df['timestamp'].dt.minute
    return df


class TechnicalIndicators:
    """
    完整的TA-Lib技术指标计算器
    适用于加密货币K线数据的cross section分析
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化技术指标计算器
        
        Parameters:
        data: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        """
        self.data = data.copy()
        self.validate_data()
        
    def validate_data(self):
        """验证数据格式"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # 确保数据类型正确
        for col in required_cols:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
    
    def calculate_all_indicators(self) -> pd.DataFrame:
        """
        计算所有技术指标
        """
        result = self.data.copy()
        
        # 1. 重叠研究 (Overlap Studies)
        overlap_indicators = self.calculate_overlap_studies()
        result = pd.concat([result, overlap_indicators], axis=1)
        
        # 2. 动量指标 (Momentum Indicators)
        momentum_indicators = self.calculate_momentum_indicators()
        result = pd.concat([result, momentum_indicators], axis=1)
        
        # 3. 成交量指标 (Volume Indicators)
        volume_indicators = self.calculate_volume_indicators()
        result = pd.concat([result, volume_indicators], axis=1)
        
        # 4. 波动率指标 (Volatility Indicators)
        volatility_indicators = self.calculate_volatility_indicators()
        result = pd.concat([result, volatility_indicators], axis=1)
        
        # 5. 价格变换 (Price Transform)
        price_transform = self.calculate_price_transform()
        result = pd.concat([result, price_transform], axis=1)
        
        # 6. 周期指标 (Cycle Indicators)
        cycle_indicators = self.calculate_cycle_indicators()
        result = pd.concat([result, cycle_indicators], axis=1)
        
        # 7. 模式识别 (Pattern Recognition)
        pattern_indicators = self.calculate_pattern_recognition()
        result = pd.concat([result, pattern_indicators], axis=1)
        
        # 8. 数学变换 (Math Transform)
        math_transform = self.calculate_math_transform()
        result = pd.concat([result, math_transform], axis=1)
        
        # 9. 统计函数 (Statistic Functions)
        statistic_functions = self.calculate_statistic_functions()
        result = pd.concat([result, statistic_functions], axis=1)
        
        return result
    
    def calculate_overlap_studies(self) -> pd.DataFrame:
        """
        重叠研究指标 - 通常与价格图表重叠显示
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 移动平均线
        for period in [5, 10, 20, 30, 50, 100, 200]:
            indicators[f'SMA_{period}'] = talib.SMA(self.data['close'], timeperiod=period)
            indicators[f'EMA_{period}'] = talib.EMA(self.data['close'], timeperiod=period)
            indicators[f'WMA_{period}'] = talib.WMA(self.data['close'], timeperiod=period)
        
        # 双指数移动平均
        indicators['DEMA_30'] = talib.DEMA(self.data['close'], timeperiod=30)
        indicators['TEMA_30'] = talib.TEMA(self.data['close'], timeperiod=30)
        
        # 三角移动平均
        indicators['TRIMA_30'] = talib.TRIMA(self.data['close'], timeperiod=30)
        
        # 卡夫曼自适应移动平均
        indicators['KAMA_30'] = talib.KAMA(self.data['close'], timeperiod=30)
        
        # MESA自适应移动平均
        indicators['MAMA'], indicators['FAMA'] = talib.MAMA(self.data['close'])
        
        # 中点价格
        indicators['MIDPOINT'] = talib.MIDPOINT(self.data['close'], timeperiod=14)
        indicators['MIDPRICE'] = talib.MIDPRICE(self.data['high'], self.data['low'], timeperiod=14)
        
        # 抛物线SAR
        indicators['SAR'] = talib.SAR(self.data['high'], self.data['low'])
        
        # 时间序列预测
        indicators['TSF'] = talib.TSF(self.data['close'], timeperiod=14)
        
        # 布林带
        indicators['BB_UPPER'], indicators['BB_MIDDLE'], indicators['BB_LOWER'] = talib.BBANDS(
            self.data['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        
        # 希尔伯特变换
        indicators['HT_TRENDLINE'] = talib.HT_TRENDLINE(self.data['close'])
        
        return indicators
    
    def calculate_momentum_indicators(self) -> pd.DataFrame:
        """
        动量指标 - 衡量价格变化的速度和强度
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # ADX - 平均方向指数
        indicators['ADX'] = talib.ADX(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        indicators['ADXR'] = talib.ADXR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        # APO - 绝对价格振荡器
        indicators['APO'] = talib.APO(self.data['close'], fastperiod=12, slowperiod=26)
        
        # Aroon - 阿隆指标
        indicators['AROON_UP'], indicators['AROON_DOWN'] = talib.AROON(
            self.data['high'], self.data['low'], timeperiod=14
        )
        indicators['AROONOSC'] = talib.AROONOSC(self.data['high'], self.data['low'], timeperiod=14)
        
        # BOP - 均势指标
        indicators['BOP'] = talib.BOP(self.data['open'], self.data['high'], self.data['low'], self.data['close'])
        
        # CCI - 顺势指标
        indicators['CCI'] = talib.CCI(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        # CMO - 钱德动量摆动指标
        indicators['CMO'] = talib.CMO(self.data['close'], timeperiod=14)
        
        # DX - 方向指数
        indicators['DX'] = talib.DX(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        # MACD - 移动平均收敛发散
        indicators['MACD'], indicators['MACD_SIGNAL'], indicators['MACD_HIST'] = talib.MACD(
            self.data['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # MFI - 资金流量指标
        indicators['MFI'] = talib.MFI(self.data['high'], self.data['low'], self.data['close'], self.data['volume'], timeperiod=14)
        
        # MINUS_DI, MINUS_DM - 负方向指标
        indicators['MINUS_DI'] = talib.MINUS_DI(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        indicators['MINUS_DM'] = talib.MINUS_DM(self.data['high'], self.data['low'], timeperiod=14)
        
        # MOM - 动量
        indicators['MOM'] = talib.MOM(self.data['close'], timeperiod=10)
        
        # PLUS_DI, PLUS_DM - 正方向指标
        indicators['PLUS_DI'] = talib.PLUS_DI(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        indicators['PLUS_DM'] = talib.PLUS_DM(self.data['high'], self.data['low'], timeperiod=14)
        
        # PPO - 价格振荡器
        indicators['PPO'] = talib.PPO(self.data['close'], fastperiod=12, slowperiod=26)
        
        # ROC - 变化率
        indicators['ROC'] = talib.ROC(self.data['close'], timeperiod=10)
        indicators['ROCP'] = talib.ROCP(self.data['close'], timeperiod=10)
        indicators['ROCR'] = talib.ROCR(self.data['close'], timeperiod=10)
        indicators['ROCR100'] = talib.ROCR100(self.data['close'], timeperiod=10)
        
        # RSI - 相对强弱指标
        indicators['RSI'] = talib.RSI(self.data['close'], timeperiod=14)
        
        # 随机指标
        indicators['STOCH_K'], indicators['STOCH_D'] = talib.STOCH(
            self.data['high'], self.data['low'], self.data['close']
        )
        indicators['STOCHF_K'], indicators['STOCHF_D'] = talib.STOCHF(
            self.data['high'], self.data['low'], self.data['close']
        )
        indicators['STOCHRSI_K'], indicators['STOCHRSI_D'] = talib.STOCHRSI(
            self.data['close'], timeperiod=14, fastk_period=5, fastd_period=3
        )
        
        # TRIX - 三重指数平滑振荡器
        indicators['TRIX'] = talib.TRIX(self.data['close'], timeperiod=30)
        
        # 终极振荡器
        indicators['ULTOSC'] = talib.ULTOSC(self.data['high'], self.data['low'], self.data['close'])
        
        # 威廉指标
        indicators['WILLR'] = talib.WILLR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        return indicators
    
    def calculate_volume_indicators(self) -> pd.DataFrame:
        """
        成交量指标
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # AD - 累积/分布线
        indicators['AD'] = talib.AD(self.data['high'], self.data['low'], self.data['close'], self.data['volume'])
        
        # ADOSC - 累积/分布振荡器
        indicators['ADOSC'] = talib.ADOSC(
            self.data['high'], self.data['low'], self.data['close'], self.data['volume']
        )
        
        # OBV - 能量潮
        indicators['OBV'] = talib.OBV(self.data['close'], self.data['volume'])
        
        return indicators
    
    def calculate_volatility_indicators(self) -> pd.DataFrame:
        """
        波动率指标
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # ATR - 平均真实波幅
        indicators['ATR'] = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        # NATR - 标准化平均真实波幅
        indicators['NATR'] = talib.NATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        
        # TRANGE - 真实波幅
        indicators['TRANGE'] = talib.TRANGE(self.data['high'], self.data['low'], self.data['close'])
        
        return indicators
    
    def calculate_price_transform(self) -> pd.DataFrame:
        """
        价格变换
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 平均价格
        indicators['AVGPRICE'] = talib.AVGPRICE(self.data['open'], self.data['high'], self.data['low'], self.data['close'])
        
        # 中位价格
        indicators['MEDPRICE'] = talib.MEDPRICE(self.data['high'], self.data['low'])
        
        # 典型价格
        indicators['TYPPRICE'] = talib.TYPPRICE(self.data['high'], self.data['low'], self.data['close'])
        
        # 加权收盘价
        indicators['WCLPRICE'] = talib.WCLPRICE(self.data['high'], self.data['low'], self.data['close'])
        
        return indicators
    
    def calculate_cycle_indicators(self) -> pd.DataFrame:
        """
        周期指标
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 希尔伯特变换
        indicators['HT_DCPERIOD'] = talib.HT_DCPERIOD(self.data['close'])
        indicators['HT_DCPHASE'] = talib.HT_DCPHASE(self.data['close'])
        
        # 相位指标
        indicators['HT_PHASOR_INPHASE'], indicators['HT_PHASOR_QUAD'] = talib.HT_PHASOR(self.data['close'])
        
        # 正弦波
        indicators['HT_SINE'], indicators['HT_LEADSINE'] = talib.HT_SINE(self.data['close'])
        
        # 趋势模式
        indicators['HT_TRENDMODE'] = talib.HT_TRENDMODE(self.data['close'])
        
        return indicators
    
    def calculate_pattern_recognition(self) -> pd.DataFrame:
        """
        模式识别指标 - K线形态
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 所有K线形态
        pattern_functions = [
            'CDL2CROWS', 'CDL3BLACKCROWS', 'CDL3INSIDE', 'CDL3LINESTRIKE',
            'CDL3OUTSIDE', 'CDL3STARSINSOUTH', 'CDL3WHITESOLDIERS', 'CDLABANDONEDBABY',
            'CDLADVANCEBLOCK', 'CDLBELTHOLD', 'CDLBREAKAWAY', 'CDLCLOSINGMARUBOZU',
            'CDLCONCEALBABYSWALL', 'CDLCOUNTERATTACK', 'CDLDARKCLOUDCOVER', 'CDLDOJI',
            'CDLDOJISTAR', 'CDLDRAGONFLYDOJI', 'CDLENGULFING', 'CDLEVENINGDOJISTAR',
            'CDLEVENINGSTAR', 'CDLGAPSIDESIDEWHITE', 'CDLGRAVESTONEDOJI', 'CDLHAMMER',
            'CDLHANGINGMAN', 'CDLHARAMI', 'CDLHARAMICROSS', 'CDLHIGHWAVE',
            'CDLHIKKAKE', 'CDLHIKKAKEMOD', 'CDLHOMINGPIGEON', 'CDLIDENTICAL3CROWS',
            'CDLINNECK', 'CDLINVERTEDHAMMER', 'CDLKICKING', 'CDLKICKINGBYLENGTH',
            'CDLLADDERBOTTOM', 'CDLLONGLEGGEDDOJI', 'CDLLONGLINE', 'CDLMARUBOZU',
            'CDLMATCHINGLOW', 'CDLMATHOLD', 'CDLMORNINGDOJISTAR', 'CDLMORNINGSTAR',
            'CDLONNECK', 'CDLPIERCING', 'CDLRICKSHAWMAN', 'CDLRISEFALL3METHODS',
            'CDLSEPARATINGLINES', 'CDLSHOOTINGSTAR', 'CDLSHORTLINE', 'CDLSPINNINGTOP',
            'CDLSTALLEDPATTERN', 'CDLSTICKSANDWICH', 'CDLTAKURI', 'CDLTASUKIGAP',
            'CDLTHRUSTING', 'CDLTRISTAR', 'CDLUNIQUE3RIVER', 'CDLUPSIDEGAP2CROWS',
            'CDLXSIDEGAP3METHODS'
        ]
        
        for pattern in pattern_functions:
            try:
                func = getattr(talib, pattern)
                indicators[pattern] = func(self.data['open'], self.data['high'], 
                                         self.data['low'], self.data['close'])
            except:
                pass  # 某些函数可能不存在
        
        return indicators
    
    def calculate_math_transform(self) -> pd.DataFrame:
        """
        数学变换
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 各种数学变换
        indicators['ACOS'] = talib.ACOS(self.data['close'] / self.data['close'].max())
        indicators['ASIN'] = talib.ASIN(self.data['close'] / self.data['close'].max())
        indicators['ATAN'] = talib.ATAN(self.data['close'])
        indicators['CEIL'] = talib.CEIL(self.data['close'])
        indicators['COS'] = talib.COS(self.data['close'])
        indicators['COSH'] = talib.COSH(self.data['close'] / self.data['close'].max())
        indicators['EXP'] = talib.EXP(self.data['close'] / self.data['close'].max())
        indicators['FLOOR'] = talib.FLOOR(self.data['close'])
        indicators['LN'] = talib.LN(self.data['close'])
        indicators['LOG10'] = talib.LOG10(self.data['close'])
        indicators['SIN'] = talib.SIN(self.data['close'])
        indicators['SINH'] = talib.SINH(self.data['close'] / self.data['close'].max())
        indicators['SQRT'] = talib.SQRT(self.data['close'])
        indicators['TAN'] = talib.TAN(self.data['close'] / self.data['close'].max())
        indicators['TANH'] = talib.TANH(self.data['close'] / self.data['close'].max())
        
        return indicators
    
    def calculate_statistic_functions(self) -> pd.DataFrame:
        """
        统计函数
        """
        indicators = pd.DataFrame(index=self.data.index)
        
        # 贝塔系数 (需要两个序列)
        market_close = self.data['close']  # 假设这是市场数据
        # indicators['BETA'] = talib.BETA(self.data['close'], market_close, timeperiod=5)
        
        # 相关系数
        indicators['CORREL'] = talib.CORREL(self.data['high'], self.data['low'], timeperiod=30)
        
        # 线性回归
        indicators['LINEARREG'] = talib.LINEARREG(self.data['close'], timeperiod=14)
        indicators['LINEARREG_ANGLE'] = talib.LINEARREG_ANGLE(self.data['close'], timeperiod=14)
        indicators['LINEARREG_INTERCEPT'] = talib.LINEARREG_INTERCEPT(self.data['close'], timeperiod=14)
        indicators['LINEARREG_SLOPE'] = talib.LINEARREG_SLOPE(self.data['close'], timeperiod=14)
        
        # 标准偏差
        indicators['STDDEV'] = talib.STDDEV(self.data['close'], timeperiod=5)
        
        # 方差
        indicators['VAR'] = talib.VAR(self.data['close'], timeperiod=5)
        
        return indicators
    
    def get_cross_section_features(self, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        为cross section分析准备特征
        """
        all_indicators = self.calculate_all_indicators()
        
        # 计算相对强度特征
        if timestamp_col in all_indicators.columns:
            # 计算横截面排名
            numeric_cols = all_indicators.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    all_indicators[f'{col}_rank'] = all_indicators.groupby(timestamp_col)[col].rank(pct=True)
                    all_indicators[f'{col}_zscore'] = all_indicators.groupby(timestamp_col)[col].apply(
                        lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
                    )
        
        return all_indicators
    
    def get_feature_summary(self) -> Dict:
        """
        获取特征摘要
        """
        all_indicators = self.calculate_all_indicators()
        
        summary = {
            'total_features': len(all_indicators.columns),
            'feature_categories': {
                'overlap_studies': len([col for col in all_indicators.columns if any(x in col for x in ['SMA', 'EMA', 'BB', 'SAR'])]),
                'momentum_indicators': len([col for col in all_indicators.columns if any(x in col for x in ['RSI', 'MACD', 'STOCH', 'ADX'])]),
                'volume_indicators': len([col for col in all_indicators.columns if any(x in col for x in ['AD', 'OBV'])]),
                'volatility_indicators': len([col for col in all_indicators.columns if any(x in col for x in ['ATR', 'TRANGE'])]),
                'pattern_recognition': len([col for col in all_indicators.columns if col.startswith('CDL')]),
                'math_transform': len([col for col in all_indicators.columns if any(x in col for x in ['ACOS', 'ASIN', 'ATAN', 'COS', 'SIN'])]),
                'statistic_functions': len([col for col in all_indicators.columns if any(x in col for x in ['CORREL', 'LINEARREG', 'STDDEV'])])
            }
        }
        
        return summary
