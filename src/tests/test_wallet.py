import pandas as pd
from pytest import fixture

from src.options import Put
from src.wallet import Wallet, Position


@fixture
def sample_put():
    """Create a sample Put option"""
    return Put(strike=100, expiration=pd.to_datetime("2020-01-08"))


@fixture
def sample_position(sample_put):
    """Create a sample short position"""
    return Position(option=sample_put, quantity=-1, cost=2.0)


class TestPosition:
    """Test the Position class"""

    def test_position_init(self, sample_put):
        """Test Position initialization"""
        position = Position(option=sample_put, quantity=-1, cost=2.0)
        assert position.option == sample_put
        assert position.quantity == -1
        assert position.cost == 2.0
        assert position.close_value is None
        assert position.closed_at is None

    def test_position_long(self, sample_put):
        """Test long position has positive quantity"""
        position = Position(option=sample_put, quantity=1, cost=2.0)
        assert position.quantity == 1

    def test_position_short(self, sample_put):
        """Test short position has negative quantity"""
        position = Position(option=sample_put, quantity=-1, cost=2.0)
        assert position.quantity == -1

    def test_position_is_expired(self, sample_position):
        """Test is_expired method"""
        assert sample_position.is_expired(pd.to_datetime("2020-01-09")) is True
        assert sample_position.is_expired(pd.to_datetime("2020-01-08")) is False
        assert sample_position.is_expired(pd.to_datetime("2020-01-07")) is False

    def test_position_is_expiring(self, sample_position):
        """Test is_expiring method"""
        assert sample_position.is_expiring(pd.to_datetime("2020-01-08")) is True
        assert sample_position.is_expiring(pd.to_datetime("2020-01-07")) is False
        assert sample_position.is_expiring(pd.to_datetime("2020-01-09")) is False

    def test_position_close(self, sample_position):
        """Test closing a position"""
        close_date = pd.to_datetime("2020-01-07")
        close_value = -1.5
        sample_position.close(close_date, close_value)
        assert sample_position.close_value == -1.5
        assert sample_position.closed_at == close_date

    def test_position_repr(self, sample_position):
        """Test Position string representation"""
        repr_str = repr(sample_position)
        assert "Position" in repr_str
        assert "Put(100" in repr_str
        assert "-1" in repr_str
        assert "2.0" in repr_str


class TestWallet:
    """Test the Wallet class"""

    def test_wallet_init_with_zero(self):
        """Test Wallet initialization with zero cash"""
        wallet = Wallet(0)
        assert wallet.cash == 0
        assert wallet.positions == []

    def test_wallet_init_with_cash(self):
        """Test Wallet initialization with starting cash"""
        wallet = Wallet(1000)
        assert wallet.cash == 1000
        assert wallet.positions == []

    def test_wallet_add_position_updates_cash(self, sample_position):
        """Test adding position updates cash when update_cash=True"""
        wallet = Wallet(1000)
        wallet.add_position(sample_position, update_cash=True)
        # For short position: cash -= (-1) * 2.0 = cash += 2.0
        assert wallet.cash == 1002.0
        assert len(wallet.positions) == 1

    def test_wallet_add_position_no_cash_update(self, sample_position):
        """Test adding position without updating cash"""
        wallet = Wallet(1000)
        wallet.add_position(sample_position, update_cash=False)
        assert wallet.cash == 1000
        assert len(wallet.positions) == 1

    def test_wallet_add_long_position(self, sample_put):
        """Test adding a long position decreases cash"""
        wallet = Wallet(1000)
        long_position = Position(option=sample_put, quantity=1, cost=2.0)
        wallet.add_position(long_position, update_cash=True)
        # For long position: cash -= 1 * 2.0 = 998
        assert wallet.cash == 998.0

    def test_wallet_add_multiple_positions(self, sample_put):
        """Test adding multiple positions"""
        wallet = Wallet(1000)
        pos1 = Position(option=sample_put, quantity=-1, cost=2.0)
        pos2 = Position(option=sample_put, quantity=-1, cost=3.0)
        wallet.add_position(pos1, update_cash=True)
        wallet.add_position(pos2, update_cash=True)
        assert wallet.cash == 1005.0  # 1000 + 2 + 3
        assert len(wallet.positions) == 2

    def test_wallet_get_expired_positions(self, sample_put):
        """Test getting expired positions"""
        wallet = Wallet(0)
        pos1 = Position(option=sample_put, quantity=-1, cost=2.0)
        pos2_put = Put(strike=105, expiration=pd.to_datetime("2020-01-15"))
        pos2 = Position(option=pos2_put, quantity=-1, cost=3.0)
        wallet.add_position(pos1, update_cash=False)
        wallet.add_position(pos2, update_cash=False)

        # On 2020-01-10, first position is expired, second is not
        expired = wallet.get_expired_positions(pd.to_datetime("2020-01-10"))
        assert len(expired) == 1
        assert expired[0].option.expiration == pd.to_datetime("2020-01-08")

    def test_wallet_get_expiring_positions(self, sample_put):
        """Test getting expiring positions"""
        wallet = Wallet(0)
        pos1 = Position(option=sample_put, quantity=-1, cost=2.0)
        pos2_put = Put(strike=105, expiration=pd.to_datetime("2020-01-15"))
        pos2 = Position(option=pos2_put, quantity=-1, cost=3.0)
        wallet.add_position(pos1, update_cash=False)
        wallet.add_position(pos2, update_cash=False)

        # On 2020-01-08, first position is expiring
        expiring = wallet.get_expiring_positions(pd.to_datetime("2020-01-08"))
        assert len(expiring) == 1
        assert expiring[0].option.expiration == pd.to_datetime("2020-01-08")

    def test_wallet_get_open_positions(self, sample_put):
        """Test getting open (not expired) positions"""
        wallet = Wallet(0)
        pos1 = Position(option=sample_put, quantity=-1, cost=2.0)
        pos2_put = Put(strike=105, expiration=pd.to_datetime("2020-01-15"))
        pos2 = Position(option=pos2_put, quantity=-1, cost=3.0)
        wallet.add_position(pos1, update_cash=False)
        wallet.add_position(pos2, update_cash=False)

        # On 2020-01-10, only second position is still open
        open_pos = wallet.get_open_positions(pd.to_datetime("2020-01-10"))
        assert len(open_pos) == 1
        assert open_pos[0].option.expiration == pd.to_datetime("2020-01-15")

    def test_wallet_get_open_positions_all_open(self, sample_put):
        """Test getting open positions when all are open"""
        wallet = Wallet(0)
        pos1 = Position(option=sample_put, quantity=-1, cost=2.0)
        pos2_put = Put(strike=105, expiration=pd.to_datetime("2020-01-15"))
        pos2 = Position(option=pos2_put, quantity=-1, cost=3.0)
        wallet.add_position(pos1, update_cash=False)
        wallet.add_position(pos2, update_cash=False)

        # On 2020-01-05, both positions are still open
        open_pos = wallet.get_open_positions(pd.to_datetime("2020-01-05"))
        assert len(open_pos) == 2
