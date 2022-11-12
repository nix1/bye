class Position:
    def __init__(self, option, quantity, cost):
        self.option = option
        self.quantity = quantity  # positive for long, negative for short
        self.cost = cost
        self.close_value = None
        self.closed_at = None

    def is_expired(self, date):
        return self.option.is_expired(date)

    def is_expiring(self, date):
        return self.option.is_expiring(date)

    def close(self, date, close_value):
        self.close_value = close_value
        self.closed_at = date


class Wallet:
    def __init__(self, cash=0):
        self.cash = cash
        self.positions = []

    def add_position(self, position, update_cash=True):
        if update_cash:
            self.cash -= position.quantity * position.cost
        self.positions.append(position)

    def get_expired_positions(self, date):
        return [p for p in self.positions if p.is_expired(date)]

    def get_expiring_positions(self, date):
        return [p for p in self.positions if p.is_expiring(date)]

    def get_open_positions(self, date):
        return [p for p in self.positions if not p.is_expired(date)]
