import json
from locale import D_FMT
from requests import get
import pandas as pd
import time


def load_stock_data(ticker, start_date, end_date, resolution='D'):
    loader = BaseLoader(ticker, 'stock', resolution, start_date, end_date)
    data = loader.load_data()
    df = pd.DataFrame.from_dict(data['data'])
    if len(df) >0:
        df.set_index('tradingDate', inplace=True)
        df.index = pd.to_datetime(df.index)
        df.index = df.index.strftime('%Y-%m-%d')
    return df

def load_index_data(ticker, start_date, end_date, resolution='D'):
    loader = BaseLoader(ticker, 'index', resolution, start_date, end_date)
    data = loader.load_data()
    df = pd.DataFrame.from_dict(data['data'])
    df.set_index('tradingDate', inplace=True)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.strftime('%Y-%m-%d')
    df = df[:end_date]
    return df
    
### load price data
class BaseLoader:
    def __init__(self, ticker, data_type, resolution, start_date, end_date):
        self.ticker = ticker
        self.data_type = data_type
        self.resolution = resolution
        self.start_date = start_date
        self.end_date = end_date

    def _convert_to_timestamp(self, date_str):
        time_format = '%Y-%m-%d'
        return str(int(time.mktime(time.strptime(date_str, time_format))))

    def load_data(self):
        start_timestamp = self._convert_to_timestamp(self.start_date)
        end_timestamp = self._convert_to_timestamp(self.end_date)
        api_load = f"https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term?ticker={self.ticker}&type={self.data_type}&resolution={self.resolution}&from={start_timestamp}&to={end_timestamp}"
        data = json.loads(get(api_load).text)
        return data
