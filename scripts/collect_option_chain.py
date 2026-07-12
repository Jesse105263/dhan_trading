import argparse
from datetime import date

from services.dhan_option_chain_client import DhanOptionChainClient
from services.expiry_repository import ExpiryRepository
from services.expiry_service import ExpiryService
from services.option_chain_collector import OptionChainCollector
from services.option_chain_models import OptionChainCollectionRequest
from services.option_chain_repository import OptionChainRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect and persist one Dhan option chain."
    )
    parser.add_argument("symbol")
    parser.add_argument("--expiry", type=date.fromisoformat)
    parser.add_argument("--minimum-days", type=int, default=0)
    parser.add_argument("--maximum-days", type=int)
    args = parser.parse_args()

    collector = OptionChainCollector(
        repository=OptionChainRepository(),
        expiry_service=ExpiryService(ExpiryRepository()),
        client=DhanOptionChainClient(),
    )
    result = collector.collect(
        OptionChainCollectionRequest(
            underlying_symbol=args.symbol,
            expiry=args.expiry,
            minimum_days_to_expiry=args.minimum_days,
            maximum_days_to_expiry=args.maximum_days,
        )
    )

    print("Option-chain collection completed")
    print(f"Run ID: {result.run_id}")
    print(f"Underlying: {result.underlying_symbol}")
    print(f"Security ID: {result.underlying_security_id}")
    print(f"Expiry: {result.expiry}")
    print(f"Spot price: {result.spot_price}")
    print(f"Strikes received: {result.strikes_received}")
    print(f"Quotes received: {result.quotes_received}")
    print(f"Quotes inserted: {result.quotes_inserted}")


if __name__ == "__main__":
    main()
