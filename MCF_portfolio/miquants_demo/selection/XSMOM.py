import pandas as pd
import numpy as np
from datetime import timedelta
from miquants_demo.data_collection.PriceLoader import load_stock_data


def XSMOM_winner(prices,num,lookback=6,offset=2):
    xsmom = prices.shift(offset)/prices.shift(offset+lookback)
    xsmom.dropna(inplace=True)
    xsmom = xsmom.T
    xsmom_dict={}
    for month in xsmom.columns:
        secret_df = xsmom[month]
        secret_df = secret_df.sort_values(ascending=False)
        xsmom_dict[month.strftime('%Y-%m-%d')] = secret_df.index[:num].to_list()
    return xsmom_dict
def XSMOM_loser(prices,num,lookback=6,offset=2):
    xsmom = prices.shift(offset)/prices.shift(offset+lookback)
    xsmom.dropna(inplace=True)
    xsmom = xsmom.T
    
    xsmom_dict={}
    for month in xsmom.columns:
        secret_df = xsmom[month]
        secret_df = secret_df.sort_values(ascending=False)
        xsmom_dict[month.strftime('%Y-%m-%d')] = secret_df.index[-num:].to_list()
    return xsmom_dict

class XSMOM:
    def __init__(self,prices, xsmom_type = 'winner',duration='M', portfolio_num=5, offset = 2,lookback = 6,transaction_cost=0.001):
        self.xsmom_type= xsmom_type
        self.prices = prices
        self.portfolio_num =portfolio_num
        self.duration = duration
        self.lookback = lookback
        self.offset = offset
        self.transaction_cost=transaction_cost
        
    def get_portfolio(self):
        resample_data = self.prices.copy()
        resample_data.index = pd.to_datetime(resample_data.index)
        resample_data = resample_data.resample(self.duration).last()
        if self.xsmom_type =='winner':
            xsmom_dict = XSMOM_winner(resample_data,num=self.portfolio_num,lookback=self.lookback,offset=self.offset)
        if self.xsmom_type =='loser':
            xsmom_dict = XSMOM_loser(resample_data,num=self.portfolio_num,lookback=self.lookback,offset=self.offset)
        return xsmom_dict
    
    def run(self):
        xsmom_dict = self.get_portfolio()
        slice_month = list(xsmom_dict.keys())
        df_rets_equal=pd.DataFrame()
        xsmom_df = pd.DataFrame(columns=['xsmom'])

        for i in range(len(slice_month)):
            start_test = slice_month[i]
            if i < len(slice_month)-1:
                end_test = slice_month[i+1]
            if i == len(slice_month)-1:
                end_test = pd.to_datetime(start_test)+timedelta(days=30)
                end_test = end_test.strftime("%Y-%m-%d")
                    
            print(start_test,end_test)
            stock_hold = xsmom_dict[start_test]
            print(stock_hold,'\n')
            df_test=pd.DataFrame(columns=stock_hold)
            for name in stock_hold:
                secret = load_stock_data(name,start_test,end_test)
                if len(secret)>0:
                    df_test[name] = secret['close']
                    

            df_test = df_test.pct_change()
            df_test.iloc[0]=0
            df_test.iloc[-1]=df_test.iloc[-1]-(1/len(df_test.columns))*self.transaction_cost
            equal_weight = (1/len(df_test.columns))*df_test 
            equal_weight= np.sum(equal_weight,axis=1)
            df_rets_equal = pd.concat([df_rets_equal,equal_weight],axis=0)
            
        xsmom_df['xsmom'] = df_rets_equal
        xsmom_df.index = pd.to_datetime(xsmom_df.index)
        return xsmom_df