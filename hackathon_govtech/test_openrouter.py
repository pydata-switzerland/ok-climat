import argparse
import json
import os
import requests
import glob

def load_url_type_dict(url_type_dict_path="url_type_dict.json"):
    """Load the url_type_dict.json file."""
    try:
        with open(url_type_dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: {url_type_dict_path} not found.")
        return {}
    except Exception as e:
        print(f"✗ Error loading {url_type_dict_path}: {e}")
        return {}
	

def find_files_for_sub_id(sub_id, texts_dir="texts"):
    """Find all files in the texts/ folder that match subID_{sub_id}_*.md."""
    pattern = f"subID_{sub_id}_*.md"
    files = glob.glob(os.path.join(texts_dir, pattern))
    return files

def analyze_files_for_sub_id(api_key, files, subsidy_type, keywords_file, subsidy_def):
	"""Analyze all files for a sub_id and return the first valid 10 kW subsidy amount."""
	total_subsidy = "0"  # Default to 0 if no valid subsidy is found

	for file_path in files:
		print(f"\n🔍 Analyzing {file_path}...")
		try:
			# Read the file content
			with open(file_path, "r", encoding="utf-8") as f:
				document_content = f.read()

			# Craft the prompt
			keywords = load_keywords_from_json(keywords_file, subsidy_type)
			if not keywords:
				print(f"✗ No keywords found for {subsidy_type}. Skipping...")
				continue


			keywords_str = ", ".join(keywords)
			prompt = (
				f"You are an expert policy assistant reading Swiss municipal documents.\n"
				f"Analyze this document specifically searching for subsidies related to '{subsidy_type}' : {subsidy_def}.\n"
				f"You should look for text with terms/categories in German, French, or Italian similar to: {keywords_str}.\n\n"
                f"If you see a PV subsidy that is calulated as a percentage X of the ProNovo subvention, then to calculate the total subsidy for 10 kW, you have to take X% of 360 CHF per kW and multiple by 10"
                f"Similarily, If a PV subsidy is given per square meter, then assume 1 m2 of solar panels generates 0.5 KW ; so you will need 20 m2 for 10 KW"
                f"Similarily, If a PV-EuaCd subsidy is given per square meter, then assume 1 m2 of solar panels generates 0.2 KW ; so you will need 50 m2 for 10 KW"
				f"Provide a structured extraction containing EXACTLY the following six points:\n"
				f"(1) Is there a subsidy provided: YES/NO\n"
				f"(2) Base amount CHF: [Specify any one-time or fixed amount in CHF, including contributions for monitoring or other requirements, or 0.0 if not found]\n"
				f"(3) Amount CHF per kW: [Specify amount per kW if found or put zero if not found]\n"
				f"(4) Calculate total subsidy amount for 10 kW: [Sum the base amount and the per kW amount times 10. If not possible, note 'N/A'/'Cannot be calculated']\n"
				f"(5) Are there any restrictions for this subsidy: [Describe any special requirements, building constraints, angles, dates, or note 'None']\n"
				f"(6) Raw text blocks (in Markdown): [Extract the exact language passages/paragraphs from the document used to confirm this information, formatted as Markdown (e.g., use bullet points, bold, blockquotes, etc.), if (1) is YES; if not, return 'no subsidy text found']\n\n"
				f"Document Content:\n"
				f"{document_content}"
			)

			# print("\n=========================================\n")
			# print("\nPrint prompt:\n")
			# print(prompt)
			# print("\n=========================================\n")

			# Call the API
			url = "https://openrouter.ai/api/v1/chat/completions"
			headers = {
				"Authorization": f"Bearer {api_key}",
				"Content-Type": "application/json"
			}

			data = {
				"model": "google/gemini-2.5-flash-lite", # 3.1 better
				"messages": [
					{
						"role": "user",
						"content": prompt
					}
				],
				"temperature": 0.1,
				"max_tokens": 1500
			}

			response = requests.post(url, json=data, headers=headers)
			response.raise_for_status()
			result = response.json()
			analysis_content = result["choices"][0]["message"]["content"]

			# Print the full analysis for verification
			print("\n" + "=" * 60)
			print(f" ANALYSIS RESULT FOR: {subsidy_type} ({file_path})")
			print("=" * 60 + "\n")
			lines = analysis_content.split('\n')
			for line in lines:
				if line.strip().startswith(tuple(str(i) for i in range(1, 7))):
					print()  # Add a blank line before each numbered answer
				print(f"\n{line}")
			print("\n" + "=" * 60)

			# Extract the 10 kW subsidy amount
			for line in analysis_content.split('\n'):
				if line.strip().startswith("4") or "Calculate total subsidy amount for 10 kW" in line:
					parts = line.split(":", 1)
					if len(parts) > 1:
						current_subsidy = parts[1].strip()
						# If a valid subsidy is found, update total_subsidy and break
						if current_subsidy and current_subsidy != "N/A" and current_subsidy != "Cannot be calculated":
							total_subsidy = current_subsidy
							break
					else:
						current_subsidy = line.strip()
						if current_subsidy and current_subsidy != "N/A" and current_subsidy != "Cannot be calculated":
							total_subsidy = current_subsidy
							break

		except Exception as e:
			print(f"✗ Error analyzing {file_path}: {e}")
			continue

	return total_subsidy

def load_keywords_from_json(keywords_file, subsidy_type):
    """Load keywords for a specific subsidy type from keywords_dict.json."""
    try:
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_dict = json.load(f)
        return keywords_dict.get(subsidy_type, [])
    except Exception as e:
        print(f"✗ Error loading keywords: {e}")
        return []        

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Analyze Swiss municipal documents for subsidies using LLM.")
	parser.add_argument("--sub_id", required=True, help="Subsidy ID (e.g., 2041).")
	parser.add_argument("--url_type_dict", default="url_type_dict.json", help="Path to url_type_dict.json file.")
	parser.add_argument("--keywords_file", default="keywords_dict.json", help="Path to keywords JSON dictionary file.")

	args = parser.parse_args()

	# Load the url_type_dict to get the subsidy_type
	url_type_dict = load_url_type_dict(args.url_type_dict)
	if not url_type_dict:
		exit(1)

	if args.sub_id not in url_type_dict:
		print(f"✗ Error: Subsidy ID '{args.sub_id}' not found in {args.url_type_dict}.")
		exit(1)

	subsidy_type = url_type_dict[args.sub_id]["type_subv"]

	# Define subsidy_def based on subsidy_type
	if subsidy_type == "PV":
		subsidy_def = "Photovoltaic (PV) subsidies typically support the installation of solar panels on residential or commercial buildings. They may include fixed amounts per kW installed, total caps, or specific requirements for eligibility such as building type, location, or installation date."
	elif subsidy_type == "PV-EauCd":
		subsidy_def = "PV-EauCd (Photovoltaic water heating) subsidies are designed to encourage the use of solar thermal systems for water heating. These subsidies may be calculated based on the area of solar collectors installed (e.g., CHF per square meter) rather than per kW, and often have specific requirements regarding system design, installation, and performance."
	else:
		print(f"✗ Error: Unknown subsidy type '{subsidy_type}'.")
		exit(1)

	print(f"🔎 Starting analysis for subsidy ID: {args.sub_id} (Type: {subsidy_type})")

	# Find all files for this sub_id
	files = find_files_for_sub_id(args.sub_id)
	if not files:
		print(f"✗ No files found for sub_id {args.sub_id} in texts/.")
		exit(1)

	print(f"Found {len(files)} files for sub_id {args.sub_id}.")

	api_key = os.getenv("OPENROUTER_API_KEY")
	if not api_key:
		print("✗ Error: OPENROUTER_API_KEY environment variable not set.")
		print("Please set it with: export OPENROUTER_API_KEY='your-key-here'")
		exit(1)
		
	print("subsidy_type:", subsidy_type)

	# Analyze all files and get the first valid 10 kW subsidy amount
	total_subsidy = analyze_files_for_sub_id(api_key, files, subsidy_type, args.keywords_file, subsidy_def)

	# Save the result
	results_dir = "results"
	if not os.path.exists(results_dir):
		os.makedirs(results_dir)

	result_data = {
		"sub_id": args.sub_id,
		"subsidy_type": subsidy_type,
		"total_subsidy_10kW": total_subsidy
	}
	result_file_path = os.path.join(results_dir, f"{args.sub_id}_analysis.json")
	with open(result_file_path, "w", encoding="utf-8") as f:
		json.dump(result_data, f, indent=4)

	print(f"\n✅ Analysis completed successfully. Result saved to {result_file_path}")


# python test_openrouter.py --subsidy_file texts/thermische_solaranlagen_luzern.md --subsidy_type PV --keywords_file keywords_dict.json

# python test_openrouter.py --subsidy_file texts/thermische_solaranlagen_luzern.md --subsidy_type PV-EauCd --keywords_file keywords_dict.json



#######################

# sub_1 -> gets right
# python test_openrouter.py --subsidy_file texts/sub_1_PV-EauCd_site_1779996252.md --subsidy_type PV-EauCd --keywords_file keywords_dict.json

# sub_2 -> does not get right
# python test_openrouter.py --subsidy_file texts/sub_2_PV_site_1779996290.md --subsidy_type PV --keywords_file keywords_dict.json

# sub 3 --> gets right
# python test_openrouter.py --subsidy_file texts/sub_3_PV_site_1779996437.md --subsidy_type PV --keywords_file keywords_dict.json

# sub 4 --> gets right
# python test_openrouter.py --subsidy_file texts/sub_4_PV_site_1779996463.md --subsidy_type PV --keywords_file keywords_dict.json
# sub 4 --> gets right (but the same as above, so we can check consistency)
# python test_openrouter.py --subsidy_file texts/sub_4_PV_site_1779996772.md --subsidy_type PV --keywords_file keywords_dict.json
# sub 4 --> gets right (but the same as above, so we can check consistency)
# python test_openrouter.py --subsidy_file texts/sub_4_PV_site_1779996796.md --subsidy_type PV --keywords_file keywords_dict.json
# finds zero on these below
# python test_openrouter.py --subsidy_file texts/sub_4_PV_site_1779996804.md --subsidy_type PV --keywords_file keywords_dict.json
# python test_openrouter.py --subsidy_file texts/sub_4_PV_site_1779996811.md --subsidy_type PV --keywords_file keywords_dict.json



