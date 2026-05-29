import argparse
import json
import os
import requests

def analyze_subsidy(api_key, file_path, subsidy_type, keywords_file, subsidy_def):
    """Analyze a markdown document for a specific subsidy type based on keywords dict."""
    
    # 1. Validate file paths
    if not os.path.exists(file_path):
        print(f"✗ Error: Subsidy markdown file not found at {file_path}")
        return

    if not os.path.exists(keywords_file):
        print(f"✗ Error: Keywords file not found at {keywords_file}")
        return

    # 2. Extract keywords from JSON
    try:
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_dict = json.load(f)
    except Exception as e:
        print(f"✗ Error reading keywords JSON: {e}")
        return

    keywords = keywords_dict.get(subsidy_type)
    if not keywords:
        print(f"✗ Error: Subsidy type '{subsidy_type}' not found in {keywords_file}. Available: {list(keywords_dict.keys())}")
        return

    # 3. Read markdown content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            document_content = f.read()
    except Exception as e:
        print(f"✗ Error reading source document: {e}")
        return

    # 4. Craft Prompt
    keywords_str = ", ".join(keywords)
    prompt = (
        f"You are an expert policy assistant reading Swiss municipal documents.\n"
        f"Analyze this document specifically searching for subsidies related to: {subsidy_def}.\n"
        f"Key search terms/categories to look for in German, French, or Italian: {keywords_str}.\n\n"
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

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-2.5-flash-lite",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,  # Low temperature for highly factual reporting
        "max_tokens": 1500
    }

    print(f"🔍 Analyzing '{file_path}' ({len(document_content)} characters) for '{subsidy_type}'...")

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        analysis_content = result["choices"][0]["message"]["content"]
        
        # Print nicely using rich if available, fallback otherwise
        print("\n" + "=" * 60)
        print(f" ANALYSIS RESULT FOR: {subsidy_type} ")
        print("=" * 60 + "\n")
        
        # Print each answer on a new line
        lines = analysis_content.split('\n')
        for line in lines:
            if line.strip().startswith(tuple(str(i) for i in range(1, 7))):
                print()  # Add a blank line before each numbered answer
            print(f"\n{line}")
            
        print("\n" + "=" * 60)

    except requests.exceptions.RequestException as e:
        print(f"✗ API Connection Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Analyze Swiss municipal documents for subsidies using LLM.")
	parser.add_argument("--subsidy_file", required=True, help="Path to markdown document to analyze.")
	parser.add_argument("--subsidy_type", required=True, choices=["PV", "PV-EauCd"], help="Subsidy type to search for.")
	parser.add_argument("--keywords_file", default="keywords_dict.json", help="Path to keywords JSON dictionary file.")

	args = parser.parse_args()

	subsidy_def = args.subsidy_type
	if args.subsidy_type == "PV":
		subsidy_def = "Photovoltaic (PV) subsidies typically support the installation of solar panels on residential or commercial buildings. They may include fixed amounts per kW installed, total caps, or specific requirements for eligibility such as building type, location, or installation date."
	elif args.subsidy_type == "PV-EauCd":
		subsidy_def = "PV-EauCd (Photovoltaic water heating) subsidies are designed to encourage the use of solar thermal systems for water heating. These subsidies may be calculated based on the area of solar collectors installed (e.g., CHF per square meter) rather than per kW, and often have specific requirements regarding system design, installation, and performance."

	print(f"🔎 Starting analysis for subsidy type: {args.subsidy_type} ({subsidy_def})")

	api_key = os.getenv("OPENROUTER_API_KEY")
	if not api_key:
		print("✗ Error: OPENROUTER_API_KEY environment variable not set.")
		prnt("Please set it with: export OPENROUTER_API_KEY='your-key-here'")
	else:
		analyze_subsidy(api_key, args.subsidy_file, args.subsidy_type, args.keywords_file, subsidy_def)
        




# python test_openrouter.py --subsidy_file texts/thermische_solaranlagen_luzern.md --subsidy_type PV --keywords_file keywords_dict.json

# python test_openrouter.py --subsidy_file texts/thermische_solaranlagen_luzern.md --subsidy_type PV-EauCd --keywords_file keywords_dict.json



######

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