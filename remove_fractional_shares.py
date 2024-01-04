"""
This file will gather all shares from the account and sell the partial shares for every stock listed in the account.
"""

import os
import logging
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# method to use with tenacity to retry if API call fails
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
def submit_order_with_retry(client: TradingClient, order: MarketOrderRequest):
    print("Submitting order: ", order)
    client.submit_order(order)

load_dotenv()

apiKey = os.getenv("API_KEY")
secretKey = os.getenv("SECRET_KEY")

# initialize trading client
client = TradingClient(apiKey, secretKey, paper=False)

# get all positions
positions = client.get_all_positions()

print(positions)

# get list of positions with fractional shares
fractional_positions = [position for position in positions if float(position.qty) % 1 != 0]

print(fractional_positions)

# sell all fractional shares
for position in fractional_positions:
    order = MarketOrderRequest(
        symbol=position.symbol,
        qty=float(position.qty) % 1,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    answer = input(f"Do you want to sell fractional shares of {order} with position of {position}? (y/n): ")
    if answer == "y":
        submit_order_with_retry(client, order)
        print(f"Sold {order.qty} shares of {order.symbol} at market price.")
