import argparse,json
from datetime import datetime
from services.v3_scale_repository import V3ScaleRepository


def main(argv=None):
    p=argparse.ArgumentParser(description="SELECT-only V3 operational health");p.parse_args(argv)
    print(json.dumps(V3ScaleRepository().health(datetime.now()),sort_keys=True,default=str));return 0
if __name__=="__main__":raise SystemExit(main())
