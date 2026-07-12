from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import uuid4

from services.dhan_option_chain_client import DhanOptionChainClient
from services.error_sanitizer import sanitize_error_message
from services.expiry_service import ExpiryService
from services.option_chain_models import (
    NormalizedOptionChain,
    OptionChainCollectionRequest,
    OptionChainCollectionResult,
    OptionQuoteSnapshot,
)
from services.option_chain_repository import OptionChainRepository


class OptionChainValidationError(ValueError):
    pass


class OptionChainCollector:
    def __init__(
        self,
        repository: OptionChainRepository,
        expiry_service: ExpiryService,
        client: DhanOptionChainClient,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.repository = repository
        self.expiry_service = expiry_service
        self.client = client
        self.clock = clock

    def collect(
        self,
        request: OptionChainCollectionRequest,
        as_of_date: date | None = None,
    ) -> OptionChainCollectionResult:
        normalized_request = request.normalized()
        reference_date = as_of_date or date.today()
        identity = self.repository.resolve_underlying(
            normalized_request.underlying_symbol
        )

        if normalized_request.expiry is not None:
            expiry = self.expiry_service.validate(
                identity.symbol,
                normalized_request.expiry,
                as_of_date=reference_date,
            )
        else:
            expiry = self.expiry_service.select_nearest(
                identity.symbol,
                as_of_date=reference_date,
                minimum_days_to_expiry=(
                    normalized_request.minimum_days_to_expiry
                ),
                maximum_days_to_expiry=(
                    normalized_request.maximum_days_to_expiry
                ),
            )

        run_id = uuid4()
        requested_at = self.clock()
        self.repository.start_run(
            run_id,
            identity,
            expiry,
            requested_at,
        )

        try:
            payload = self.client.fetch(
                underlying_security_id=identity.security_id,
                underlying_segment=identity.segment,
                expiry=expiry.isoformat(),
            )
            chain = self.normalize_response(
                payload=payload,
                underlying_symbol=identity.symbol,
                expiry=expiry,
                captured_at=self.clock(),
            )
            inserted = self.repository.complete_run_with_quotes(
                run_id=run_id,
                completed_at=self.clock(),
                spot_price=chain.spot_price,
                quotes=chain.quotes,
            )
        except Exception as error:
            self.repository.fail_run(
                run_id=run_id,
                completed_at=self.clock(),
                error_message=sanitize_error_message(str(error)),
            )
            raise

        return OptionChainCollectionResult(
            run_id=run_id,
            underlying_symbol=identity.symbol,
            underlying_security_id=identity.security_id,
            expiry=expiry,
            spot_price=chain.spot_price,
            strikes_received=chain.strike_count,
            quotes_received=len(chain.quotes),
            quotes_inserted=inserted,
        )

    @staticmethod
    def normalize_response(
        payload: dict[str, Any],
        underlying_symbol: str,
        expiry: date,
        captured_at: datetime,
    ) -> NormalizedOptionChain:
        data: Any = payload.get("data", payload)
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            data = data["data"]
        if not isinstance(data, dict):
            raise OptionChainValidationError(
                "Option-chain response data must be an object."
            )

        raw_chain = (
            data.get("oc")
            or data.get("option_chain")
            or data.get("optionChain")
        )
        if not isinstance(raw_chain, dict) or not raw_chain:
            raise OptionChainValidationError(
                "Option-chain response contains no strikes."
            )

        quotes: list[OptionQuoteSnapshot] = []
        missing_sides: list[str] = []
        for raw_strike, item in raw_chain.items():
            if not isinstance(item, dict):
                raise OptionChainValidationError(
                    f"Strike {raw_strike} must contain an object."
                )
            strike = OptionChainCollector._decimal(
                raw_strike,
                "strike",
                required=False,
            ) or OptionChainCollector._decimal(
                item.get("strike_price") or item.get("strikePrice"),
                "strike",
                required=True,
            )

            side_values = {
                "CE": item.get("ce") or item.get("CE"),
                "PE": item.get("pe") or item.get("PE"),
            }
            for option_type, side in side_values.items():
                if not isinstance(side, dict) or not side:
                    missing_sides.append(
                        f"{strike}:{option_type}"
                    )
                    continue
                quotes.append(
                    OptionChainCollector._normalize_quote(
                        side=side,
                        underlying_symbol=underlying_symbol,
                        expiry=expiry,
                        strike=strike,
                        option_type=option_type,
                        captured_at=captured_at,
                    )
                )

        if missing_sides:
            raise OptionChainValidationError(
                "Option-chain response is incomplete; missing sides: "
                + ", ".join(missing_sides[:10])
            )
        if not quotes:
            raise OptionChainValidationError(
                "Option-chain response contains no valid quotes."
            )

        return NormalizedOptionChain(
            spot_price=OptionChainCollector._decimal(
                data.get("last_price")
                or data.get("ltp")
                or data.get("underlying_value")
                or data.get("spot"),
                "spot_price",
                required=False,
            ),
            quotes=tuple(quotes),
        )

    @staticmethod
    def _normalize_quote(
        side: dict[str, Any],
        underlying_symbol: str,
        expiry: date,
        strike: Decimal,
        option_type: str,
        captured_at: datetime,
    ) -> OptionQuoteSnapshot:
        return OptionQuoteSnapshot(
            underlying_symbol=underlying_symbol,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            security_id=OptionChainCollector._text(
                side.get("security_id") or side.get("securityId")
            ),
            last_price=OptionChainCollector._decimal(
                side.get("last_price")
                or side.get("ltp")
                or side.get("last_traded_price"),
                "last_price",
                required=False,
            ),
            implied_volatility=OptionChainCollector._decimal(
                side.get("implied_volatility")
                or side.get("iv")
                or side.get("IV"),
                "implied_volatility",
                required=False,
            ),
            open_interest=OptionChainCollector._integer(
                side.get("oi")
                or side.get("open_interest")
                or side.get("openInterest"),
                "open_interest",
            ),
            volume=OptionChainCollector._integer(
                side.get("volume"),
                "volume",
            ),
            bid_price=OptionChainCollector._decimal(
                side.get("top_bid_price")
                or side.get("bid_price")
                or side.get("bidPrice"),
                "bid_price",
                required=False,
            ),
            ask_price=OptionChainCollector._decimal(
                side.get("top_ask_price")
                or side.get("ask_price")
                or side.get("askPrice"),
                "ask_price",
                required=False,
            ),
            captured_at=captured_at,
        )

    @staticmethod
    def _decimal(
        value: Any,
        field_name: str,
        required: bool,
    ) -> Decimal | None:
        if value is None or value == "":
            if required:
                raise OptionChainValidationError(
                    f"{field_name} is required."
                )
            return None
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise OptionChainValidationError(
                f"{field_name} must be numeric."
            ) from None
        if number < 0:
            raise OptionChainValidationError(
                f"{field_name} cannot be negative."
            )
        return number

    @staticmethod
    def _integer(value: Any, field_name: str) -> int | None:
        if value is None or value == "":
            return None
        try:
            number = int(Decimal(str(value)))
        except (InvalidOperation, ValueError):
            raise OptionChainValidationError(
                f"{field_name} must be numeric."
            ) from None
        if number < 0:
            raise OptionChainValidationError(
                f"{field_name} cannot be negative."
            )
        return number

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
