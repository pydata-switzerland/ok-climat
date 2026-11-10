import pandas as pd
import argparse

# python build_golden_set.py --input_file '../PV examples.xlsx' --output_file 'golden_set.csv' --sub_types PV PV-EauCd

def build_golden_set(input_file, output_file, sub_types):

	
	print(f"\nBuilding golden set from {input_file} to evaluate model\n")

	#------------------------------------------------------------
	# Make "left" dataframe

	# Define the sheet name 
	excel_sheet_name = 'exemples'
	print(f"\nReading Excel sheet '{excel_sheet_name}' from {input_file}\n")

	# Read the Excel 'exemples' sheet and filter based on the provided sub_types
	df_exemples = pd.read_excel(input_file, sheet_name=excel_sheet_name)
	mask = df_exemples['type_subv'].isin(sub_types)
	df_exemples_filtered = df_exemples[mask]	
	print(f"\nOriginal columns in df_exemples: {df_exemples.columns.tolist()}\n")

	print(f"\ndf_exemples_filtered.shape: {df_exemples_filtered.shape}\n")

	#------------------------------------------------------------
	# Make "right" dataframe

	# Define the sheet name
	excel_sheet_name = 'all'
	print(f"\nReading Excel sheet '{excel_sheet_name}' from {input_file}\n")

	# Read the Excel 'all' sheet and filter the data based on the provided sub_types
	df_all = pd.read_excel(input_file, sheet_name=excel_sheet_name)
	mask = df_all['type_subv'].isin(sub_types)
	df_all_filtered = df_all[mask]
	print(f"\nOriginal columns in df_all: {df_all.columns.tolist()}\n")

	print(f"\ndf_all_filtered.shape: {df_all_filtered.shape}\n")

	#------------------------------------------------------------
	# Join dataframes

	# Define the relevant columns for the join operation
	relevant_columns_left = ["type_subv", "langue", "url_start", "result", "10kW", "condition", "text"]
	relevant_columns_right = ["subv_id", "type_subv", "contributor" ,"site_url"]

	# Join the two filtered DataFrames on 'subv_id' to get the final golden set
	df_join_left = pd.merge(df_exemples_filtered[relevant_columns_left], df_all_filtered[relevant_columns_right], how='left', left_on=["type_subv","url_start"], right_on=["type_subv","site_url"], indicator=True)
	#print(f"\ndf_join_left.shape: {df_join_left.shape}\n")
	#print(df_join_left.to_markdown(maxcolwidths=40))

	# Define the relevant columns for the final golden set DataFrame
	relevant_columns_join = ["subv_id", "type_subv", "contributor", "langue", "result", "10kW", "condition", "text", "url_start"]
	relevant_columns_join_print = ["subv_id", "type_subv", "contributor", "langue", "10kW", "url_start"]
	df_golden_set = df_join_left[relevant_columns_join]

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set[relevant_columns_join].to_markdown(tablefmt="grid", maxcolwidths=40))
	# print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Add missing subv_id values with manual IDs file

	# Read the manual IDs CSV file
	df_manual = pd.read_csv("manual_ids.csv")
	print(f"\nOriginal columns in df_manual: {df_manual.columns.tolist()}\n")

	# Define the relevant columns for the manual IDs DataFrame 
	relevant_columns_manual = ["url_start", "type_subv", "sub_id"]

	# Merge the golden set DataFrame with the manual IDs DataFrame to correct missing subv_id values
	df_golden_set_corrected = pd.merge(df_golden_set, df_manual[relevant_columns_manual], how='left', on=["url_start", "type_subv"])
	df_golden_set_corrected["subv_id"] = df_golden_set_corrected["subv_id"].fillna(df_golden_set_corrected["sub_id"])
	df_golden_set_corrected = df_golden_set_corrected.drop(columns="sub_id")

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))	
	# print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Dropping rows with NAN subv_id values

	print(df_golden_set_corrected[df_golden_set_corrected["subv_id"].isna()][["type_subv", "url_start"]])
	df_golden_set_corrected = df_golden_set_corrected.dropna(subset=["subv_id"])

	# print("\n----------------------------------------------------------------\n")
	# print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))	
	# print("\n----------------------------------------------------------------\n")

	print("\n================================================================\n")
	for id, url in zip(df_golden_set_corrected["subv_id"],df_golden_set_corrected["url_start"]):
		print(f"{int(id)} : {url}")
	print("\n================================================================\n")

	#------------------------------------------------------------
	# Additional data preparations 

	# convert subv_id to int
	df_golden_set_corrected["subv_id"] = df_golden_set_corrected["subv_id"].astype(int)

	# Create a new column 'subsidy_exist' based on the 'result' column
	df_golden_set_corrected["subsidy_exist"] = df_golden_set_corrected["result"].apply(lambda x: "no" if x == "no" else "yes")

	# Create a new column 'expected_10kW' based on the '10kW' column, ensuring that negative values are set to 0.0
	df_golden_set_corrected["expected_10kW"] = df_golden_set_corrected["10kW"].apply(lambda x: x if x > 0.0 else 0.0)
	
	# Drop the 'result' and '10kW' columns as they are no longer needed
	df_golden_set_corrected = df_golden_set_corrected.drop(columns=["result", "10kW"])

	print("\n----------------------------------------------------------------\n")
	print(df_golden_set_corrected.to_markdown(tablefmt="grid", maxcolwidths=40))	
	print("\n----------------------------------------------------------------\n")

	#------------------------------------------------------------
	# Save the golden set based on input excel files from OPK Climat

	assert df_golden_set_corrected["subv_id"].is_unique

	df_golden_set_corrected.to_csv(output_file, index=False)



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Build a golden set for model evaluation from an Excel file.")
	parser.add_argument("--input_file", type=str, help="Path to the input Excel file.", default='../PV examples.xlsx')
	parser.add_argument("--output_file", type=str, help="Path to the output CSV file.", default='golden_set.csv')
	parser.add_argument("--sub_types", type=str, nargs='+', help="List of allowed subv types (e.g., PV, PV-EauCd).", default=['PV', 'PV-EauCd'])
	args = parser.parse_args()

	build_golden_set(args.input_file, args.output_file, args.sub_types) 

	






