# import libraries
from dotenv import load_dotenv
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import logging


CONSTANTS = {
    "NOTIONAL" : {
        "VTI": .40,
        "VXUS": .20,
        "VGT": .25,
    },
    "QTY" : {
        "PTY": .15,
    },
    "AMOUNT" : 1200,
}

# method to use with tenacity to retry if API call fails
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
def submit_order_with_retry(client: TradingClient, order: MarketOrderRequest):
    print("Submitting order: ", order)
    client.submit_order(order)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_calendar_with_retry(client: TradingClient, calendar_request: GetCalendarRequest):
    print("Getting calendar: ", calendar_request)
    return client.get_calendar(calendar_request)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_price_with_retry(broker: StockHistoricalDataClient, ticker: str):
    print("Fetching price for: ", ticker)
    return broker.get_stock_latest_quote(
                    StockLatestQuoteRequest(symbol_or_symbols=ticker))[ticker].bid_price

def handler(event, context):
    # load environment variables based on paper/live trading
    load_dotenv()

    apiKey = os.getenv("API_KEY")
    secretKey = os.getenv("SECRET_KEY")

    # initialize trading client
    client = TradingClient(apiKey, secretKey, paper=False)
    broker = StockHistoricalDataClient(api_key=apiKey, secret_key=secretKey)

    # check if today is the last open day of the week
    start = end = datetime.datetime.today().date()
    end += datetime.timedelta(days=2)

    calendar = GetCalendarRequest(start=start, end=end)
    calendar = get_calendar_with_retry(client, calendar)

    print("Calendar: ", calendar)

    # make sure we have enough cash to make trades
    cash = float(client.get_account().cash)
    if cash < CONSTANTS["AMOUNT"]:
        CONSTANTS["AMOUNT"] = min(CONSTANTS["AMOUNT"], cash - 1)
        logging.error("Not enough cash to make trades. Amount changed to: ", CONSTANTS["AMOUNT"])
    elif cash < CONSTANTS["AMOUNT"] * 2:
        logging.error("Not enough cash to make trades next week. Please deoposit more cash.")

    # if today is the last open day of the week
    if len(calendar) > 0 and calendar[-1].date == start:
        print("Today is the last open day of the week.")

        # start making trades
        try:
            # notional trades
            for ticker in CONSTANTS["NOTIONAL"]:
                order = MarketOrderRequest(
                    symbol=ticker,
                    notional=CONSTANTS["NOTIONAL"][ticker] * CONSTANTS["AMOUNT"],
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
                submit_order_with_retry(client, order)
                print("Order submitted for: ", ticker)
            
            # quantity trades
            for ticker in CONSTANTS["QTY"]:
                last_price = fetch_price_with_retry(broker, ticker)
                shares = CONSTANTS["QTY"][ticker] * CONSTANTS["AMOUNT"] / last_price
                shares = int(shares + 0.5)
                print("Ticker: ", ticker, "Shares: ", shares)
                order = MarketOrderRequest(
                    symbol=ticker,
                    qty=shares,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
                submit_order_with_retry(client, order)
                print("Order submitted for: ", ticker)
        except Exception as e:
            print("Exception: ", e)
    else:
        print("Not the last open day of the week.")