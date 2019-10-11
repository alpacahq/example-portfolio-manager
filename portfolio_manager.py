import alpaca_trade_api as tradeapi
import threading
import time


class PortfolioManager():
    def __init__(self):
        self.api = tradeapi.REST()

        self.r_positions = {}

    def format_percent(self, num):
        if(str(num)[-1] == "%"):
            return float(num[:-1]) / 100
        else:
            return float(num)

    def clear_orders(self):
        try:
            self.api.cancel_all_orders()
            print("All open orders cancelled.")
        except Exception as e:
            print(f"Error: {str(e)}")

    def add_items(self, data):
        ''' Expects a list of lists containing two items: symbol and position qty/pct

        '''
        for row in data:
            self.r_positions[row[0]] = [row[1], 0]

    def percent_rebalance(self, order_style, timeout=60):
        print(f"Desired positions: ")
        for sym in self.r_positions:
            print(f"{sym} - {self.r_positions.get(sym)[0]} of portfolio.")
        print()

        positions = self.api.list_positions()
        account = self.api.get_account()
        portfolio_val = float(account.portfolio_value)
        for sym in self.r_positions:
            price = self.api.get_barset(sym, "minute", 1)[sym][0].c
            self.r_positions[sym][0] = int(
                self.format_percent(
                    self.r_positions.get(sym)[0]) * portfolio_val / price)

        print(f"Current positions: ")
        for position in positions:
            print(
                f"{position.symbol} - {round(float(position.market_value) / portfolio_val * 100, 2)}% of portfolio.")
        print()

        self.clear_orders()

        print("Clearing extraneous positions.")
        for position in positions:
            if(self.r_positions.get(position.symbol)):
                self.r_positions.get(position.symbol)[1] = int(position.qty)
            else:
                self.send_basic_order(
                    position.symbol, position.qty, ("buy", "sell")[
                        position.side == "long"])
        print()

        if(order_style == "send"):
            for sym in self.r_positions:
                qty = self.r_positions.get(
                    sym)[0] - self.r_positions.get(sym)[1]
                self.send_basic_order(sym, qty, ("buy", "sell")[qty < 0])
        elif(order_style == "timeout"):
            threads = []
            for i, sym in enumerate(self.r_positions):
                qty = self.r_positions.get(
                    sym)[0] - self.r_positions.get(sym)[1]
                threads.append(
                    threading.Thread(
                        target=self.timeout_execution, args=(
                            sym, qty, ("buy", "sell")[
                                qty < 0], self.r_positions.get(sym)[0], timeout)))
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()
        elif(order_style == "block"):
            threads = []
            for i, sym in enumerate(self.r_positions):
                qty = self.r_positions.get(
                    sym)[0] - self.r_positions.get(sym)[1]
                threads.append(
                    threading.Thread(
                        target=self.confirm_full_execution, args=(
                            sym, qty, ("buy", "sell")[
                                qty < 0], self.r_positions.get(sym)[0])))
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()

    def rebalance(self, order_style, timeout=60):
        print(f"Desired positions: ")
        for sym in self.r_positions:
            print(f"{sym} - {self.r_positions.get(sym)[0]} shares.")
        print("\n")

        positions = self.api.list_positions()

        print(f"Current positions: ")
        for position in positions:
            print(f"{position.symbol} - {position.qty} shares owned.")
        print()

        self.clear_orders()

        print("Clearing extraneous positions.")
        for position in positions:
            if(self.r_positions.get(position.symbol)):
                self.r_positions[position.symbol][1] = int(position.qty)
            else:
                self.send_basic_order(
                    position.symbol, position.qty, ("buy", "sell")[
                        position.side == "long"])
        print()

        if(order_style == "send"):
            for sym in self.r_positions:
                qty = int(self.r_positions.get(sym)[
                          0]) - self.r_positions.get(sym)[1]
                self.send_basic_order(sym, qty, ("buy", "sell")[qty < 0])
        elif(order_style == "timeout"):
            threads = []
            for i, sym in enumerate(self.r_positions):
                qty = int(self.r_positions.get(sym)[
                          0]) - self.r_positions.get(sym)[1]
                threads.append(
                    threading.Thread(
                        target=self.timeout_execution, args=(
                            sym, qty, ("buy", "sell")[
                                qty < 0], self.r_positions.get(sym)[0], timeout)))
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()
        elif(order_style == "block"):
            threads = []
            for i, sym in enumerate(self.r_positions):
                qty = int(self.r_positions.get(sym)[
                          0]) - self.r_positions.get(sym)[1]
                threads.append(
                    threading.Thread(
                        target=self.confirm_full_execution, args=(
                            sym, qty, ("buy", "sell")[
                                qty < 0], self.r_positions.get(sym)[0])))
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()

    def send_basic_order(self, sym, qty, side):
        qty = int(qty)
        if(qty == 0):
            return
        q2 = 0
        try:
            position = self.api.get_position(sym)
            curr_pos = int(position.qty)
            if((curr_pos + qty > 0) != (curr_pos > 0)):
                q2 = curr_pos
                qty = curr_pos + qty
        except BaseException:
            pass
        try:
            if q2 != 0:
                self.api.submit_order(sym, abs(q2), side, "market", "gtc")
                try:
                    self.api.submit_order(sym, abs(qty), side, "market", "gtc")
                except Exception as e:
                    print(
                        f"Error: {str(e)}. Order of | {abs(qty) + abs(q2)} {sym} {side} | partially sent ({abs(q2)} shares sent).")
                    return False
            else:
                self.api.submit_order(sym, abs(qty), side, "market", "gtc")
            print(f"Order of | {abs(qty) + abs(q2)} {sym} {side} | submitted.")
            return True
        except Exception as e:
            print(
                f"Error: {str(e)}. Order of | {abs(qty) + abs(q2)} {sym} {side} | not sent.")
            return False

    def confirm_full_execution(self, sym, qty, side, expected_qty):
        sent = self.send_basic_order(sym, qty, side)
        if(not sent):
            return

        executed = False
        while(not executed):
            try:
                position = self.api.get_position(sym)
                if int(position.qty) == int(expected_qty):
                    executed = True
                else:
                    print(f"Waiting on execution for {sym}...")
                    time.sleep(20)
            except BaseException:
                print(f"Waiting on execution for {sym}...")
                time.sleep(20)
        print(
            f"Order of | {abs(qty)} {sym} {side} | completed.  Position is now {expected_qty} {sym}.")

    def timeout_execution(self, sym, qty, side, expected_qty, timeout):
        sent = self.send_basic_order(sym, qty, side)
        if(not sent):
            return
        output = []
        executed = False
        timer = threading.Thread(
            target=self.set_timeout, args=(
                timeout, output))
        timer.start()
        while(not executed):
            if(len(output) == 0):
                try:
                    position = self.api.get_position(sym)
                    if int(position.qty) == int(expected_qty):
                        executed = True
                    else:
                        print(f"Waiting on execution for {sym}...")
                        time.sleep(20)
                except BaseException:
                    print(f"Waiting on execution for {sym}...")
                    time.sleep(20)
            else:
                timer.join()
                try:
                    position = self.api.get_position(sym)
                    curr_qty = position.qty
                except BaseException:
                    curr_qty = 0
                print(
                    f"Process timeout at {timeout} seconds: order of | {abs(qty)} {sym} {side} | not completed. Position is currently {curr_qty} {sym}.")
                return
        print(
            f"Order of | {abs(qty)} {sym} {side} | completed.  Position is now {expected_qty} {sym}.")

    def set_timeout(self, timeout, output):
        time.sleep(timeout)
        output.append(True)
