# Portfolio Manager For Alpaca Trade API

The script [`portfolio_manager.py`](./portfolio_manager.py) contains a class that
makes it easy to manage busket of stocks based on the shares or weight for each symbol name.
It is designed so that you can feed your own desired portfolio either by
calculation or simply from CSV.

## Usage

You need to obtain Alpaca API key, found in the [dashboard](https://app.alpaca.markets/) and set
it in the environment variables. Please read [API documents](https://docs.alpaca.markets/) or
[Python SDK documents](https://github.com/alpacahq/alpaca-trade-api-python) for more details.

The `PortfolioManager` class implements the following methods.

- add_items(items)
  Add desired portfolio structure, in two dimentional list.
- rebalance(order_style, timeout=60)
  Start rebalancing based on the shares by sending orders now. `order_style` can be either "timeout" or "block"
- percent_rebalance(order_style, timeout=60)
  Start rebalancing based on the percentage by sending orders now. `order_style` can be either "timeout" or "block"

The `timeout` order style times out if orders are not executed in the specified timeout seconds.
The `block` order style blocks the process indifinitely until orders are executed.

## Example Code

```py
import os
from portfolio_manager import PortfolioManager

os.environ['APCA_API_KEY_ID'] = 'API_KEY_ID'
os.environ['APCA_API_SECRET_KEY'] = 'API_SECRET_KEY'

manager = PortfolioManager()
# Hedging SPY with GLD 1:1
manager.add_items([
    ['SPY', 0.5],
    ['GLD', 0.5],
])
manager.percent_rebalance('block')
```
