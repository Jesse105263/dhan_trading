import argparse
from services.news_event_service import NewsEventService
def main():
    parser=argparse.ArgumentParser(description="Link persisted events to historical vectors without future leakage."); parser.add_argument("--limit",type=int,default=5000)
    result=NewsEventService().link_historical(parser.parse_args().limit)
    print(f"Historical event context linked | vectors={result['vector_count']} links={result['link_count']} similarity_links={result['similarity_link_count']}"); return 0
if __name__=="__main__": raise SystemExit(main())
