import pandas as pd


class Report():

    def net_worth(self, mintworth, stock_balance):
        """ Returns total networth including mint and stocks. """
        net_worth = round(sum([mintworth, stock_balance]), 2)
        return net_worth

    def create_flow_df(self, income, spending, networth):
        """ Returns flow dataframe ready for HTML output. """
        flow = [('Income', income),
                ('Spending', spending),
                ('Flow',  income+spending),
                ('Net Worth', networth)]
        df = pd.DataFrame(flow, columns=['Type', 'Amount'])
        return df

    def stocks_overview(self, balance, last_month_stocks_balance):
        overview = [('Total Invested', balance),
                    ('Monthly Returns', balance - last_month_stocks_balance)]
        df = pd.DataFrame(overview, columns=['Type', 'Amount'])
        return df


def main():
    pass


if __name__ == '__main__':
    main()
