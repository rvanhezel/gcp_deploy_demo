from src.logger import Logger
import logging
from dotenv import load_dotenv
from src.configuration import Configuration
import pandas as pd
from src.utils import load_market_data
from src.period import Period
from src.enums import Signal, OrderType
from src.order import Order
from src.alpaca_broker_api import AlpacaAPI
import time


if __name__ == '__main__':
    # Load API keys
    load_dotenv()

    Logger()
    cfg = Configuration('run.cfg')

    broker_api = AlpacaAPI()
    broker_api.connect()    
        
    now = pd.Timestamp.now(tz=cfg.timezone)
    today_open = pd.Timestamp(
            now.year, 
            now.month, 
            now.day, 
            int(cfg.market_open_time[:2]), 
            int(cfg.market_open_time[2:]),
            tz=cfg.timezone)
    
    today_close = pd.Timestamp(
            now.year, 
            now.month, 
            now.day, 
            16, 
            30,
            tz=cfg.timezone)
        
    md_time_lag = Period('10min')
    ticker = 'TSLA'

    market_data = load_market_data(
        ticker, 
        cfg.tick_interval, 
        today_open - pd.Timedelta(days=1), 
        today_close - pd.Timedelta(days=1),
        cfg.timezone)


    while today_open < now < today_close:
        logging.debug(f'Time is now {now}. Can trade')

        latest_md_time = market_data.index.max()

        if now - latest_md_time < pd.Timedelta(str(md_time_lag)):
            time_elapsed = (now - latest_data).total_seconds()
            time_to_sleep = pd.Timedelta(str(md_time_lag)).total_seconds() - time_elapsed
            logging.info(f"Sleeping for {time_to_sleep/60} mins")
            time.sleep(time_to_sleep)   
        
        time.sleep(1)
        now = pd.Timestamp.now(tz=cfg.timezone)

        logging.info(f'Loading market data from {latest_md_time} to {now}')
        latest_data = load_market_data(ticker, cfg.tick_interval, latest_md_time, now, cfg.timezone)

        market_data = pd.concat([market_data, latest_data], axis=0)
        market_data.drop_duplicates(inplace=True)
        market_data.sort_index(ascending=False, inplace=True)

        print(market_data.head(15))

        current_price = market_data['close'].iloc[-1]
        open_price = market_data['open'].iloc[0]

        message_str = f"{ticker} open price: {open_price}.  Latest close price: {current_price}"
        logging.debug(message_str)

        if open_price < current_price:
            signal = Signal.BUY
        elif open_price > current_price:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD

        logging.info(f"Signal for {ticker}: {signal}")

        units = 100 / current_price
        order = Order(ticker, signal, units, None, OrderType.MARKET)

        broker_api.place_orders(order)
        now = pd.Timestamp.now(tz=cfg.timezone)



    logging.debug(f'Time is now {now}. Market opens at {today_open} and closes at {today_close}')
    logging.info(f"Exiting run")
