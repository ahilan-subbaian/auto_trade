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

# check if today is the last open day of the week
start = end = datetime.datetime.today()
while end != 4:
    end += datetime.timedelta(days=1)

calendar = GetCalendarRequest(start=start, end=end)
calendar = client.get_calendar(calendar)

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
        last_price = yfinance.Ticker(ticker).history(period="1d")["Close"][0]
        shares = CONSTANTS["QTY"][ticker] * CONSTANTS["AMOUNT"] / last_price
        shares = int(shares + 0.5)
        order = MarketOrderRequest(
            symbol=ticker,
            qty=shares,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        client.submit_order(order)

