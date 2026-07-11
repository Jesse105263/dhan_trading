import unittest
from datetime import date
from decimal import Decimal

from services.derivative_contract_repository import DerivativeContract


class DerivativeContractTest(unittest.TestCase):
    def test_normalizes_option_contract(self) -> None:
        contract = DerivativeContract(
            exchange=" nse ",
            segment=" nse_fno ",
            security_id=" 12345 ",
            trading_symbol=" reliance-jul-ce ",
            underlying_symbol=" reliance ",
            instrument_type=" optstk ",
            expiry=date(2026, 7, 30),
            strike=Decimal("3000"),
            option_type=" ce ",
            lot_size=250,
            tick_size=Decimal("0.05"),
        ).normalized()

        self.assertEqual(contract.exchange, "NSE")
        self.assertEqual(contract.segment, "NSE_FNO")
        self.assertEqual(contract.security_id, "12345")
        self.assertEqual(contract.trading_symbol, "RELIANCE-JUL-CE")
        self.assertEqual(contract.underlying_symbol, "RELIANCE")
        self.assertEqual(contract.instrument_type, "OPTSTK")
        self.assertEqual(contract.option_type, "CE")
        self.assertEqual(contract.strike, Decimal("3000"))

    def test_rejects_option_without_strike(self) -> None:
        with self.assertRaisesRegex(ValueError, "require strike"):
            DerivativeContract(
                exchange="NSE",
                segment="NSE_FNO",
                security_id="12345",
                trading_symbol="RELIANCE-CE",
                underlying_symbol="RELIANCE",
                instrument_type="OPTSTK",
                expiry=date(2026, 7, 30),
                option_type="CE",
                lot_size=250,
                tick_size=Decimal("0.05"),
            ).normalized()

    def test_rejects_future_with_option_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot have strike"):
            DerivativeContract(
                exchange="NSE",
                segment="NSE_FNO",
                security_id="12346",
                trading_symbol="RELIANCE-FUT",
                underlying_symbol="RELIANCE",
                instrument_type="FUTSTK",
                expiry=date(2026, 7, 30),
                strike=Decimal("3000"),
                option_type="CE",
                lot_size=250,
                tick_size=Decimal("0.05"),
            ).normalized()

    def test_rejects_invalid_option_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "CE or PE"):
            DerivativeContract(
                exchange="NSE",
                segment="NSE_FNO",
                security_id="12347",
                trading_symbol="RELIANCE-XE",
                underlying_symbol="RELIANCE",
                instrument_type="OPTSTK",
                expiry=date(2026, 7, 30),
                strike=Decimal("3000"),
                option_type="XE",
                lot_size=250,
                tick_size=Decimal("0.05"),
            ).normalized()

    def test_rejects_non_positive_lot_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "lot_size"):
            DerivativeContract(
                exchange="NSE",
                segment="NSE_FNO",
                security_id="12348",
                trading_symbol="RELIANCE-FUT",
                underlying_symbol="RELIANCE",
                instrument_type="FUTSTK",
                expiry=date(2026, 7, 30),
                lot_size=0,
                tick_size=Decimal("0.05"),
            ).normalized()


if __name__ == "__main__":
    unittest.main()
