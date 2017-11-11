import mintapi
import arrow
import pandas as pd
import sys
sys.path.append("..")
from modules import config


class Calculation():
    def __init__(self):
        pass

    def transactions_by_month_name(self,
                                   month=None,
                                   year=arrow.utcnow().format('YYYY')):
        """ Returns a dataframe for the month & year selected.
        Keyword Arguments:
        month -- (Required) Input: String. Ex. 'march'
        year -- (Optional) Input: Int. Ex. 2017
        """
        if month is None:
            try:
                month = self.config['summary']['month']
                if self.config['summary']['month'] is None:
                    return self.lastMonthDF
            except:
                return self.lastMonthDF
        startDate = arrow.get(
            '{} {}'.format(month, year), 'MMMM YYYY').format('YYYY-MM-DD')
        endDate = arrow.get(
            '{} {}'.format(month, year),
            'MMMM YYYY').ceil('month').format('YYYY-MM-DD')
        df = self.transactionsDF[endDate:startDate]
        return df

    def last_month_transactions(self):
        """ Returns a dataframe for last months transactions. """
        startDate, endDate = self.range_by_num_months(months=1)
        df = self.transactionsDF[endDate:startDate]
        if df.empty:
            df = self.transactionsDF[startDate:endDate]
        return df

    def range_by_num_months(self, months):
        """ Expects number of months and returns start and end date. """
        now = arrow.utcnow()
        startDate = now.shift(
            months=-months).replace(day=1).format('YYYY-MM-DD')
        endDate = now.shift(months=-1).ceil('month').format('YYYY-MM-DD')
        return startDate, endDate

    def get_income(self, month=None):
        """ Retrieves total amount of Income. """
        if month is None:
            try:
                month = self.config['summary']['month']
                df = self.transactions_by_month_name('{}'.format(month))
                if self.config['summary']['month'] is None:
                    df = self.last_month_transactions()
            except:
                df = self.last_month_transactions()
        else:
            df = self.transactions_by_month_name('{}'.format(month))
        totalIncome = df.loc[df.Category == 'Income', 'Amount'].sum()
        return totalIncome

    def get_spending(self, month=None):
        """ Retrieves total amount of money spent. """
        if month is None:
            try:
                month = self.config['month']
                df = self.transactions_by_month_name('{}'.format(month))
                if self.config['summary']['month'] is None:
                    df = self.lastMonthDF
            except:
                df = self.lastMonthDF
        else:
            df = self.transactions_by_month_name('{}'.format(month))
        df = df.loc[(df.Category != 'Transfer') &
                    (df.Category != 'Credit Card Payment')]
        totalSpending = df.Amount[df['Amount'] < 0].sum()
        return totalSpending

    def mint_worth(self):
        mint_worth = self.mintapi.get_net_worth()
        return mint_worth


class Dataframe(Calculation):

    def __init__(self):
        """ Connects to Mintapi and assigns variables for methods used
        more than once. """
        self.config = config.load()
        self.mintapi = mintapi.Mint(self.config['mint']['user'],
                                    self.config['mint']['pass'],
                                    self.config['mint']['ius_session'],
                                    self.config['mint']['thx_guid'])
        self.mintapi.initiate_account_refresh()
        self.transactionsDF = self.transactionsDF()
        self.lastMonthDF = self.last_month_transactions()

    def transactionsDF(self):
        """ Returns a dataframe with all transactions in mint. """
        df = self.mintapi.get_transactions()
        df.loc[df.transaction_type == 'debit', 'amount'] *= -1
        df.drop(['labels', 'notes', 'transaction_type',
                 'original_description'], axis=1, inplace=True)
        df.columns = ['Date', 'Description', 'Amount',
                      'Category', 'Account Name']
        df.Category = df.Category.str.title()
        df.set_index('Date', inplace=True)
        df.sort_index(ascending=False, inplace=True)
        return df

    def accountsDF(self):
        """ Returns a dataframe with account names and balances. """
        accounts = self.mintapi.get_accounts(True)
        df = pd.DataFrame.from_records(accounts)
        df = df.loc[:, ['userName', 'value']]
        df.columns = ['Account Name', 'Balance']
        df.drop([0, 6], inplace=True)
        return df


def main():
    data = Dataframe()
    print(data.get_income())


if __name__ == '__main__':
    main()
