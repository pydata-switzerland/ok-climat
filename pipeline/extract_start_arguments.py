import pandas as pd

# Read the Excel file and get the 'exemples' sheet
#df = pd.read_excel('PV examples.xlsx', sheet_name='exemples')

sub_types_allowed = ['PV', 'PV-EauCd']

df = pd.read_excel('PV examples.xlsx', sheet_name='all')

# Print all rows from the 'url' column
print("\n-----------------------\n")

print(df['type_subv'])
print("\n-----------------------\n")

# # Make and save a dict file with the url and type_subv columns
# url_type_dict = dict(zip(df['subv_id'] ,df['site_url'], df['type_subv']))

# add a key for each url and type_sub pair that is called sub_1, sub_2 etc
url_type_dict = {
    str(row['subv_id']): {
        "site_url": row['site_url'],
        "type_subv": row['type_subv']
    }
    for _, row in df.iterrows()
    if row['type_subv'] in sub_types_allowed
}


# Save the dict to a file
import json
with open('url_type_dict.json', 'w') as f:
	json.dump(url_type_dict, f, indent=4)	

# Get from the sheet called keywords, and print all columns
df_keywords = pd.read_excel('PV examples.xlsx', sheet_name='keywords')

# print("\n-----------------------\n")
# print(df_keywords)

# import pandas as pd

# # Read the keywords sheet
# df_keywords = pd.read_excel('PV examples.xlsx', sheet_name='keywords')

# # Create a dict to store keywords by category
# keywords_dict = {}

# # Iterate through the dataframe
# for idx, row in df_keywords.iterrows():
#     category = row.iloc[0]  # First column (PV, PV-EauCd, etc.)
#     keyword = row.iloc[2]   # Third column (the keyword)
    
#     # Skip if category or keyword is NaN
#     if pd.isna(category) or pd.isna(keyword):
#         continue
    
#     # Add category to dict if it doesn't exist
#     if category not in keywords_dict:
#         keywords_dict[category] = []
    
#     # Add keyword to the list
#     keywords_dict[category].append(keyword)

# # Print the result
# for category, keywords in keywords_dict.items():
#     print(f"{category}: {keywords}")

# # Optionally save to JSON
# import json
# with open('keywords_dict.json', 'w') as f:
#     json.dump(keywords_dict, f, indent=4)