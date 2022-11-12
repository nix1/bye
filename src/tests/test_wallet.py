from src.wallet import Wallet


class TestWallet:
    def test_instance(self):
        wallet = Wallet(0)
        assert wallet.cash == 0
        assert wallet.positions == []
