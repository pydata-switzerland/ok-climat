import argparse
import subprocess
import json
import time

#===============================================
# Alternativily give list of subsidy
#sub_ids = ["118","522","225","2939"] 
# sub_ids = ["118"] # Only site info, no pdf
# sub_ids = ["5125"]  
# sub_ids = ["4553"] # direct pdf link
# sub_ids = ["4830"] # with nan url 
# sub_ids = ["4793"] # with one pdf that does not work and another that does with dockling (same?)
# sub_ids = ["4792"] # with pdf that works
# sub_ids = ["3351"] # with one pdf that does not work and another that does with dockling (same?)
#===============================================

# Run example:

# python run_pipeline.py -ni 0 -nf 10 --step "scraper"
# python run_pipeline.py -ni 0 -nf 10 --step "llm"

# python run_pipeline.py --sub_id 118 --step "scraper"

#===============================================

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

def run_scraper_for_sub_id(sub_id, url_type_dict_path="url_type_dict.json"):
    """Run the scraper for a given sub_id."""
    cmd = [
        "python", "scraper_okclimat.py",
        "--sub_id", sub_id,
        "--url_type_dict", url_type_dict_path
    ]
    print(f"Running scraper for sub_id: {sub_id}")
    subprocess.run(cmd, check=True)

def run_llm_analysis_for_sub_id(sub_id, url_type_dict_path="url_type_dict.json", keywords_file="keywords_dict.json"):
    """Run the LLM analysis for a given sub_id."""
    cmd = [
        "python", "test_openrouter.py",
        "--sub_id", sub_id,
        "--url_type_dict", url_type_dict_path,
        "--keywords_file", keywords_file
    ]
    print(f"🧠 Running LLM analysis for sub_id: {sub_id}")
    subprocess.run(cmd, check=True)

def main(start_index, end_index, run_scraper=True, run_llm=True, url_type_dict_path="url_type_dict.json", keywords_file="keywords_dict.json"):
    """Run the pipeline for a range of sub_ids."""
    # Load the url_type_dict

    url_type_dict = load_url_type_dict(url_type_dict_path)
    if not url_type_dict:
        return
    
    # If end_index is -1, set it to the last index of url_type_dict
    if end_index == -1 :
        end_index = len(url_type_dict) - 1

    # Extract the first N sub_ids
    sub_ids = list(url_type_dict.keys())[start_index:end_index + 1]
    if not sub_ids:
        print(f"✗ No sub_ids found in the range {start_index}-{end_index}.")
        return

    print(f"Run pipeline on index {start_index}-{end_index} corresponding to these sub_ids: \n{sub_ids}\n")

    for sub_id in sub_ids:
        if run_scraper:
            run_scraper_for_sub_id(sub_id, url_type_dict_path)
        if run_llm:
            run_llm_analysis_for_sub_id(sub_id, url_type_dict_path, keywords_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the scraper and LLM analysis pipeline for a range of sub_ids.")
    parser.add_argument("-ni", "--start_index", type=int, default=0, help="Start index (0-based) of sub_ids to process. Defaults to 0.")
    parser.add_argument("-nf", "--end_index", type=int, default=None, help="End index (0-based) of sub_ids to process. If omitted, start_index is used.")
    parser.add_argument("-s", "--sub_id", type=str, default=None, help="Specific sub_id to process (overrides index range).")
    parser.add_argument("--step", type=str, choices=["scraper", "llm", "both"], default="both", help="Run only the scraper, only the LLM analysis, or both (default: both).")
    parser.add_argument("--url_type_dict", default="url_type_dict.json", help="Path to url_type_dict.json file.")
    parser.add_argument("--keywords_file", default="keywords_dict.json", help="Path to keywords_dict.json file.")
    args = parser.parse_args()

    time_start = time.time()

    # Determine which steps to run
    run_scraper = (args.step == "scraper" or args.step == "both")
    run_llm = (args.step == "llm" or args.step == "both")

    # If a specific sub_id is given, run only that (overrides index-based running)
    if args.sub_id:
        sub_id = args.sub_id
        print(f"\nRunning pipeline for specific sub_id: {sub_id}\n")
        if run_scraper:
            run_scraper_for_sub_id(sub_id, args.url_type_dict)
        if run_llm:
            run_llm_analysis_for_sub_id(sub_id, args.url_type_dict, args.keywords_file)
    else:
        # If end_index omitted, process only start_index
        end_index = args.end_index if args.end_index is not None else args.start_index
        main(
            args.start_index,
            end_index,
            run_scraper,
            run_llm,
            args.url_type_dict,
            args.keywords_file
        )

    time_end = time.time()
    time_elapsed = time_end - time_start

    # print time nicely IN HOURS, MINUTES, SECONDS	
    hours, rem = divmod(time_elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\n⏱️ Total time elapsed: {int(hours)}h {int(minutes)}m {int(seconds)}s\n")


