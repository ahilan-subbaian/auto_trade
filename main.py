# Auto trades stocks on the last open day of 
# the week. Uses Alpaca API to process trades.

# import libraries
from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime
import yfinance
from tenacity import retry, stop_after_attempt, wait_exponential


CONSTANTS = {
    "NOTIONAL" : {
        "VTI": .40,
        "VXUS": .20,
        "VGT": .25,
    },
    "QTY" : {
        "PTY": .15,
    },
    "AMOUNT" : 100,
}

# load environment variables based on paper/live trading
load_dotenv()

apiKey = os.getenv("API_KEY_LIVE")
secretKey = os.getenv("SECRET_KEY_LIVE")


# initialize trading client
client = TradingClient(apiKey, secretKey)

# method to use with tenacity to retry if API call fails
# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def submit_order_with_retry(client, order):
    client.submit_order(order)

# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_calendar_with_retry(client, calendar_request):
    return client.get_calendar(calendar_request)

# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_price_with_retry(ticker):
    return yfinance.Ticker(ticker).history(period="1d")["Close"][0]

# check if today is the last open day of the week
start = end = datetime.datetime.today()
end += datetime.timedelta(days=2)

calendar = GetCalendarRequest(start=start, end=end)
calendar = get_calendar_with_retry(client, calendar)

# if today is the last open day of the week
if len(calendar) > 0 and calendar[-1].date == start:

    # start making trades

    # notional trades
    for ticker in CONSTANTS["NOTIONAL"]:
        order = MarketOrderRequest(
            symbol=ticker,
            notional=CONSTANTS["NOTIONAL"][ticker] * CONSTANTS["AMOUNT"],
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        client.submit_order(order)
    
    # quantity trades
    for ticker in CONSTANTS["QTY"]:
        last_price = fetch_price_with_retry(ticker)
        shares = CONSTANTS["QTY"][ticker] * CONSTANTS["AMOUNT"] / last_price
        shares = int(shares + 0.5)
        order = MarketOrderRequest(
            symbol=ticker,
            qty=shares,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        client.submit_order(order)

