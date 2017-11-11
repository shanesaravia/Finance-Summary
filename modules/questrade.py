import os
import json
import requests
import yaml
from pandas.io.json import json_normalize
import sys
sys.path.append("..")
from modules import config
from modules import errors
from modules import logger


class Token():

    def check_token(self, file, account=1):
        self.logger.debug('checking token.')
        try:
            with open(file, 'r') as f:
                token = json.load(f)
                headers = {'Authorization':
                           f"{token['token_type']} {token['access_token']}"}
                url = f'{token["api_server"]}v1/accounts'
                r = requests.get(url, headers=headers)
                data = r.json()
                if 'accounts' in data:
                    self.logger.info(f'Token{account} retrieved successfully.')
                    return True
                else:
                    self.logger.debug('token failed.')
                    return False
        except:
            self.logger.debug('token failed.')
            return False

    def refresh_token(self, file):
        self.logger.debug('refreshing token.')
        with open(file, 'r') as f:
            try:
                token = json.load(f)
                refreshToken = token['refresh_token']
                self.create_token(file, refreshToken)
            except json.decoder.JSONDecodeError:
                return False

    def create_token(self, file, token):
        self.logger.debug('creating token.')
        url = 'https://login.questrade.com/oauth2/token'
        r = requests.get(
            f'{url}?grant_type=refresh_token&refresh_token={token}')
        resp = r.text
        with open(file, 'w') as f:
            f.write(resp)

    def get_token(self, account=1):
        file = f'modules/tokens/refreshToken{account}.txt'
        manualToken = self.config['questrade'][f'refresh_token{account}']
        if not os.path.isfile(file):
            self.create_token(file, manualToken)
            if self.check_token(file) is not True:
                self.logger.error('Unable to refresh token.')
                raise errors.TokenError(
                    'Please update refresh_token manually in config.')
        else:
            if self.check_token(file, account) is not True:
                self.refresh_token(file)
            else:
                return
            if self.check_token(file, account) is not True:
                self.create_token(file, manualToken)
            else:
                return
            if self.check_token(file, account) is not True:
                self.logger.error('Unable to refresh token.')
                raise errors.TokenError(
                    'Please update refresh_token manually in config.')
            else:
                return


class Prepare(Token):
    def __init__(self):
        pass

    def questradeBalances(self, account, refresh='refreshToken1.txt'):
        """ Input account & token and returns account balance. """
        with open(f'modules/tokens/{refresh}', 'r') as f:
            try:
                token = json.load(f)
            except:
                raise errors.TokenError(
                    'Please update refresh_token manually in config.')
        headers = {'Authorization':
                   f"{token['token_type']} {token['access_token']}"}
        api = token["api_server"]
        questrade = self.config["questrade"][account]
        url = f'{api}v1/accounts/{questrade}/balances'
        r = requests.get(url, headers=headers)
        balance = r.json()['combinedBalances'][0]['totalEquity']
        return balance

    def questradeStocks(self, account, refresh='refreshToken1.txt'):
        """ Returns dataframe with stocks data

        Purchase Value
        Market Value
        Loss/Gain
        """
        with open(f'modules/tokens/{refresh}', 'r') as f:
            try:
                token = json.load(f)
            except JSONDecodeError:
                raise errors.TokenError(
                    'Please update refresh_token manually in config.')
        headers = {'Authorization':
                   f"{token['token_type']} {token['access_token']}"}
        api = token["api_server"]
        questrade = self.config["questrade"][account]
        url = f'{api}v1/accounts/{questrade}/positions'
        r = requests.get(url, headers=headers)
        df = json_normalize(r.json()['positions'])
        return df

    def prepareDF(self, df, percentage=None):
        """ Prepares the stocks dataframe by dropping unnecessary data. """
        df.drop(['closedPnl', 'closedQuantity', 'isRealTime',
                 'isUnderReorg', 'symbolId', 'averageEntryPrice',
                 'currentPrice', 'openQuantity'], axis=1, inplace=True)
        df = df[['symbol', 'totalCost', 'currentMarketValue', 'openPnl']]
        df.columns = ['Ticker', 'Purchase Value', 'Market Value', 'Loss/Gain']
        df.set_index('Ticker', inplace=True)
        if percentage is not None:
            df = df.apply(lambda x: round(x * percentage, 2))
        else:
            df = df.apply(lambda x: round(x, 2))
        df = df.reset_index()
        return df


class Questrade(Prepare):

    def __init__(self):
        """ Intiates variables for account balances and stocks data. """
        self.config = config.load()
        self.logger = logger.log()
        self.get_token(1)
        self.get_token(2)
        self.RRSPbalance, self.RRSPdata = self.questradeRRSP()
        self.TFSAbalance, self.TFSAdata = self.questradeTFSA()
        self.TFSA2balance, self.TFSA2data = self.questradeTFSA2()

    def questradeRRSP(self):
        """ Returns RRSP account balance and dataframe with stock data. """
        balance = self.questradeBalances('RRSP')
        df = self.questradeStocks('RRSP')
        df = self.prepareDF(df)
        return balance, df

    def questradeTFSA(self):
        """ Returns TFSA account balance and dataframe with stock data. """
        current_amount = self.questradeBalances('TFSA')
        original_amount = self.config['questrade']['originalTFSA']
        contributed = self.config['questrade']['contributedTFSA']
        percentage = (current_amount - original_amount) / original_amount
        perc_in_dollars = percentage * contributed
        balance = contributed + perc_in_dollars
        df = self.questradeStocks('TFSA')
        df = self.prepareDF(df, percentage=percentage)
        return balance, df

    def questradeTFSA2(self):
        """ Returns TFSA2 account balance and dataframe with stock data. """
        balance = self.questradeBalances(
            account='TFSA2', refresh='refreshToken2.txt')
        percentage = .5
        balance = balance * percentage
        df = self.questradeStocks(account='TFSA2', refresh='refreshToken2.txt')
        df = self.prepareDF(df, percentage=percentage)
        return balance, df

    def stockBalance(self):
        """ Returns a total stocks balance of all three account balances. """
        stockbalance = round(sum([self.TFSAbalance,
                                  self.RRSPbalance,
                                  self.TFSA2balance]), 2)
        return stockbalance


def main():
    questrade = Questrade()


if __name__ == '__main__':
    main()
