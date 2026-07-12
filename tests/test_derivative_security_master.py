import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from services.derivative_security_master import (
    DerivativeSecurityMasterParser,
)


FIELDNAMES = [
    "EXCH_ID",
    "SEGMENT",
    "SECURITY_ID",
    "INSTRUMENT",
    "UNDERLYING_SYMBOL",
    "SYMBOL_NAME",
    "LOT_SIZE",
    "SM_EXPIRY_DATE",
    "STRIKE_PRICE",
    "OPTION_TYPE",
    "TICK_SIZE",
]


class DerivativeSecurityMasterParserTest(unittest.TestCase):
    def test_parses_supported_future_and_option(self) -> None:
        path = self._write_rows(
            [
                self._row(
                    security_id="101",
                    instrument="FUTSTK",
                    symbol="ABC-Jul2026-FUT",
                    strike="",
                    option_type="",
                ),
                self._row(
                    security_id="102",
                    instrument="OPTSTK",
                    symbol="ABC-Jul2026-100-CE",
                    strike="100",
                    option_type="CE",
                ),
            ]
        )

        result = DerivativeSecurityMasterParser(
            supported_underlyings={"ABC"},
            as_of_date=date(2026, 7, 1),
        ).parse(path)

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_eligible, 2)
        self.assertEqual(len(result.contracts), 2)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(result.contracts[0].segment, "NSE_FNO")

    def test_ignores_unsupported_and_expired_rows(self) -> None:
        path = self._write_rows(
            [
                self._row(underlying="OTHER"),
                self._row(expiry="2026-06-30"),
            ]
        )

        result = DerivativeSecurityMasterParser(
            supported_underlyings={"ABC"},
            as_of_date=date(2026, 7, 1),
        ).parse(path)

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_eligible, 0)
        self.assertEqual(len(result.contracts), 0)
        self.assertEqual(len(result.failures), 0)

    def test_applies_symbol_alias(self) -> None:
        path = self._write_rows(
            [self._row(underlying="ABCOLD")]
        )

        result = DerivativeSecurityMasterParser(
            supported_underlyings={"ABC"},
            symbol_aliases={"ABCOLD": "ABC"},
            as_of_date=date(2026, 7, 1),
        ).parse(path)

        self.assertEqual(len(result.contracts), 1)
        self.assertEqual(
            result.contracts[0].underlying_symbol,
            "ABC",
        )

    def test_isolates_invalid_supported_row(self) -> None:
        path = self._write_rows(
            [self._row(lot_size="bad")]
        )

        result = DerivativeSecurityMasterParser(
            supported_underlyings={"ABC"},
            as_of_date=date(2026, 7, 1),
        ).parse(path)

        self.assertEqual(result.rows_eligible, 1)
        self.assertEqual(len(result.contracts), 0)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0][1], "100")

    def test_rejects_missing_required_columns(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            newline="",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["SECURITY_ID"],
            )
            writer.writeheader()
            path = Path(handle.name)

        self.addCleanup(path.unlink, missing_ok=True)

        with self.assertRaisesRegex(
            RuntimeError,
            "missing required columns",
        ):
            DerivativeSecurityMasterParser(
                supported_underlyings={"ABC"}
            ).parse(path)

    def _write_rows(self, rows: list[dict[str, str]]) -> Path:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            newline="",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
            path = Path(handle.name)

        self.addCleanup(path.unlink, missing_ok=True)
        return path

    @staticmethod
    def _row(
        security_id: str = "100",
        underlying: str = "ABC",
        instrument: str = "OPTSTK",
        symbol: str = "ABC-Jul2026-100-CE",
        expiry: str = "2026-07-30",
        strike: str = "100",
        option_type: str = "CE",
        lot_size: str = "25.0",
    ) -> dict[str, str]:
        return {
            "EXCH_ID": "NSE",
            "SEGMENT": "D",
            "SECURITY_ID": security_id,
            "INSTRUMENT": instrument,
            "UNDERLYING_SYMBOL": underlying,
            "SYMBOL_NAME": symbol,
            "LOT_SIZE": lot_size,
            "SM_EXPIRY_DATE": expiry,
            "STRIKE_PRICE": strike,
            "OPTION_TYPE": option_type,
            "TICK_SIZE": "0.05",
        }


if __name__ == "__main__":
    unittest.main()
