import pandas as pd

from src.options import Put


class TestPut:
    """Test the Put option class"""

    def test_put_init(self):
        """Test Put initialization"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.strike == 100
        assert put.expiration == pd.to_datetime("2020-01-08")

    def test_put_is_itm_when_underlying_below_strike(self):
        """Test that Put is ITM when underlying is below strike"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.is_itm(99) is True
        assert put.is_itm(95) is True
        assert put.is_itm(50) is True

    def test_put_is_otm_when_underlying_above_strike(self):
        """Test that Put is OTM when underlying is above strike"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.is_itm(101) is False
        assert put.is_itm(105) is False
        assert put.is_itm(150) is False

    def test_put_is_atm_when_underlying_equals_strike(self):
        """Test that Put is OTM when underlying equals strike"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.is_itm(100) is False

    def test_put_is_expiring(self):
        """Test is_expiring method"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.is_expiring(pd.to_datetime("2020-01-08")) is True
        assert put.is_expiring(pd.to_datetime("2020-01-07")) is False
        assert put.is_expiring(pd.to_datetime("2020-01-09")) is False

    def test_put_is_expired(self):
        """Test is_expired method"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.is_expired(pd.to_datetime("2020-01-09")) is True
        assert put.is_expired(pd.to_datetime("2020-01-10")) is True
        assert put.is_expired(pd.to_datetime("2020-01-08")) is False
        assert put.is_expired(pd.to_datetime("2020-01-07")) is False

    def test_put_intrinsic_value_when_itm(self):
        """Test intrinsic value when Put is ITM"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.intrinsic_value(95) == 5
        assert put.intrinsic_value(90) == 10
        assert put.intrinsic_value(99) == 1

    def test_put_intrinsic_value_when_otm(self):
        """Test intrinsic value when Put is OTM"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert put.intrinsic_value(105) == 0
        assert put.intrinsic_value(110) == 0
        assert put.intrinsic_value(100) == 0

    def test_put_repr(self):
        """Test Put string representation"""
        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        assert repr(put) == "Put(100, 2020-01-08 00:00:00)"
