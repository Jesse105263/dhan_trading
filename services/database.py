import psycopg

from services.config import POSTGRES


def get_connection():
    return psycopg.connect(**POSTGRES)

def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS instruments(
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(30) UNIQUE NOT NULL,
        exchange VARCHAR(20),
        security_id VARCHAR(30),
        instrument_type VARCHAR(20),
        lot_size INTEGER,
        tick_size DOUBLE PRECISION,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS underlying_quotes(
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(30) NOT NULL,
        spot_price DOUBLE PRECISION,
        volume BIGINT,
        oi BIGINT,
        timestamp TIMESTAMP NOT NULL
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_underlying_symbol_time
    ON underlying_quotes(symbol, timestamp DESC);
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS option_quotes(
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(30) NOT NULL,
        expiry DATE,
        strike DOUBLE PRECISION,
        option_type VARCHAR(5),
        ltp DOUBLE PRECISION,
        iv DOUBLE PRECISION,
        oi BIGINT,
        volume BIGINT,
        timestamp TIMESTAMP NOT NULL
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_option_symbol_expiry
    ON option_quotes(symbol, expiry);
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trade_signals(
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(30),
        signal VARCHAR(30),
        confidence DOUBLE PRECISION,
        score DOUBLE PRECISION,
        strike DOUBLE PRECISION,
        premium DOUBLE PRECISION,
        stop_loss DOUBLE PRECISION,
        target1 DOUBLE PRECISION,
        target2 DOUBLE PRECISION,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scanner_snapshots(
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(30),
        rank_score DOUBLE PRECISION,
        trade_score DOUBLE PRECISION,
        nearby_pcr DOUBLE PRECISION,
        atm_iv DOUBLE PRECISION,
        total_oi BIGINT,
        call_wall DOUBLE PRECISION,
        put_wall DOUBLE PRECISION,
        snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database initialized")

if __name__ == "__main__":
    initialize_database()