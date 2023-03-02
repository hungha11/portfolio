import datetime
import numpy as np
import pandas as pd
import numpy as np


def calc_returns(srs: pd.Series, day_offset: int = 1):
    returns = srs / srs.shift(day_offset) - 1.0
    return returns

class trend_estimation:
    def old_school_estimate(srs,TS_LENGTH):
        return calc_returns(srs, TS_LENGTH)
    
    def macd_estimate(srs,short_timescale,long_timescale):
        def _calc_halflife(timescale):
            return np.log(0.5) / np.log(1 - 1 / timescale)

        macd = (
            srs.ewm(halflife=_calc_halflife(short_timescale)).mean()
            - srs.ewm(halflife=_calc_halflife(long_timescale)).mean()
        )
        q = macd / srs.rolling(63).std().fillna(method="bfill")
        return q / q.rolling(252).std().fillna(method="bfill")

class trading_signal:
    def sign_func(trend):
        return np.sign(trend)
    
    def phi_func(trend):
        return trend * np.exp(-(trend ** 2) / 4) / 0.89
    
class TSMOM:
    def __init__(self,srs,signal ,VOL_LOOKBACK=60, VOL_TARGET=0.35, long_only=True, volatility_scaling=True,T_3=False,transaction_fee=0.001):
        self.srs = srs
        self.VOL_LOOKBACK= VOL_LOOKBACK
        self.VOL_TARGET =VOL_TARGET
        self.long_only=long_only
        self.volatility_scaling = volatility_scaling
        self.signal = signal
        self.T_3 =T_3
        self.transaction_fee = transaction_fee
        self.anualize_factor=252
        self.daily_returns = calc_returns(self.srs)
        if self.T_3:
            self.anualize_factor = self.anualize_factor/3
            self.VOL_LOOKBACK=self.VOL_LOOKBACK/3
        if self.long_only ==True:
            self.signal = np.maximum(0,self.signal)
        
    
    ## for volatility targeting
    def calc_daily_vol(self,daily_returns):
        return (
            daily_returns.ewm(span=self.VOL_LOOKBACK, min_periods=self.VOL_LOOKBACK)
            .std()
            .fillna(method="bfill")
        )

    def volatility_target_map(self):
        daily_vol = self.calc_daily_vol(self.daily_returns)
        annualised_vol = daily_vol * np.sqrt(self.anualize_factor)  # annualised
        position_map = self.VOL_TARGET / annualised_vol.shift(1)
        position_map[position_map > 2.0] = 2.0
        return position_map
    
    def calc_vol_scaled_returns(self):
        position_map = self.volatility_target_map()
        return self.daily_returns * position_map
    
    def transaction_cost(self):
        position_map = self.volatility_target_map()
        total_position = position_map*self.signal
        transaction_cost = np.abs(total_position-total_position.shift(1))*self.transaction_fee
        return transaction_cost
        
    ## strategy run here
    def run(self):
        next_day_returns = (
            self.calc_vol_scaled_returns().shift(-1)
            if self.volatility_scaling
            else self.daily_returns.shift(-1)
            )
        transaction_cost = self.transaction_cost()
        cap_returns = self.signal * next_day_returns - transaction_cost
        cap_returns.rename('tsmom',inplace=True)
        return cap_returns