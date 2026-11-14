
import pandas as pd
from pathlib import Path
from collections import Counter
from tqdm import tqdm
import json

# ==================================================
# CONFIGURATION
# ==================================================

INPUT_FILE = Path(
    r"C:\Users\Acer\Downloads\UMDAC\swift_umdac_datathon_2026_fictitious_payment_data.csv"
)

OUTPUT_DIR = Path(
    r"C:\Users\Acer\Downloads\UMDAC"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 50_000

CATEGORICAL_COLUMNS = [
    "DISCLAIMER",
    "CURRENCY_CODE",
    "CONTINUITY_QFLAG",
    "TRANSACTION_TYPE_CODE",
    "ORDERING_TYPE",
    "BENEFICIARY_TYPE",
    "ANOMALY_TYPE"
]

NUMERIC_COLUMNS = [
    "EPOCH_SECONDS",
    "USD_AMOUNT",
    "TOTAL_DURATION",
    "CURRENCY_CONVERSION_COUNT",
    "PARTICIPANT_COUNT"
]

# ==================================================
# INITIALISE
# ==================================================

category_counts = {
    col: Counter() for col in CATEGORICAL_COLUMNS
}

numeric_stats = {
    col: {
        "count": 0,
        "invalid": 0,
        "missing": 0,
        "sum": 0.0,
        "min": None,
        "max": None
    }
    for col in NUMERIC_COLUMNS
}

total_rows = 0

file_size = INPUT_FILE.stat().st_size

print("Starting full dataset profiling...")
print(f"File size: {file_size / (1024**3):.3f} GB")

# ==================================================
# PROCESS DATASET IN CHUNKS
# ==================================================

reader = pd.read_csv(
    INPUT_FILE,
    chunksize=CHUNK_SIZE,
    dtype=str,
    keep_default_na=False,
    encoding="utf-8-sig",
    on_bad_lines="error"
)

for chunk in tqdm(reader, desc="Processing dataset"):

    total_rows += len(chunk)

    # Categorical distributions
    for col in CATEGORICAL_COLUMNS:

        counts = chunk[col].value_counts(
            dropna=False
        )

        category_counts[col].update(
            counts.to_dict()
        )

    # Numeric statistics
    for col in NUMERIC_COLUMNS:

        raw = chunk[col].str.strip()

        missing = raw.eq("")

        values = pd.to_numeric(
            raw,
            errors="coerce"
        )

        invalid = values.isna() & ~missing
        valid = values.dropna()

        stats = numeric_stats[col]

        stats["missing"] += int(missing.sum())
        stats["invalid"] += int(invalid.sum())

        if len(valid) > 0:

            stats["count"] += len(valid)
            stats["sum"] += float(valid.sum())

            current_min = float(valid.min())
            current_max = float(valid.max())

            if stats["min"] is None:
                stats["min"] = current_min
                stats["max"] = current_max
            else:
                stats["min"] = min(
                    stats["min"], current_min
                )
                stats["max"] = max(
                    stats["max"], current_max
                )

# ==================================================
# GENERATE REPORT
# ==================================================

report = {
    "total_records": total_rows,
    "file_size_gb": round(
        file_size / (1024**3), 3
    ),
    "categorical_distributions": {},
    "numeric_statistics": {}
}

for col, counter in category_counts.items():

    report["categorical_distributions"][col] = {
        str(k): int(v)
        for k, v in counter.most_common(100)
    }

for col, stats in numeric_stats.items():

    count = stats["count"]

    report["numeric_statistics"][col] = {
        "count": count,
        "missing": stats["missing"],
        "invalid": stats["invalid"],
        "minimum": stats["min"],
        "maximum": stats["max"],
        "mean": (
            stats["sum"] / count
            if count else None
        )
    }

# Save report
output_file = OUTPUT_DIR / "full_dataset_profile.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4, ensure_ascii=False)

print("\n========== FULL DATASET PROFILE ==========")
print("Total records:", f"{total_rows:,}")

for col, counter in category_counts.items():

    print(f"\n{col}:")

    for value, count in counter.most_common(15):
        print(f"  {value!r}: {count:,}")

print("\nNumeric statistics:")

for col, stats in numeric_stats.items():

    count = stats["count"]

    mean = (
        stats["sum"] / count
        if count else 0
    )

    print(f"\n{col}")
    print("  Valid:", f"{count:,}")
    print("  Missing:", f"{stats['missing']:,}")
    print("  Invalid:", f"{stats['invalid']:,}")
    print("  Minimum:", stats["min"])
    print("  Maximum:", stats["max"])
    print("  Mean:", mean)

print("\nReport saved to:", output_file)
print("==========================================")

