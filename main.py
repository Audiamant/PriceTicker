import time
import yfinance as yf
from logs import logger
from config.config import config
from config.builder import Builder
from presentation.observer import Observable
from datetime import datetime, timezone, timedelta

DATETIME_FORMAT = "%Y-%m-%d"


def get_dummy_data():
    logger.info('Generating dummy data')

def api_request(stock, start):
    prices = yf.download(stock,
                        start=start,
                        interval = "2m",
                        progress = False,
                        show_errors=False)
    return prices

def fetch_prices(stock):
    logger.info('Fetching prices')
    timeslot_end = datetime.now(timezone.utc)
    start_date = timeslot_end.strftime(DATETIME_FORMAT)
    prices = api_request(stock, start_date)

    if prices.empty:
        if timeslot_end.weekday() == 7:
            start_date = (timeslot_end - timedelta(days=3)).strftime(DATETIME_FORMAT)
            prices = api_request(stock, start_date)
        else:
            start_date = (timeslot_end - timedelta(days=2)).strftime(DATETIME_FORMAT)
            prices = api_request(stock, start_date)

    prices = prices[['Open', 'High', 'Low','Close']].values.tolist()
    return prices

def main():
    logger.info('Initialize')

    data_sink = Observable()
    builder = Builder(config)
    builder.bind(data_sink)

    try:
        while True:
            prices_list = []
            stocks_list = config.stocks
            for stock in stocks_list:
                prices_list.append(fetch_prices(stock[1]))
            start_time = time.time()
            while time.time() < start_time + config.refresh_data_interval:
                for i in range(len(stocks_list)):
                    try:
                        data_sink.update_observers(prices_list[i], stocks_list[i][0])
                        time.sleep(config.refresh_display_interval)
                    except Exception as e: 
                        logger.error(str(e))
                        time.sleep(5)
    except IOError as e:
        logger.error(str(e))
    except KeyboardInterrupt:
        logger.info('Exit')
        data_sink.close()
        exit()


if __name__ == "__main__":
    main()
