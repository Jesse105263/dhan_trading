from services.database import get_connection


def save_underlying_quote(
    symbol,
    spot_price,
    volume,
    oi,
    timestamp,
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO underlying_quotes
        (
            symbol,
            spot_price,
            volume,
            oi,
            timestamp
        )
        VALUES
        (%s,%s,%s,%s,%s)
        """,
        (
            symbol,
            spot_price,
            volume,
            oi,
            timestamp,
        ),
    )

    conn.commit()

    cur.close()
    conn.close()

    print(f"Saved {symbol}")