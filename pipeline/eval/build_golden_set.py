"""
Build the golden set (ground truth) for evaluating the LLM subsidy extraction.

Inputs (all read from pipeline/eval/ unless a path is given):
- PV examples.xlsx, sheet 'exemples': OK Climat's hand-labelled examples (expected 10 kW amount)
- PV examples.xlsx, sheet 'all': list of subsidies processed by the pipeline (gives subv_id)
- manual_ids.csv: subv_id for example rows that could not be matched automatically
- ../../data/exp_subventions_20260317.xlsx: OK Climat database export (contributor info)
- row_flags.csv: our flags, evidence quotes and notes per subsidy
- corrections.csv: proposed changes to the expected amount after label review

Outputs:
- golden_set.csv: version 0, the labels as given by OK Climat
- golden_set_corrected.csv: the same rows with corrections.csv applied

Run from pipeline/eval/:
python build_golden_set.py --input_file '../PV examples.xlsx' --output_file 'golden_set.csv' --sub_types PV PV-EauCd
"""

import pandas as pd
import argparse
import os

def build_golden_set(input_file, output_file, sub_types):


	print(f"\nBuilding golden set from {input_file} to evaluate model\n")

	#------------------------------------------------------------
	# Left table: OK Climat's labelled examples ('exemples' sheet)

	# Define the sheet name
	excel_sheet_name = 'exemples'
	print(f"\nReading Excel sheet '{excel_sheet_name}' from {input_file}\n")

	# Read the 'exemples' sheet and keep only the requested subsidy types
	df_exemples = pd.read_excel(input_file, sheet_name=excel_sheet_name)
	mask = df_exemples['type_subv'].isin(sub_types)
	df_exemples_filtered = df_exemples[mask]
	print(f"\nOriginal columns in df_exemples: {df_exemples.columns.tolist()}\n")

	print(f"\ndf_exemples_filtered.shape: {df_exemples_filtered.shape}\n")

	#------------------------------------------------------------
	# Right table: subsidies processed by the pipeline ('all' sheet), which has the subv_id

	# Define the sheet name
	excel_sheet_name = 'all'
	print(f"\nReading Excel sheet '{excel_sheet_name}' from {input_file}\n")

	# Read the 'all' sheet and keep only the requested subsidy types
	df_all = pd.read_excel(input_file, sheet_name=excel_sheet_name)
	mask = df_all['type_subv'].isin(sub_types)
	df_all_filtered = df_all[mask]
	print(f"\nOriginal columns in df_all: {df_all.columns.tolist()}\n")

	print(f"\ndf_all_filtered.shape: {df_all_filtered.shape}\n")

	#------------------------------------------------------------
	# Join the examples with the pipeline list to get subv_id (record linkage)

	# Columns to keep from each table
	relevant_columns_left = ["type_subv", "langue", "url_start", "result", "10kW", "condition", "text"]
	relevant_columns_right = ["subv_id", "type_subv", "contributor" ,"site_url"]

	# Left join on subsidy type + URL, so every example row is kept even without a match.
	# Unmatched rows get subv_id = NaN and are filled from manual_ids.csv below.
	df_join_left = pd.merge(df_exemples_filtered[relevant_columns_left], df_all_filtered[relevant_columns_right], how='left', left_on=["type_subv","url_start"], right_on=["type_subv","site_url"], indicator=True)
	#print(f"\ndf_join_left.shape: {df_join_left.shape}\n")
	#print(df_join_left.to_markdown(maxcolwidths=40))

	# Keep only the columns needed for the golden set (drops site_url and _merge)
	relevant_columns_join = ["subv_id", "type_subv", "contributor", "langue", "result", "10kW", "condition", "text", "url_start"]
	relevant_columns_join_print = ["subv_id", "type_subv", "contributor", "langue", "10kW", "url_start"]
	df_golden_set = df_join_left[relevant_columns_join]

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set[relevant_columns_join].to_markdown(tablefmt="grid", maxcolwidths=40))
	# print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Fill in missing subv_id values from the manual IDs file

	# Read the manual IDs CSV file (one row per example that the URL join could not match)
	df_manual = pd.read_csv("manual_ids.csv")
	print(f"\nOriginal columns in df_manual: {df_manual.columns.tolist()}\n")

	# Columns needed from the manual IDs file
	relevant_columns_manual = ["url_start", "type_subv", "sub_id"]

	# Merge in the manual IDs and use them only where the automatic join found no subv_id
	df_golden_set_corrected = pd.merge(df_golden_set, df_manual[relevant_columns_manual], how='left', on=["url_start", "type_subv"])
	df_golden_set_corrected["subv_id"] = df_golden_set_corrected["subv_id"].fillna(df_golden_set_corrected["sub_id"])
	df_golden_set_corrected = df_golden_set_corrected.drop(columns="sub_id")


	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))
	# print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Remove rows that cannot be evaluated

	# Print and drop rows that still have no subv_id (e.g. Crans, which is not in the database)
	print(df_golden_set_corrected[df_golden_set_corrected["subv_id"].isna()][["type_subv", "url_start"]])
	df_golden_set_corrected = df_golden_set_corrected.dropna(subset=["subv_id"])

	# Print and drop rows whose subv_id is not processed by the pipeline (not in the filtered 'all' sheet)
	in_pipeline = df_golden_set_corrected["subv_id"].isin(df_all_filtered["subv_id"])
	print(df_golden_set_corrected[~in_pipeline][["subv_id", "type_subv", "url_start"]])
	df_golden_set_corrected = df_golden_set_corrected[in_pipeline]

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))
	# print("\n----------------------------------------------------------------\n")

	# Print the remaining subv_id and URL pairs for a manual check
	print("\n================================================================\n")
	for id, url in zip(df_golden_set_corrected["subv_id"],df_golden_set_corrected["url_start"]):
		print(f"{int(id)} : {url}")
	print("\n================================================================\n")

	#------------------------------------------------------------
	# Create the label columns: subsidy_exist and expected_10kW

	# subv_id became float because of the NaN values; convert it back to int now that all NaN are gone
	df_golden_set_corrected["subv_id"] = df_golden_set_corrected["subv_id"].astype(int)

	# subsidy_exist is "no" only when OK Climat's 'result' column says "no"
	df_golden_set_corrected["subsidy_exist"] = df_golden_set_corrected["result"].apply(lambda x: "no" if x == "no" else "yes")

	# expected_10kW is the ground-truth amount; rows without a subsidy get 0
	df_golden_set_corrected["expected_10kW"] = df_golden_set_corrected["10kW"].fillna(0.0)

	# Check: every row with a subsidy must have an amount in the original '10kW' column
	assert df_golden_set_corrected.loc[df_golden_set_corrected["subsidy_exist"] == "yes", "10kW"].notna().all()

	# Drop the original columns, now replaced by subsidy_exist and expected_10kW
	df_golden_set_corrected = df_golden_set_corrected.drop(columns=["result", "10kW"])

	print("\n----------------------------------------------------------------\n")
	print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))
	print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Add contributor information (name and canton/municipality) from the OK Climat database export

	data_input_file = "../../data/exp_subventions_20260317.xlsx"

	excel_sheet_name_1 = 'subventions'
	excel_sheet_name_2 = "subv_contrib"

	# 'subventions' links subv_id to contributor_id; 'subv_contrib' links contributor_id to name and la_id
	df_data_subventions = pd.read_excel(data_input_file, sheet_name=excel_sheet_name_1)
	df_data_subv_contrib = pd.read_excel(data_input_file, sheet_name=excel_sheet_name_2)

	# Keep only the subsidies in the golden set
	mask = df_data_subventions['subv_id'].isin(df_golden_set_corrected["subv_id"])
	df_data_subventions = df_data_subventions[mask]

	# Keep only their contributors (subv_contrib has duplicate contributor_ids, but not for these rows)
	mask = df_data_subv_contrib['contributor_id'].isin(df_data_subventions["contributor_id"])
	df_data_subv_contrib = df_data_subv_contrib[mask]

	relevant_columns_left = ["subv_id","contributor_id"]
	relevant_columns_right = ["contributor_id","contributor_name","la_id"]

	# subv_id -> contributor. validate="many_to_one" fails loudly if a contributor_id appears twice
	df_contributors = pd.merge(df_data_subventions[relevant_columns_left], df_data_subv_contrib[relevant_columns_right], how='left', on="contributor_id", indicator=True, validate="many_to_one")

	# Expect one row per golden set subsidy
	print(f"\ndf_contributors.shape: {df_contributors.shape}\n")

	relevant_columns_right = ["subv_id","contributor_name","la_id"]

	# Add contributor_name and la_id to the golden set (one contributor per subsidy)
	df_golden_set_corrected = pd.merge(df_golden_set_corrected, df_contributors[relevant_columns_right], how='left', on="subv_id", indicator=True, validate="one_to_one")

	# Check: all rows should be "both" (every subsidy found a contributor)
	print(df_golden_set_corrected["_merge"].value_counts())

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=20))
	# print("\n----------------------------------------------------------------\n")

	#-----------------------------------------------------------
	# Clean up the contributor columns

	# TODO: use .str.strip() instead, to remove the trailing spaces in "Cantone Ticino"
	df_golden_set_corrected["contributor_name"] = df_golden_set_corrected["contributor_name"].astype(str)

	# la_id >= 10000 is a canton (cantons table), lower ids are municipalities.
	# Note: SIG-éco21 (99999) is Geneva's utility but has a canton la_id, so it shows as "canton".
	df_golden_set_corrected["contributor_level"] = df_golden_set_corrected["la_id"].apply(lambda x: "canton" if x >= 10000 else "municipality")

	# Drop the merge indicator and the old short contributor code from the 'all' sheet (la_id is kept)
	df_golden_set_corrected = df_golden_set_corrected.drop(columns=["_merge","contributor"])# ,"la_id"

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=20))
	# print("\n----------------------------------------------------------------\n")

	print("\n----------------------------------------------------------------\n")
	print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=20))
	print("\n----------------------------------------------------------------\n")

	#-----------------------------------------------------------
	# Add our flags, evidence and notes per subsidy (metadata for slicing the eval results)

	flag_conditions_file = "row_flags.csv"

	df_conditions_flags = pd.read_csv(flag_conditions_file)

	print(f"\ndf_conditions_flags: {df_conditions_flags}\n")

	print(f"\ndf_conditions_flags.columns: {df_conditions_flags.columns}\n")

	# Left join keeps all golden set rows; subsidies without a row in row_flags.csv get NaN
	df_golden_set_corrected = pd.merge(df_golden_set_corrected, df_conditions_flags, how='left', on="subv_id", indicator=True, validate="one_to_one")

	# The flag columns are 1 or empty in the CSV: turn empty (NaN) into 0 and store as int.
	# The text columns evidence and notes are left as they are.
	flag_columns = df_conditions_flags.columns.drop(["subv_id", "evidence", "notes"])
	for col in flag_columns:
		print(f"\nFilling NaN values in column '{col}' with 0 and converting to int\n")
		df_golden_set_corrected[col] = df_golden_set_corrected[col].fillna(0).astype(int)

	df_golden_set_corrected = df_golden_set_corrected.drop(columns=["_merge"])

	print("\n----------------------------------------------------------------\n")
	print(df_golden_set_corrected[flag_columns].to_markdown(tablefmt="grid", maxcolwidths=20))
	print("\n----------------------------------------------------------------\n")


	#------------------------------------------------------------
	# Save version 0 of the golden set: the labels as given by OK Climat, no corrections

	assert df_golden_set_corrected["subv_id"].is_unique


	df_golden_set_corrected.to_csv(output_file, index=False)


	#-------------------------------------------------------------
	# Apply the label corrections from corrections.csv

	correction_file = "corrections.csv"

	df_corrections = pd.read_csv(correction_file)

	print(f"\ndf_corrections: {df_corrections}\n")

	relevant_columns_right = ["subv_id", "old_expected_10kW", "new_expected_10kW", "status"]

	# Left join: rows without a correction get NaN in the correction columns
	# (note: relevant_columns_right is not used here, so 'reason' is also merged in)
	df_golden_set_corrected = pd.merge(df_golden_set_corrected, df_corrections, how='left', on="subv_id", indicator=True, validate="one_to_one")

	# Rows that have a correction
	has_correction = df_golden_set_corrected["new_expected_10kW"].notna()
	# The next two lines only select values and have no effect (can be deleted)
	df_golden_set_corrected.loc[has_correction, "old_expected_10kW"]   # the old values of those rows
	df_golden_set_corrected.loc[has_correction, "expected_10kW"]       # the current values of those rows

	# Check: the old value in corrections.csv must equal the current label.
	# If not, the label changed after the correction was written, so stop instead of overwriting it.
	assert (df_golden_set_corrected.loc[has_correction, "old_expected_10kW"] == df_golden_set_corrected.loc[has_correction, "expected_10kW"]).all()

	# Apply every correction except the ones marked "rejected"
	mask = (df_golden_set_corrected["new_expected_10kW"].notna()) & (df_golden_set_corrected["status"] != "rejected")

	print("mask: ", mask)

	# Replace the label with the corrected value, only in the masked rows
	df_golden_set_corrected.loc[mask,"expected_10kW"] = df_golden_set_corrected.loc[mask,"new_expected_10kW"]

	# Drop the helper columns from corrections.csv
	df_golden_set_corrected = df_golden_set_corrected.drop(columns=["old_expected_10kW", "new_expected_10kW", "status", "_merge"])

	print("\nCOLUMNS : ", df_golden_set_corrected.columns)

	# Short column selection for a readable printout
	columns_for_printing = ["subv_id", "type_subv", "contributor_name", "contributor_level", "langue", "subsidy_exist", "expected_10kW", "url_start"]

	print("\n----------------------------------------------------------------\n")
	print(df_golden_set_corrected[columns_for_printing].to_markdown(tablefmt="grid", maxcolwidths=20))
	print("\n----------------------------------------------------------------\n")

	#-------------------------------------------------------------
	# Save the corrected golden set next to version 0, e.g. golden_set.csv -> golden_set_corrected.csv

	base, ext = os.path.splitext(output_file)   # "../golden_set", ".csv"
	corrected_file = f"{base}_corrected{ext}"   # "../golden_set_corrected.csv"

	df_golden_set_corrected.to_csv(corrected_file, index=False)


if __name__ == "__main__":
	# Command-line arguments; the defaults work when running from pipeline/eval/
	parser = argparse.ArgumentParser(description="Build a golden set for model evaluation from an Excel file.")
	parser.add_argument("--input_file", type=str, help="Path to the input Excel file.", default='../PV examples.xlsx')
	parser.add_argument("--output_file", type=str, help="Path to the output CSV file.", default='golden_set.csv')
	parser.add_argument("--sub_types", type=str, nargs='+', help="List of allowed subv types (e.g., PV, PV-EauCd).", default=['PV', 'PV-EauCd'])
	args = parser.parse_args()

	build_golden_set(args.input_file, args.output_file, args.sub_types)
