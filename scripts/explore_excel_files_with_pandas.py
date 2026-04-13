import pandas as pd 
import time
import argparse 


# Start time
t1 = time.time()

# Load excel file 
excel_file_1 = pd.ExcelFile("../data/exp_subventions_20251203.xlsx")
excel_file_2 = pd.ExcelFile("../data/exp_subventions_20251213.xlsx")
excel_file_2 = pd.ExcelFile("../exp_subventions_20260317.xlsx")

# Print sheet names
print(f"\nFile 1, excel sheet names : \n{excel_file_1.sheet_names}\n")
print(f"File 2, excel sheet names : \n{excel_file_2.sheet_names}\n")

# Store each sheet as a pandas data frame in a dictionary 
sheets1_dict = {sheet_name : excel_file_1.parse(sheet_name) for sheet_name in excel_file_1.sheet_names}
sheets2_dict = {sheet_name : excel_file_2.parse(sheet_name) for sheet_name in excel_file_2.sheet_names}

print("\nPrinting columns of each table from file 2:")
for table in excel_file_2.sheet_names:
	print(f"\nTable = '{table}' : ")
	for col in sheets2_dict[table].columns.tolist():
		print(f"	{col}")

# #----------------------------------------------------------------
# # checking if string exist in tables
# indicator = "ENRG_C103"
# indicator = "ENRG_D_104"

# for sheet_name, df in sheets2_dict.items():
#     found = False
#     for col in df.columns:
#         mask = df[col].astype(str).str.contains(indicator, na=False)
#         if mask.any():
#             found = True
#             rows = df.index[mask].tolist()
#             print(f"Found '{indicator}' in sheet '{sheet_name}', column '{col}' at rows: {rows}")
#     if not found:
#         print(f"Did not find '{indicator}' in sheet '{sheet_name}'")
# #------------------------------------

# Display the first few rows
# print("\nFile 1 :")
# print(df1_subventions.head())
# print("\nFile 2 :")
# print(df2_subventions.head())

# #======================================================
# # File 2

# df2_municipalities = pd.read_excel(excel_file_2, sheet_name="municipalities")

# # Display the first few rows
# print("------------------------------------------------\n")
# print("\nFile 2 :")
# print("\n subv_type:")
# print(sheets2_dict["subv_type"].head())
# print("\n subventions:")
# print(sheets2_dict["subventions"].head())
# print("\n subv_contrib:")
# print(sheets2_dict["subv_contrib"].head())
# print("\n municipalities:")
# print(sheets2_dict["municipalities"].head())
# print("\n cantons:")
# print(sheets2_dict["cantons"].head())
# print("------------------------------------------------\n")
# # #=======================================================
# # Explore

# df_subs = sheets2_dict["subventions"]
# cont_ids = df_subs.loc[df_subs["subv_id"]==14, "contributor_id"]

# df_contrib = sheets2_dict["subv_contrib"]
# la_ids = df_contrib.loc[df_contrib["contributor_id"].isin(cont_ids), "la_id"]

# print("\ncont_ids" , cont_ids)
# print("\nla_ids" , la_ids)

# subv_id = df_subs['subv_id']
# print(f"\nlen(subv_id)={len(subv_id)}")
# subv_id_unique = df_subs['subv_id'].unique()
# print(f"len(subv_id_unique)={len(subv_id_unique)}")



def print_each_row_for_column(column_name, df_name, dict_sheet, rowprint=False, unique=False):

	df = dict_sheet[df_name]

	df_unique = df[column_name].copy().unique()

	if unique:
		for row in df_unique:
			if rowprint==True:
				print(f"{row}")
	else:
		for row in df[column_name]:
			if rowprint==True:
				print(f"{row}")


	print(f"Table {df_name} there are {len(df[column_name])} rows in column {column_name} -> unique rows are : {len(df[column_name].unique())}")

# #-----------------------------

dict_sheet = sheets2_dict

# df_name = "subv_type"
# print(f"\nTABLE '{df_name}'")

# column_name = "subv_id"
# print_each_row_for_column(column_name, df_name, dict_sheet)
# column_name = "group_id"
# print_each_row_for_column(column_name, df_name, dict_sheet)
# column_name = "sector"
# print_each_row_for_column(column_name, df_name, dict_sheet)
# column_name = "group_name"
# print_each_row_for_column(column_name, df_name, dict_sheet)
# column_name = "key"
# print_each_row_for_column(column_name, df_name, dict_sheet)
# column_name = "available_for"
# print_each_row_for_column(column_name, df_name, dict_sheet)

df_name = "subventions"
print(f"\nTABLE '{df_name}'")

column_name = "subv_id"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "contributor_id"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "language"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "subv_name"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "subv_desc"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "site_url"
print_each_row_for_column(column_name, df_name, dict_sheet)
column_name = "type_subv"
print_each_row_for_column(column_name, df_name, dict_sheet)

# print("\n-------------------------------------------\n ")
df_name = "subventions"
column_name = "type_subv"
print_each_row_for_column(column_name, df_name, dict_sheet, True, True)
print(" ")
column_name = "subv_id"
print_each_row_for_column(column_name, df_name, dict_sheet, True, True)
# print("\n-------------------------------------------\n ")
# df_name = "indicators"
# column_name = "indicateur"
# print_each_row_for_column(column_name, df_name, dict_sheet, True, True)

