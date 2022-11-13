from abc import abstractmethod


class Option:
    def __init__(self, strike, expiration):
        self.strike = strike
        self.expiration = expiration

    @abstractmethod
    def is_itm(self, underlying):
        pass

    def is_expiring(self, date):
        return date == self.expiration

    def is_expired(self, date):
        return date > self.expiration

    def intrinsic_value(self, underlying):
        if self.is_itm(underlying):
            # same for puts and calls
            # always positive, often needs to be multiplied by -1
            return abs(self.strike - underlying)
        else:
            return 0


class Put(Option):
    def is_itm(self, underlying):
        return underlying < self.strike

    def __repr__(self):
        return f"Put({self.strike}, {self.expiration})"


# class Call(Option):
#     def is_itm(self, underlying):
#         return underlying > self.strike
