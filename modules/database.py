import sqlite3
import arrow


class Database():
    def __init__(self):
        """ Assigns variables for methods used more than once. """
        self.today = arrow.now().format('YYYY-MM-DD')

    def open(self, file='data/finances.sqlite'):
        """ Opens an SQLite3 database connection. """
        self.conn = sqlite3.connect(file)
        self.c = self.conn.cursor()
        return self.c

    def close(self):
        """ Closes SQLite3 database connection. """
        return self.conn.close()

    def storeData(self, networth, income, spending):
        """ Stores net worth, income, and spending in databse.

        database = finances.sqlite
        table = net_chart
        """
        self.open()
        try:
            exists = self.c.execute(
                'SELECT EXISTS(SELECT * FROM net_chart WHERE Date=? LIMIT 1)',
                (self.today,)).fetchone()
            if exists[0] == 0:
                self.c.execute('''INSERT INTO net_chart(Date, Net_Worth, Income, Spending)
                               VALUES(?,?,?,?)''',
                               (self.today, networth, income, spending))
        except sqlite3.OperationalError:
            self.c.execute(
                'CREATE TABLE "net_chart" (Date STRING, \
                                           Net_Worth INTEGER, \
                                           Income INTEGER, \
                                           Spending INTEGER)')
            self.c.execute('''INSERT INTO net_chart(Date, Net_Worth, Income, Spending)
                           VALUES(?,?,?,?)''', (
                            self.today, networth, income, spending))
        self.conn.commit()
        self.close()

    def storeStocks(self, stock_balance):
        """ Stores stock balance in databse.

        database = finances.sqlite
        table = stocks_table
        """
        self.open()
        try:
            exists = self.c.execute(
                'SELECT EXISTS(SELECT * FROM stocks_table \
                               WHERE Date=? LIMIT 1)',
                                   (self.today,)).fetchone()
            if exists[0] == 0:
                self.c.execute('''INSERT INTO stocks_table(Date, Balance)
                               VALUES(?,?)''', (self.today, stock_balance))
        except sqlite3.OperationalError:
            self.c.execute('CREATE TABLE "stocks_table" \
                           (Date STRING, balance INTEGER)')
            self.c.execute('''INSERT INTO stocks_table(Date, Balance)
                           VALUES(?,?)''', (self.today, stock_balance))
        self.conn.commit()
        self.close()

    def last_month_stocks_balance(self,
                                  lastmonth=arrow.now().replace(
                                    months=-1, day=1).format('YYYY-MM') + '%'):
        """ Searches database and returns earliest stock balance for previous month.

        database = finances.sqlite
        table = stocks_table
        """
        self.open()
        self.c.execute('SELECT balance FROM stocks_table \
                        WHERE Date LIKE ? \
                        ORDER BY Date ASC LIMIT 1', (lastmonth,))
        try:
            data = self.c.fetchone()[0]
        except TypeError:
            print('No Value for last month in database.')
            return 0
        return data
        self.close()


def main():
    pass


if __name__ == '__main__':
    main()
