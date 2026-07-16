import json
from datetime import datetime
from services.database import get_connection


def main():
    with get_connection() as c:
        with c.cursor() as q:q.execute("SELECT current_database(),pg_database_size(current_database()),MAX(applied_at),COUNT(*) FROM schema_migrations");name,size,latest,count=q.fetchone()
    print(json.dumps({"database":name,"database_size_bytes":size,"migration_count":count,"latest_migration_at":latest,"checked_at":datetime.now(),"restore_executed":False},default=str,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
