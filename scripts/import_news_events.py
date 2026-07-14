import argparse
from pathlib import Path
from services.news_event_provider import LocalJsonEventProvider
from services.news_event_service import NewsEventService

def main():
    parser=argparse.ArgumentParser(description="Import bounded local event JSON without network access.")
    parser.add_argument("--file",type=Path,default=Path("fixtures/news_events.json")); parser.add_argument("--limit",type=int,default=500)
    arguments=parser.parse_args(); result=NewsEventService().import_records(LocalJsonEventProvider(arguments.file),arguments.limit)
    print(f"News events imported | sources={result['source_count']} events={result['imported_count']}"); return 0
if __name__=="__main__": raise SystemExit(main())
