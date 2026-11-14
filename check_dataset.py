
import csv
from pathlib import Path

file_path = Path(
    r"C:\Users\Acer\Downloads\swift_umdac_datathon_2026_fictitious_payment_data.csv"
)

total_records = 0

with open(
    file_path,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    reader = csv.reader(f)

    header = next(reader)

    for row in reader:
        total_records += 1

print("Columns:", len(header))
print("Header:", header)
print("Actual data records:", f"{total_records:,}")
print("Total including header:", f"{total_records + 1:,}")
print("File size (GB):", round(file_path.stat().st_size / (1024**3), 3))
