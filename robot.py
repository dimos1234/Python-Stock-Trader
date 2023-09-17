import pandas as pd

from td.client import TDClient
from td.utils import TDUtilities

from datetime import datetime
from datetime import time
from datetime import timezone
from datetime import timedelta

import time as time_true
import pathlib
import json

from typing import List
from typing import Dict
from typing import Optional
from typing import Union

from pyrobot.portfolio import Portfolio
from pyrobot.stock_frame import StockFrame
from pyrobot.trades import Trade

milliseconds_since_epoch = TDUtilities().milliseconds_since_epoch

class PyRobot():

    def __init__(self, client_id: str, redirect_uri: str, credentials_path: str = None, trading_account: str = None, paper_trading: bool = True) -> None:
        self.trading_account: str = trading_account
        self.client_id: str = client_id
        self.redirect_uri: str = redirect_uri
        self.credentials_path: str = credentials_path
        self.session: TDClient = self._create_session()
        self.trades: dict = {}
        self.historical_prices: dict = {}
        self.stock_frame = None
        self.paper_trading = paper_trading

    def _create_session(self) -> TDClient:
        td_client = TDClient(client_id=self.client_id, redirect_uri=self.redirect_uri, credentials_path=self.credentials_path)
        td_client.login()
        return td_client

    @property
    def pre_market_open(self) -> bool:
        pre_market_start_time = datetime.utcnow().replace(hour=12, minute=00, second=00).timestamp()
        market_start_time = datetime.utcnow().replace(hour=13, minute=30, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self) -> bool:
        post_market_end_time = datetime.utcnow().replace(hour=22, minute=30, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=20, minute=00, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if post_market_end_time >= right_now >= market_end_time:
            return True
        else:
            return False

    @property
    def regular_market_open(self) -> bool:
        market_start_time = datetime.utcnow().replace(hour=13, minute=30, second=00).timestamp()
        market_end_time = datetime.utcnow().replace(hour=20, minute=00, second=00).timestamp()
        right_now = datetime.utcnow().timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    def create_portfolio(self):
        self.portfolio = Portfolio(account_number=self.trading_account)
        self.portfolio.td_client = self.session

        return self.portfolio

    def create_trade(self, trade_id: str, enter_or_exit: str, long_or_short: str, order_type: str = "mkt", price: float = 0.0, stop_limit_price: float = 0.0) -> Trade:
        trade = Trade()
        trade.new_trade(trade_id=trade_id, order_type=order_type, long_or_short=long_or_short, enter_or_exit=enter_or_exit, price=price, stop_limit_price=stop_limit_price)
        self.trades[trade_id] = trade

        return trade

    def grab_current_quotes(self) -> dict:
        symbols = self.portfolio.positions.keys()
        quotes = self.session.get_quotes(instruments=list(symbols))

        return quotes

    def grab_historical_prices(self, start: datetime, end: datetime, bar_size: int = 1, bar_type: str = "minute", symbols: Optional[List[str]] = None) -> dict:
        self._bar_size = bar_size
        self._bar_type = bar_type

        start = str(milliseconds_since_epoch(dt_object=start))
        end = str(milliseconds_since_epoch(dt_object=end))
        
        new_prices = []

        if not symbols:
            symbols = self.portfolio.positions

        for symbol in symbols:
            historical_prices_response = self.session.get_price_history(
                symbol=symbol,
                period_type="day",
                start_date=start,
                end_date=end,
                frequency_type=bar_type,
                frequency=bar_size,
                extended_hours=True
            )

            self.historical_prices[symbol] = {}
            self.historical_prices[symbol]["candles"] = historical_prices_response["candles"]

            for candle in historical_prices_response["candles"]:
                new_price_mini_dict = {}
                new_price_mini_dict["symbol"] = symbol
                new_price_mini_dict["open"] = candle["open"]
                new_price_mini_dict["close"] = candle["close"]
                new_price_mini_dict["high"] = candle["high"]
                new_price_mini_dict["volume"] = candle["volume"]
                new_price_mini_dict["datetime"] = candle["datetime"]
                new_prices.append(new_price_mini_dict)

        self.historical_prices["aggregated"] = new_prices

        return self.historical_prices


    def create_stock_frame(self, data: List[dict]) -> StockFrame:
        self.stock_frame = StockFrame(data=data)

        return self.stock_frame

    def get_latest_bar(self) -> List[dict]:
        # Grab the info from the last quest.
        bar_size = self._bar_size
        bar_type = self._bar_type

        # Define the start and end date.
        end_date = datetime.today()
        start_date = end_date - timedelta(days=1)
        start = str(milliseconds_since_epoch(dt_object=start_date))
        end = str(milliseconds_since_epoch(dt_object=end_date))

        latest_prices = []

        # Loop through each symbol.
        for symbol in self.portfolio.positions:

            try:

                # Grab the request.
                historical_prices_response = self.session.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            except:

                time_true.sleep(2)

                # Grab the request.
                historical_prices_response = self.session.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            # parse the candles.
            for candle in historical_prices_response['candles'][-1:]:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                latest_prices.append(new_price_mini_dict)

        return latest_prices

    def wait_till_next_bar(self, last_bar_timestamp: pd.DatetimeIndex) -> None:
        last_bar_time = last_bar_timestamp.to_pydatetime()[0].replace(tzinfo=timezone.utc)
        next_bar_time = last_bar_time + timedelta(seconds=60)
        curr_bar_time = datetime.now(tz=timezone.utc)

        last_bar_timestamp = int(last_bar_time.timestamp())
        next_bar_timestamp = int(next_bar_time.timestamp())
        curr_bar_timestamp = int(curr_bar_time.timestamp())

        _time_to_wait_bar = next_bar_timestamp - last_bar_timestamp
        time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

        if time_to_wait_now < 0:
            time_to_wait_now = 0

        print("="*80)
        print("Pausing for the next bar")
        print("-"*80)
        print("Curr Time: {time_curr}".format(time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")))
        print("Next Time: {time_next}".format(time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")))
        print("Sleep Time: {seconds}".format(seconds=time_to_wait_now))
        print("-"*80)
        print("")

        time_true.sleep(time_to_wait_now)