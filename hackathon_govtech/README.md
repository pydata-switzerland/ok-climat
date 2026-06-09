# GovTech Hackathon Prototype

This folder contains the prototype developed during the GovTech Hackathon (Bern, May 2026) for extracting information about municipal solar subsidies in Switzerland.

The prototype focuses on two subsidy types:

* `PV` (photovoltaic installations)
* `PV-EauCd` (solar water heating)

The goal is to automatically:

1. Visit municipal websites.
2. Search for subsidy-related information using predefined keywords.
3. Extract relevant website and PDF content.
4. Convert the content to Markdown.
5. Use a Large Language Model (LLM) to analyse the extracted content.
6. Save the subsidy information in a structured JSON format.

---

# How the Pipeline Works

The workflow consists of two steps:

## Step 1: Web Scraping

Script:

```bash
scraper_okclimat.py
```

For a given subsidy ID (`sub_id`), the scraper:

* Reads the municipality URL from `url_type_dict.json`
* Identifies the subsidy type (`PV` or `PV-EauCd`)
* Searches the website for relevant keywords
* Searches for PDF documents linked from the website
* Filters PDFs based on keyword matches
* Converts relevant websites and PDFs into Markdown files
* Saves the extracted content into the `texts/` folder

Output:

```text
texts/
├── subID_118_site_1.md
├── subID_118_pdf_1.md
├── subID_118_pdf_1_metaData.txt
└── ...
```

---

## Step 2: LLM Analysis

Script:

```bash
test_openrouter.py
```

The LLM analysis:

* Reads all Markdown files associated with a given subsidy ID
* Sends the content to an LLM through OpenRouter
* Extracts structured subsidy information
* Estimates the subsidy amount for a 10 kW installation
* Saves the result as JSON

Output:

```text
results/
└── 118_analysis.json
```

Example output:

```json
{
    "sub_id": "118",
    "subsidy_type": "PV",
    "total_subsidy_10kW": "3600 CHF"
}
```

---

# Important Files

| File                  | Purpose                                                 |
| --------------------- | ------------------------------------------------------- |
| `url_type_dict.json`  | Maps subsidy IDs to municipality URLs and subsidy types |
| `keywords_dict.json`  | Defines keywords used to identify relevant content      |
| `scraper_okclimat.py` | Website and PDF scraping                                |
| `test_openrouter.py`  | LLM analysis                                            |
| `run_pipeline.py`     | Convenience script to run the full workflow             |

---

# OpenRouter Setup (Required for LLM Analysis)

The LLM analysis requires an OpenRouter account and API key.

## Create an OpenRouter Account

Create an account at:

https://openrouter.ai

Generate an API key from your account dashboard.

---

## Set the API Key

### macOS / Linux

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

### Windows (PowerShell)

```powershell
$env:OPENROUTER_API_KEY="your-api-key-here"
```

Verify that the variable is available:

```bash
echo $OPENROUTER_API_KEY
```

The LLM analysis script will automatically read this environment variable.

---

# Quick Start

The easiest way to run the prototype is with:

```bash
python run_pipeline.py
```

However, it is usually better to specify exactly what should be processed.

---

# Running the Pipeline

## Process a Single Subsidy ID

Run scraping only:

```bash
python run_pipeline.py --sub_id 118 --step scraper
```

Run LLM analysis only:

```bash
python run_pipeline.py --sub_id 118 --step llm
```

Run both steps:

```bash
python run_pipeline.py --sub_id 118 --step both
```

---

## Process Multiple Subsidies

Run scraping for subsidy IDs corresponding to indices 0–10 in `url_type_dict.json`:

```bash
python run_pipeline.py -ni 0 -nf 10 --step scraper
```

Run LLM analysis:

```bash
python run_pipeline.py -ni 0 -nf 10 --step llm
```

Run the complete workflow:

```bash
python run_pipeline.py -ni 0 -nf 10 --step both
```

---

## Process All Subsidies

The last index can be set to `-1`:

```bash
python run_pipeline.py -ni 0 -nf -1 --step both
```

This runs the pipeline for all entries in `url_type_dict.json`.

---

# Running Individual Scripts

Most users should use `run_pipeline.py`.

The individual scripts are useful for debugging.

## Run Only the Scraper

```bash
python scraper_okclimat.py --sub_id 118
```

---

## Run Only the LLM Analysis

```bash
python test_openrouter.py --sub_id 118
```

Note:

* The scraper must have been run first.
* Markdown files must already exist in the `texts/` folder.
* The `OPENROUTER_API_KEY` environment variable must be set.

---

# Output Folders

## texts/

Contains extracted website and PDF content converted to Markdown.

```text
texts/
├── subID_118_site_1.md
├── subID_118_pdf_1.md
├── subID_118_pdf_1_metaData.txt
└── ...
```

---

## pdfs/

Temporary PDF downloads.

```text
pdfs/
```

---

## results/

Final structured subsidy information.

```text
results/
├── 118_analysis.json
├── 522_analysis.json
└── ...
```

---

# Typical Workflow

For a new subsidy ID:

```bash
# Step 1: scrape website and PDFs
python run_pipeline.py --sub_id 118 --step scraper

# Step 2: analyse extracted content with the LLM
python run_pipeline.py --sub_id 118 --step llm
```

Or simply:

```bash
python run_pipeline.py --sub_id 118 --step both
```

This will create:

```text
texts/
results/
```

containing the extracted content and the final subsidy analysis.
