import argparse
from services.news_event_service import NewsEventService
def main():
    parser=argparse.ArgumentParser(description="Attach context-only persisted events to trade opportunities."); parser.add_argument("--limit",type=int,default=1000)
    result=NewsEventService().link_opportunities(parser.parse_args().limit)
    print(f"Opportunity event context materialized | opportunities={result['opportunity_count']} links={result['link_count']}"); return 0
if __name__=="__main__": raise SystemExit(main())
