import os
import json
import csv
import re

results_dir = "results"
output_csv = "aggregated_results.csv"

# Matches a CHF amount either before or after the "CHF" keyword, e.g. "3,250 CHF" or "CHF 3250"
AMOUNT_PATTERN = re.compile(r"[\d][\d,\.']*\s*CHF|CHF\s*[\d][\d,\.']*")

def clean_total_subsidy(raw):
    """Strip markdown noise and split the raw LLM answer into a short amount and full notes."""
    if not raw:
        return "", ""
    text = raw.replace("*", "").strip()
    match = AMOUNT_PATTERN.search(text)
    amount = match.group(0).strip() if match else text
    notes = text if text != amount else ""
    return amount, notes

# Prepare the CSV header
header = ["sub_id", "total_subsidy_10kW", "subsidy_type", "notes"]
rows = []

# Loop through all JSON files in the results directory
for filename in os.listdir(results_dir):
    if filename.endswith("_analysis.json"):
        filepath = os.path.join(results_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            sub_id = data.get("sub_id", "")
            total, notes = clean_total_subsidy(data.get("total_subsidy_10kW", ""))
            subsidy_type = data.get("subsidy_type", "")
            rows.append([sub_id, total, subsidy_type, notes])

# Write to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"✅ Aggregated results saved to {output_csv}")