print("\n====================================================\n")

dict_sheet = sheets2_dict

df_subventions = dict_sheet["subventions"]
df_subv_contrib = dict_sheet["subv_contrib"]
df_cantons = dict_sheet["cantons"]

# In df_subventions get 'contributor_id' of all rows where 'type_subv'=="PV"
pv_subv = df_subventions[(df_subventions["type_subv"] == "PV") | (df_subventions["type_subv"] == "PV-EauCd")]
contributor_ids = pv_subv["contributor_id"]
print(f"\n{contributor_ids}")

# In df_subv_contrib get the 'la_id' of the corresponding 'contributor_id' (from before)
pv_contrib = df_subv_contrib[df_subv_contrib["contributor_id"].isin(contributor_ids)]
la_ids = pv_contrib["la_id"]

# In df_cantons get the 'kt_abrev' of the corresponding 'la_id' (from before)
pv_cantons = df_cantons[df_cantons["la_id"].isin(la_ids)]

# Merge pv_subv with pv_contrib on contributor_id
merged = pd.merge(pv_subv, pv_contrib, on="contributor_id", how="inner")

# Merge with pv_cantons on la_id
final = pd.merge(merged, pv_cantons, on="la_id", how="inner")

# Select desired columns
result = final[["type_subv", "base_value","kt_abrev", "subv_desc"]]
print("\nRESULT:")
print(result)
print("\nlen(result)", len(result))

print(" ")
for c,d in zip(result["kt_abrev"],result["subv_desc"]):

	print(f"\n{c} : d = {d}'")

# # #=======================================================

# print("\n====================================================\n")

# dict_sheet = sheets2_dict

# df_subventions = dict_sheet["subventions"]
# df_subv_contrib = dict_sheet["subv_contrib"]
# df_cantons = dict_sheet["cantons"]

# # In df_subventions get 'contributor_id' of all rows where 'type_subv'=="PV"
# pv_subv = df_subventions
# contributor_ids = pv_subv["contributor_id"]

# # In df_subv_contrib get the 'la_id' of the corresponding 'contributor_id' (from before)
# pv_contrib = df_subv_contrib[df_subv_contrib["contributor_id"].isin(contributor_ids)]
# la_ids = pv_contrib["la_id"]

# # In df_cantons get the 'kt_abrev' of the corresponding 'la_id' (from before)
# pv_cantons = df_cantons[df_cantons["la_id"].isin(la_ids)]

# # Merge pv_subv with pv_contrib on contributor_id
# merged = pd.merge(pv_subv, pv_contrib, on="contributor_id", how="inner")

# # Merge with pv_cantons on la_id
# final = pd.merge(merged, pv_cantons, on="la_id", how="inner")

# # Select desired columns
# result = final[["type_subv", "base_value","kt_abrev", "subv_desc", "site_url"]].sort_values(by="kt_abrev")
# print("\nRESULT:")
# print(result)
# print("\nlen(result)", len(result))

# print("Start running through joined data frame: ")
# for c,d,w in zip(result["kt_abrev"],result["type_subv"],result["site_url"]):

# 	print(f"\n{c} : sub = {d} ({w})' ")

# #=======================================================

# print("\n====================================================\n")

# dict_sheet = sheets2_dict

# df_subventions = dict_sheet["subventions"]
# df_subv_contrib = dict_sheet["subv_contrib"]
# df_cantons = dict_sheet["cantons"]

# print("\ndf_cantons",df_cantons)

# print("\ndf_subventions",df_subventions)

# merged_1 = pd.merge(df_cantons, df_subv_contrib, on="la_id", how="inner")

# print("\nmerged_1 = \n",merged_1)

# merged_2 = pd.merge(merged_1, df_subventions, on="contributor_id", how="inner")

# print("\nmerged_2 = \n", merged_2[merged_2["kt_abrev"] == "ZH"][["kt_abrev", "site_url"]])

# print("\n====================================================\n")

# dict_sheet = sheets2_dict

# df_subventions = dict_sheet["subventions"]
# df_subv_contrib = dict_sheet["subv_contrib"]
# df_cantons = dict_sheet["municipalities"]

# print("\ndf_cantons",df_cantons)
# print("\n&& len(df_cantons)", len(df_cantons))

# print("\ndf_subventions",df_subventions)

# merged_1 = pd.merge(df_cantons, df_subv_contrib, on="la_id", how="inner")

# print("\nmerged_1 = \n",merged_1)

# df_subventions_PV = df_subventions[df_subventions["type_subv"]=="PV"]

# merged_2 = pd.merge(merged_1, df_subventions_PV, on="contributor_id", how="inner")

# print("\nmerged_2 = \n",merged_2)

# print("LEN merged_2=",len(merged_2))

# print("\nmerged_2 = \n", merged_2[merged_2["name_mun"] == "Kloten"][["name_mun", "site_url","type_subv"]])

# #==============================

# # End time
# t2 = time.time()

# # Run time in seconds
# t_diff = t2-t1
# print(f"\nRun time = {t_diff:0f} s\n")
