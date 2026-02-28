import csv
import io


def load_ohlc_from_csv_string(csv_string: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_string))
    return [
        {
            "timestamp": row["timestamp"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        }
        for row in reader
    ]
