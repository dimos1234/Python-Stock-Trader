import time as true_time
import pprint
import pathlib
import operator
import pandas as pd

from datetime import datetime
from datetime import timedelta
from configparser import ConfigParser

from pyrobot.robot import PyRobot
from pyrobot.indicators import Indicators

config = ConfigParser()
config.read("configs/config.ini")

CLIENT_ID = config.get("main", "CLIENT_ID")
REDIRECT_URI = config.get("main", "REDIRECT_URI")
CREDENTIALS_PATH = config.get("main", "JSON_PATH")
ACCOUNT_NUMBER = config.get("main", "ACCOUNT_NUMBER")

trading_robot = PyRobot(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    credentials_path=CREDENTIALS_PATH,
    trading_account=ACCOUNT_NUMBER,
    paper_trading=True
)

trading_robot_portfolio = trading_robot.create_portfolio()

multi_position = [
    {
        "asset_type": "equity",
        "quantity": 2,
        "purchase_price": 4.00,
        "symbol": "TSLA",
        "purchase_date": "2021-03-04"
    },
    {
        "asset_type": "equity",
        "quantity": 2,
        "purchase_price": 4.00,
        "symbol": "SQ",
        "purchase_date": "2021-03-04"
    }
]

new_positions = trading_robot.portfolio.add_positions(positions=multi_position)
#pprint.pprint(new_positions)

trading_robot.portfolio.add_position(
    symbol="MSFT",
    quantity=10,
    purchase_price=10.00,
    asset_type="equity",
    purchase_date="2021-03-04"
)

#pprint.pprint(trading_robot.portfolio.positions)

#Check to see if the market is open.
if trading_robot.pre_market_open:
    print("Regular Market Open")
else:
    print("Regular Market Not Open")

if trading_robot.pre_market_open:
    print("Pre Market Open")
else:
    print("Pre Market Not Open")

if trading_robot.post_market_open:
    print("Post Market Open")
else:
    print("Post Market Not Open")

# Grab the current quotes in our portfolio
current_quotes = trading_robot.grab_current_quotes()
#pprint.pprint(current_quotes)

end_date = datetime.today()
start_date = end_date - timedelta(days=30)

historical_prices = trading_robot.grab_historical_prices(
    start=start_date,
    end=end_date,
    bar_size=1,
    bar_type="minute"
)

stock_frame = trading_robot.create_stock_frame(data=historical_prices["aggregated"])
pprint.pprint(stock_frame.frame.head(n=20))

new_trade = trading_robot.create_trade(
    trade_id="long_msft",
    enter_or_exit="enter",
    long_or_short="long",
    order_type="lmt",
    price=150.00
)

new_trade.good_till_cancel(cancel_time=datetime.now() + timedelta(minutes=90))

new_trade.modify_session(session="am")

new_trade.instrument(
    symbol="MSFT",
    quantity=2,
    asset_type="EQUITY"
)

new_trade.add_stop_loss(
    stop_size=.10,
    percentage=False
)

pprint.pprint(new_trade.order)

#create a new indicator client
indicator_client = Indicators(price_data_frame=stock_frame)

#add the rsi indicator
indicator_client.rsi(period=14)

#add a 200-day simple moving average
indicator_client.sma(period=200)

#add a 50 day exponential moving average
indicator_client.ema(period=50)

#add a signal to check for
indicator_client.set_indicator_signals(
    indicator="rsi",
    buy=40.0,
    sell=20.0,
    condition_buy=operator.ge,
    condition_sell=operator.le
)

#define a trade dictionary
trades_dict = {
    "MSFT": {
        "trade_func": trading_robot.trades["long_msft"],
        "trade_id": trading_robot.trades["long_msft"].trade_id
    }
}

while True:
    #Grab the latest bar
    latest_bars = trading_robot.get_latest_bar()

    #add those bars to the stockframe
    stock_frame.add_rows(data=latest_bars)

    #refresh the indicators
    indicator_client.refresh()

    print("="*50)
    print("Current StockFrame")
    print("-"*50)
    print(stock_frame.symbol_groups.tail())
    print("-"*50)
    print("")

    #signals = indicator_client.check_signals()

    last_bar_timestamp = trading_robot.stock_frame.frame.tail(1).index.get_level_values(1)

    trading_robot.wait_till_next_bar(last_bar_timestamp=last_bar_timestamp)