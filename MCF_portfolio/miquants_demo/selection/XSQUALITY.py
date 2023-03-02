from miquants_demo.data_collection.PriceLoader import load_stock_data,load_index_data
from miquants_demo.data_collection.FinanceLoader import FinanceLoader
import pandas as pd
import numpy as np
import os
import datetime
from datetime import timedelta
from sklearn.preprocessing import StandardScaler
from empyrical import stats


class XSQUALITY:
    def __init__(self, stock_list, data_folder):
        self.stock_list = stock_list
        self.data_folder = data_folder
        
        self.price_data_folder = self.data_folder+'price_data/'
        self.fundametal_data_folder = self.data_folder+'fundamental_data/'
        self.beta_folder = self.data_folder+'beta/'
        self.quality_folder = self.data_folder+'ratios/'
        self.ranking_folder = self.data_folder+'ranking/'
        
    def get_quality_data(self):
        # Check whether the specified path exists or not
        isExist = os.path.exists(self.data_folder)
        if not isExist:
            os.makedirs(self.data_folder)
        
        ## stock price data
        start = '2018-01-01'
        end = datetime.datetime.now().strftime('%Y-%m-%d')
        isExist = os.path.exists(self.price_data_folder)
        if not isExist:
            os.makedirs(self.price_data_folder)


        for symbol in self.stock_list:
            price_df = load_stock_data(symbol,start,end)
            price_df = price_df['close']
            price_df.to_csv(self.price_data_folder+symbol+'.csv')

        vnindex_df = load_index_data('VNINDEX',start,end)
        vnindex_df['close'].to_csv(self.price_data_folder+'VNINDEX'+'.csv')

        ## funda data
        isExist = os.path.exists(self.fundametal_data_folder)
        if not isExist:
            os.makedirs(self.fundametal_data_folder)

        for symbol in self.stock_list:
            funda_df = FinanceLoader(symbol,yearly='0')
            secret_bl = funda_df.get_balance_sheet()
            secret_cf = funda_df.get_cashflow()
            secret_income = funda_df.get_income_statement()
            fundamental = secret_bl.merge(secret_cf.merge(secret_income))
            fundamental = fundamental[::-1]
            fundamental.drop_duplicates(subset=['quarter', 'year'],inplace=True)
            fundamental.to_csv(self.fundametal_data_folder+symbol+'.csv')
            
    def calc_beta(self):
        year = ['2018', '2019', '2020', '2021', '2022']
        quarter = ['1','2','3','4']
        quarter_list =[y+'Q'+q for y in year for q in quarter]

        isExist = os.path.exists(self.beta_folder)
        if not isExist:
            os.makedirs(self.beta_folder)

        for locator in quarter_list:
            year = locator[:4]
            quarter = locator[-1]
            if quarter=='1':
                start ='01-01'
                end='03-31'
            if quarter=='2':
                start ='04-01'
                end='06-30'
            if quarter=='3':
                start ='07-01'
                end='09-30'
            if quarter=='4':
                start ='10-01'
                end='12-31'

            start = str(year+'-'+start)
            end = str(year+'-'+end)
            vnindex=pd.DataFrame()
            index = pd.read_csv(self.price_data_folder+'VNINDEX.csv')
            index.set_index('tradingDate',inplace=True)
            vnindex['VNINDEX'] = index[start:end]

            beta_list=[]

            for symbol in self.stock_list:
                stock_df = pd.DataFrame()
                stock  = pd.read_csv(self.price_data_folder+symbol+'.csv')
                stock.set_index('tradingDate',inplace=True)
                stock_df[symbol] = stock[start:end]
                secret_df = pd.DataFrame()
                secret_df = pd.concat([stock_df,vnindex], axis=1)
                secret_df = secret_df.pct_change()
                secret_df.dropna(inplace=True)
                beta = stats.beta(secret_df[symbol],secret_df['VNINDEX'])
                beta_list.append(beta)
            beta_df = pd.DataFrame({"Ticker": self.stock_list,"beta":beta_list})
            beta_df.to_csv(self.beta_folder+locator+'.csv')
            
    def calc_quality(self):
        year = ['2018', '2019', '2020', '2021', '2022']
        quarter = ['1','2','3','4']
        quarter_list =[y+'Q'+q for y in year for q in quarter]
        ## 2. Quality ratio
        isExist = os.path.exists(self.quality_folder)
        if not isExist:
           # Create a new directory because it does not exist
           os.makedirs(self.quality_folder)


        for symbol in self.stock_list:
            ratio_df = pd.DataFrame()
            secret_df = pd.read_csv(self.fundametal_data_folder+symbol+'.csv')
            ratio_df['ticker'] = secret_df['ticker']
            ratio_df['quarter'] = secret_df['quarter']
            ratio_df['year'] = secret_df['year']
            #Profitability
            AT=secret_df['asset'].rolling(window=2).mean()
            ratio_df['AT'] = AT
            ratio_df['ROE'] = round(secret_df['postTaxProfit']/secret_df['equity'],5)
            ratio_df['ROA'] = round(secret_df['postTaxProfit']/AT,5)
            ratio_df['GPOA'] = round(secret_df['grossProfit']/AT,5)

            if ratio_df['GPOA'].any() == 0:
                ratio_df['GPOA'] = round(secret_df['operationProfit']/AT ,5)

            ratio_df['CFOA'] = round(secret_df['fromSale']/AT ,5)

            ratio_df['GMAR'] = round((secret_df['revenue']+secret_df['costOfGoodSold'])/secret_df['revenue'],5)

            if ratio_df['GMAR'].any() == 0:
                ratio_df['GMAR'] = round((secret_df['revenue'] + secret_df['investCost'])/secret_df['stockInvest'] ,5)

            #Safety
            ratio_df['LEV'] = -(secret_df['debt'])/AT

            ratio_df['stdROE'] = ratio_df['ROE'].rolling(5).std() #STD_ROE belongs to Safety factor



            DFDelta = ratio_df.drop(['ticker', 'quarter', 'year','stdROE','LEV'], axis=1)           
            DFDelta = DFDelta.diff(periods=5).round(decimals = 5)
            DFDelta.rename({'ROE': 'dROE', 'ROA': 'dROA', 'ROA': 'dROA', 
                            'GPOA': 'dGPOA', 'CFOA': 'dCFOA', 'GMAR': 'dGMAR'}, axis=1, inplace=True)
            ratio_df = pd.concat([ratio_df,DFDelta],axis=1).dropna().reset_index(drop=True)
            ratio_df =ratio_df.drop(columns=['AT'])
            ratio_df = ratio_df[ratio_df['year']>2017].reset_index(drop=True)
            ratio_df['beta']=0

            beta_list = []
            for locator in quarter_list:
                secret_df = pd.read_csv(self.beta_folder+locator+'.csv',index_col='Ticker')
                beta_list.append(-secret_df['beta'][symbol])

            beta_list = pd.Series(beta_list).fillna(0).tolist()[-(len(ratio_df)):]
            ratio_df['beta']=beta_list

            cols_to_normalize = ratio_df.columns.drop(['ticker', 'year', 'quarter'])
            # initialize scaler object
            scaler = StandardScaler()

            # fit and transform selected columns
            ratio_df[cols_to_normalize] = scaler.fit_transform(ratio_df[cols_to_normalize])
            ratio_df['sum']=ratio_df.loc[:,'ROE':].sum(axis=1)
            ratio_df.to_csv(self.quality_folder+symbol+'.csv')
            
    def get_quality_rank(self):
        year = ['2018', '2019', '2020', '2021', '2022']
        quarter = ['1','2','3','4']
        quarter_list =[y+'Q'+q for y in year for q in quarter]
        isExist = os.path.exists(self.ranking_folder)
        if not isExist:
           # Create a new directory because it does not exist
           os.makedirs(self.ranking_folder)

        for locator in quarter_list:
            year_loc = int(locator[:4])
            quarter_loc = int(locator[-1])

            ranking_df  = pd.DataFrame()
            for symbol in self.stock_list:
                ratio_df = pd.read_csv(self.quality_folder+symbol+'.csv')
                secret_df=ratio_df[(ratio_df['quarter']==quarter_loc)&(ratio_df['year']==year_loc)]
                ranking_df = pd.concat([ranking_df,secret_df])
            # Normalize the 'sum' column using z-score method
            ranking_df['sum'] = (ranking_df['sum'] - ranking_df['sum'].mean()) / ranking_df['sum'].std()

            # Sort the dataframe based on the 'sum' column in descending order
            ranking_df = ranking_df.sort_values(by=['sum'], ascending=False).reset_index(drop=True)
            # Round the financial ratios and 'sum' column to 5 decimal places
            ranking_df = ranking_df.round(5)
            ranking_df = ranking_df.loc[:,'ticker':]
            ranking_df.to_csv(self.ranking_folder+locator+'.csv')  
    def run_quality(self):
        self.get_quality_data()
        self.calc_beta()
        self.calc_quality()
        self.get_quality_rank()
        
    def get_quality_port(self,test_year =['2020','2021','2022'], xsquality_type ='winner' ,portfolio_num = 5):
        quarter = ['1','2','3','4']
        quarter_list =[y+'Q'+q for y in test_year for q in quarter]
        
        path = self.ranking_folder
        xsquality_portfolio={}
        for locator in quarter_list:
            df = pd.read_csv(path+locator+'.csv')
            if xsquality_type=='winner':
                xsquality_portfolio[locator] = df[:portfolio_num].ticker.to_list()
            if xsquality_type=='loser':
                xsquality_portfolio[locator] = df[-portfolio_num:].ticker.to_list()
        return xsquality_portfolio
    
    def run_backtest(self, quality_port,time_delay=15,transaction_cost = 0.001, optimizer = None):
        df_rets=pd.DataFrame()
        df_rets_equal=pd.DataFrame()
        for xx in quality_port:
            year = xx[:4]
            ##stock
            my_stock_list = quality_port[xx]
            print(my_stock_list)

            delay_time = timedelta(days=time_delay)
            ##train time format
            
            quarter_train =int(xx[-1])
            if quarter_train==1:
                end='03-31'
            if quarter_train==2:
                end='06-30'
            if quarter_train==3:
                end='09-30'
            if quarter_train==4:
                end='12-31'
            end_train = pd.to_datetime(year+'-'+end) +delay_time
            start_train = end_train-timedelta(days=365)+delay_time

            print('Train',start_train,end_train)
            end_train = end_train.strftime('%Y-%m-%d')
            start_train = start_train.strftime('%Y-%m-%d')
            
            if optimizer:
                df_train = pd.DataFrame(columns=my_stock_list)
                for name in my_stock_list:
                    secret = load_stock_data(name,start_train,end_train)
                    if len(secret)>0:
                        df_train[name] = secret['close']
                df_train = df_train.dropna()
                df_train = df_train.pct_change().dropna()
                stock_list = df_train.columns.to_list()
                weight =  optimizer(df_train,my_stock_list)
                print(weight,sum(weight))

            ##test
            quarter_hold = quarter_train+1
            if quarter_hold ==5:
                quarter_hold=1
                year=str(int(year)+1)
                
            if quarter_hold==1:
                start ='01-01'
                end='04-01'
            if quarter_hold==2:
                start ='04-01'
                end='07-01'
            if quarter_hold==3:
                start ='07-01'
                end='10-01'
            if quarter_hold==4:
                start ='10-01'
                end='01-01'
                

            start_test = year+'-'+start
            end_test = year+'-'+end
            if quarter_hold==4:
                end_test = str(int(year)+1)+'-'+end
            
            start_test = pd.to_datetime(start_test)+delay_time
            end_test = pd.to_datetime(end_test)+delay_time
            end_test = end_test.strftime('%Y-%m-%d')
            start_test = start_test.strftime('%Y-%m-%d')
            print('Test',start_test,end_test)
            df_test = pd.DataFrame(columns=my_stock_list)
            for name in my_stock_list:
                secret = load_stock_data(name,start_test,end_test)
                if len(secret)>0:
                    df_test[name] = secret['close']

        #     df_test =df_test.dropna()
            df_test = df_test.pct_change()
            df_test.iloc[0]=0
            df_test.iloc[-1] = (1/len(df_test.columns))*transaction_cost
            
            if optimizer:
                rets = weight*df_test
                rets= np.sum(rets,axis=1)
                df_rets = pd.concat([df_rets,rets])

            equal_weight = (1/len(df_test.columns))*df_test
            equal_weight= np.sum(equal_weight,axis=1)
            df_rets_equal = pd.concat([df_rets_equal,equal_weight])
            print('---------------***--------------')
        df_rets_equal.index = pd.to_datetime(df_rets_equal.index)
        final_port = pd.DataFrame(columns=['xsquality'])
        if optimizer:
            df_rets.index = pd.to_datetime(df_rets.index)
            final_port['xsquality'] = df_rets
        else:
            final_port['xsquality'] = df_rets_equal
        return final_port