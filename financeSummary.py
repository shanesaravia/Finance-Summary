from jinja2 import Environment, FileSystemLoader
import os
from dateutil import parser
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from modules.mint import Dataframe
from modules.questrade import Questrade
from modules.database import Database
from modules.report import Report
from modules import config


class Graph():
    def graph_data(self):
        """ Graphs networth chart and income/spending chart to image. """
        self.database.open()
        self.database.c.execute('SELECT * FROM net_chart ORDER BY Date ASC')
        data = self.database.c.fetchall()
        dates = []
        net_worth = []
        income = []
        spending = []
        for row in data:
            dates.append(parser.parse(row[0]))
            net_worth.append(row[1])
            income.append(row[2])
            spending.append(abs(row[3]))

        plt.style.use('seaborn-darkgrid')
        fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True)
        # DATA
        ax1.plot(dates, net_worth, '-', label='Net Worth')
        ax2.plot(dates, income, '-', label='Income')
        ax2.plot(dates, spending, '-', label='Spending')
        # MONTH FORMATTING
        xfmt = mdates.DateFormatter('%b %Y')
        ax1.xaxis.set_major_formatter(xfmt)
        fig.autofmt_xdate() # automatically rotate dates appropriately
        months = mdates.MonthLocator()
        ax1.xaxis.set_major_locator(months)
        # CURRENCY FORMATTING
        # fmt = '${x:,.0f}'
        tick = mtick.StrMethodFormatter('${x:,.0f}')
        ax1.yaxis.set_major_formatter(tick)
        ax2.yaxis.set_major_formatter(tick)
        # TITLES
        ax1.set_title('Net Worth')
        ax2.set_title('Income & Spending')
        # DISPLAY
        plt.subplots_adjust(hspace=0.3)
        ax1.legend(), ax2.legend()
        plt.savefig(f'static/images/{self.config["graphs"]["netchart"]}',
                    bbox_inches='tight')
        self.database.close()


class Summary(Graph):

    def __init__(self):
        """ Creates objects for each module required and variables
        for each method required.

        objects = mint, questrade, database, report
        variables = transactions, accounts, income, spending, networth, flow
        """
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.config = config.load()
        self.mint = Dataframe()
        self.questrade = Questrade()
        self.database = Database()
        self.report = Report()
        self.stocks_balance = self.questrade.stockBalance()
        self.transactions = self.mint.transactions_by_month_name()
        self.accounts = self.mint.accountsDF()
        self.income = self.mint.get_income()
        self.spending = self.mint.get_spending()
        self.networth = self.report.net_worth(self.mint.mint_worth(),
                                              self.stocks_balance)
        self.flow = self.report.create_flow_df(self.income,
                                               self.spending,
                                               self.networth)
        self.stocks_overview = self.report.stocks_overview(
            self.stocks_balance, self.database.last_month_stocks_balance())

    def convert_to_html(self):
        """ Converts all data into HTML and writes to index.html """
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("templates/base.html")
        template_vars = {
            "last_month_transactions": self.transactions.reset_index().to_html(
                classes='transactionstable',
                index=False,
                justify='center'),
            "flow": self.flow.to_html(
                classes='flowtable',
                index=False,
                justify='center'),
            "accounts": self.accounts.to_html(
                classes='accountstable',
                index=False,
                justify='center'),
            "netchart": f"../static/images/{self.config['graph']['netchart']}",
            "TFSAdata": self.questrade.TFSAdata.to_html(
                classes='TFSAdata',
                index=False,
                justify='center'),
            "RRSPdata": self.questrade.RRSPdata.to_html(
                classes='RRSPdata',
                index=False,
                justify='center'),
            "TFSA2data": self.questrade.TFSA2data.to_html(
                classes='TFSA2data',
                index=False,
                justify='center'),
            "stocks_overview": self.stocks_overview.to_html(
                classes='stocks_overview',
                index=False,
                justify='center')
                        }
        html_out = template.render(template_vars)
        with open("templates/index.html", "w") as f:
            f.write(html_out)

    def open_summary(self):
        """ Opens summary page in browser. """
        os.chdir('templates/')
        os.startfile("index.html")


def main():
    summary = Summary()
    summary.database.storeData(summary.networth,
                               summary.income,
                               summary.spending)
    summary.database.storeStocks(summary.questrade.stockBalance())
    summary.graph_data()
    summary.convert_to_html()
    summary.open_summary()


if __name__ == '__main__':
    main()
