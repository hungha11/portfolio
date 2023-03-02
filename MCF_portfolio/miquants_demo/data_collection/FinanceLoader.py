
import json
from locale import D_FMT
from requests import get
import pandas as pd
import requests

class FinanceLoader:
    def __init__(self, symbol, yearly):
        self.symbol = symbol
        self.yearly = yearly
        self.session = requests.Session()

    def _get_data(self, type_):
        df = pd.DataFrame()
        url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{self.symbol}/{type_}?yearly={self.yearly}&isAll=true"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = json.loads(response.text)
            temp = pd.DataFrame.from_dict(data)
            df = pd.concat([df, temp])
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while making the API request: {e}")
        return df

    def get_income_statement(self):
        """Return a dataframe of the income statement for the symbols in symbol_list."""
        return self._get_data("incomestatement")
    
    def get_cashflow(self):
        """Return a dataframe of the cashflow statement for the symbols in symbol_list."""
        return self._get_data("cashflow")

    def get_balance_sheet(self):
        """Return a dataframe of the balance sheet for the symbols in symbol_list."""
        return self._get_data("balancesheet")
    
    def get_dividend(self):
        div_url = f'https://apipubaws.tcbs.com.vn/tcanalysis/v1/company/{self.symbol}/dividend-payment-histories?page=0&size=1000'
        data = json.loads(get(div_url).text)['listDividendPaymentHis']

        secret_list = ['ticker','cashYear','exerciseDate','cashDividendPercentage','issueMethod']
        div_df = pd.DataFrame.from_records([{k: v for k, v in item.items() if k in secret_list} for item in data])
        return div_df