import json
from locale import D_FMT
from requests import get
import requests
import pandas as pd
import datetime
import time



def load_basic_info(symbol):
    url = f'https://wichart.vn/wichartapi/wichart/popquick?code={symbol}'
    data = get(url).json()
    if len(data)>0:
        data = data[0]
    elif len(data)==0:
        data = data
    return data
    
def add_in(symbol):
    url = f'https://fiin-fundamental.ssi.com.vn/Snapshot/GetSnapshot?&OrganCode={symbol}'
    data = get(url).json()
    data = data['items'][0]['summary']
    return data

def load_universe():
    '''
    Returns:
    All stock 'Ticker', 'Company name', 'Exchange', 'OutstandingShares', 'Margin', 'Industry_lev3', 'Industry_lev4',
               'Listed_date'
    '''    
    columns = ['Ticker','Company_code', 'Company_name', 'Exchange', 'OutstandingShares', 'Margin', 'Industry_lev3', 'Industry_lev4',
               'Listed_date','freeFloat','freeFloatRate','statePercentage','foreignerPercentage','maximumForeignPercentage']
    ticker_df = pd.DataFrame(columns=columns)
    organ_data = get('https://fiin-core.ssi.com.vn/Master/GetListOrganization?language=vi').json()
    organ_data = organ_data['items']

    ticker_organ =[]
    organ_code=[]
    organ_name=[]
    for i in range(len(organ_data)):
        ticker_organ.append(organ_data[i]['ticker'])
        organ_code.append(organ_data[i]['organCode'])
        organ_name.append(organ_data[i]['organName'])
    ticker_df['Ticker'] = ticker_organ
    ticker_df['Company_code']=organ_code
    ticker_df['Company_name'] = organ_name
    ticker_df.set_index('Ticker', inplace=True)
    
    for name in ticker_df.index:
        secret_df = load_basic_info(name)
        secret_df_add_in = add_in(ticker_df.loc[name]['Company_code'])
        if len(secret_df) > 0:
            ticker_df['Exchange'].loc[name] = secret_df['san']
            ticker_df['OutstandingShares'].loc[name] = secret_df['soluongluuhanh']
            ticker_df['Margin'].loc[name] = secret_df['kyquy']
            ticker_df['Industry_lev3'].loc[name] = secret_df['nganhcap3_vi']
            ticker_df['Industry_lev4'].loc[name] = secret_df['nganhcap4_vi']
            ticker_df['Listed_date'].loc[name] = secret_df['ngayniemyet']
            if secret_df_add_in is None:
                pass
            else:
                ticker_df['freeFloat'].loc[name] = secret_df_add_in['freeFloat']
                ticker_df['freeFloatRate'].loc[name] = secret_df_add_in['freeFloatRate']
                ticker_df['statePercentage'].loc[name] = secret_df_add_in['statePercentage']
                ticker_df['foreignerPercentage'].loc[name] = secret_df_add_in['foreignerPercentage']
                ticker_df['maximumForeignPercentage'].loc[name] = secret_df_add_in['maximumForeignPercentage']

    return ticker_df

def get_vn30_list():
    vn30= requests.get('https://services.entrade.com.vn/chart-api/symbols?type=vn30').json()
    return vn30['symbols']