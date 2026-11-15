# Minimal eval framework for the subsidy pipeline

This file holds the initial plan, approved at the start of the work on issue #11, and its revisions.
The newest revision comes first; the initial plan text at the bottom is kept as it was.

## Revised plan (2026-11-15), after the meeting with OK Climat

### What changed

- OK Climat proposed how the subsidy search should work and sent a Postgres script
  (`create_llm.txt`) with the tables `llm.subv_llm_data` (one row per subsidy type: prompt,
  keywords, standard case) and `llm.subv_llm_detail` (one row per subsidy / URL: markdown, LLM
  response, amount), plus a CSV with 236 PV rows (only `subv_id` and `search_url` filled).
- She does the scraping in **FME**, not with our Python scraper. Her MARKDOWN step uses
  docling / Python (OCR and image conversion off); her CALL_LLM step uses OpenRouter at low
  temperature. These are the two places our Python code plugs in.
- Results are to be stored in **Postgres**.
- She suggests the standard case for PV-EauCd may be **5 kW instead of 10 kW** (our open question in
  `ANNOTATION_GUIDELINES.md` §2).

Goals: (1) an isolated markdown function FME can call, (2) a reliable LLM analysis step OK Climat
can run, (3) keep an end-to-end Python tool in this repo (own scraping, or starting from FME's
text). The eval stays the first step, because it makes "reliable" measurable. New: the code is split
into functions with clear inputs and outputs, and the output must fit the database.

### Phases (one at a time)

**A. Postgres and OK Climat's tables** (relational schema, roles and grants, sequence / surrogate key,
foreign key)
- Install Postgres + pgAdmin, run `create_llm.txt` in the pgAdmin Query Tool, import the CSV
  (separator `;`, header on).
- Expected issues in the script: `GRANT ... TO llm_test` comes before `CREATE ROLE llm_test`; the
  `insert into llm.subv_llm_data` line has no `;`; only `PV` exists in `subv_llm_data`, so
  `PV-EauCd` rows would fail the foreign key.
- Explore with `SELECT`s; connect from Python (`psycopg` + `pandas.read_sql`).

**B. Finish the eval on files** (initial plan steps 2–5: test fixtures, baseline, experiment tracking)
- Freeze the markdown for the 19 golden IDs (`run_pipeline.py --step scraper`).
- Make `analyze_subsidies.py` callable as a function; parse the amount to a number.
- `pipeline/eval/evaluate.py` and `pipeline/eval/runs.csv`; record the baseline.
- Only 9 of the 19 golden IDs are in OK Climat's CSV (PV only), so the eval stays on our own files
  for now.

**C. Two callable functions** (separation of concerns, interface / contract, pure function, adapter)
- `to_markdown(source) -> str` for HTML or PDF, reusing the docling code in
  `pipeline/scrape_subsidies.py` (`convert_html_to_markdown`, `extract_text_from_pdf`), with OCR and
  image extraction off.
- `analyze(markdown, type_subv, contributor_name, ...) -> result`, with no file or database access
  inside; returns the amount, whether a subsidy exists, and the raw response.
- Thin wrappers: the existing CLI (files) and later a database runner. FME can call the functions
  through its Python caller or the CLI.

**D. Improve the LLM step against the baseline** (ablation, prompt engineering, structured output)
- One change per run, logged in `runs.csv`: fix the swapped m² factors and the PV-EauCd definition,
  add the contributor name, add guideline rules and worked examples, then structured JSON output plus
  a Python function for the standard-case amount.

**E. Read from and write to Postgres** (ETL, idempotency, change detection)
- Select rows where `markdown` is filled and the LLM result is empty, call `analyze`, write
  `llm_response`, `llm_base_value`, `llm_date`.
- Re-running creates no duplicates; for the yearly update, only re-run rows whose markdown changed
  (store a hash of the markdown).

**F. Schema points to discuss with OK Climat**
- The rules "one of subv_id / la_id is not null" and "not both valid_url and valid_pdf" could be
  `CHECK` constraints.
- `llm_base_value` is an integer but should allow "N/A", and CALL_LLM selects rows where it is null.
  One null cannot mean "not run yet", "not found" and "no subsidy (0)"; a status column would
  separate them.
- No model, prompt version or run date per result, so runs cannot be compared, and an overwritten
  prompt loses its history. `llm_prompt varchar(1000)` is short for a prompt with rules and examples.
- Room for structured fields (base, rate, threshold, cap, conditions), e.g. one JSON column.
- A markdown hash column for the yearly update; `text` instead of `varchar(500000)`.
- What `valid` means and how it links to the golden set.
- `subv_std '10 KW'` as text: a number plus a unit is easier to compute with.
- PV-EauCd 5 kW: if confirmed, update the guidelines and re-label the 8 thermal golden rows through
  `corrections.csv` (e.g. 2400 + 1000 × 5 = 7400).

## Status (2026-11-12)

- **Step 1 (golden dataset): done, with changes to the plan.**
  - The `subv_id` comes from joining the `exemples` and `all` sheets of `PV examples.xlsx`,
    not from `url_type_dict.json`.
  - 19 rows, not 22: Crans VD (2 rows, no `subv_id` in the database) and Luzern Solar-Impuls
    (5097, type `PV-Cnsl`, not processed by the pipeline) were removed. One negative case remains
    (5138).
  - Added beyond the plan: contributor name and level (from the OK Climat database export),
    `row_flags.csv` (flags, evidence and notes), `corrections.csv` and
    `golden_set_corrected.csv`, and `ANNOTATION_GUIDELINES.md` with open questions for OK Climat.
  - `golden_set_corrected.csv` is the version to use for evaluating the LLM step.
- **Steps 2–5: not started.**

### Ideas discussed on 2026-11-11, to fold into the plan later

- Turn the annotation guidelines into the LLM prompt: fixed steps (subsidy exists → is 10 kW
  eligible → calculate → list requirements and bonuses), the conversion rules, worked examples per
  calculation pattern, and the contributor name.
- Avoid data leakage: no few-shot examples taken from the golden set rows.
- Structured output (JSON with fixed fields) plus a Python function for the 10 kW calculation,
  instead of letting the LLM do the arithmetic. Validate the output with a schema.
- Experiment tracking: one predictions file per run, `evaluate.py` scores it overall and per flag
  (slicing), one line per run in `runs.csv`, compare with the baseline row by row, change one thing
  per run.
- Known bugs in `analyze_subsidies.py`, to fix as the first experiments after the baseline:
  swapped m² factors, wrong PV-EauCd definition ("photovoltaic water heating"), contributor name
  missing from the prompt.
- Check `run_pipeline.py` before step 2; it may already cover scraping the golden IDs.

---

## Context

Veronica wants to learn Data/ML/AI concepts on the OK Climat project, in small steps.
First goal: be able to tell whether a change (prompt, model, parsing) makes the output better or worse.
Today the only check is reading the printed LLM answer by eye.

Decisions made:
- Ground truth: the `exemples` sheet in `pipeline/PV examples.xlsx` (22 rows, column `10kW`). It may contain mistakes; we correct it as we go.
- The `all` sheet is used only for `subv_id`, `contributor`, `type_subv` and `site_url`. Its `fr_10kw` column is not used as ground truth.
- Scope: LLM step only, on scraped texts that are saved once and not re-scraped.

## Working mode

- Veronica writes and runs the code herself by default. Claude guides: explains what to write and why, reviews what she wrote, names the concept.
- Claude only edits files when Veronica explicitly hands a piece over.
- One step at a time, short explanations, stop after each step.

## What I found

- `exemples` has no `subv_id`. The pipeline is keyed on `subv_id` (from the `all` sheet, via `pipeline/extract_start_arguments.py` into `pipeline/url_type_dict.json`).
- Joining on URL + `type_subv` matches 15 of the 22 table rows automatically. 7 do not match: Luzern 76930, Aarau x2, Nesslau, Crans VD x2, canton AG.
- 2 table rows have `result = "no"` and an empty `10kW` (Luzern 76930 and Basel "Aktion Solarkraftwerk"). They mean "no subsidy here" and are kept as negative cases.
- SIG Genève matches `subv_id` 99999, a placeholder. It works as a key in the pipeline, so it is kept and flagged in `notes`.
- The LLM answer is saved as free text (`"** 3,250 CHF"`). A function that pulls the amount out already exists: `clean_total_subsidy` in `pipeline/combine_results.py`. It cannot be reused from another script yet, because importing that file would also run the whole CSV-writing script.

## Steps

### 1. Golden dataset (concepts: golden dataset, record linkage, negative examples)
- New script `pipeline/eval/build_golden_set.py`, written by Veronica with guidance. It:
  - reads the `exemples` sheet and `url_type_dict.json`,
  - joins on normalised URL (`url_start` or `url`) + `type_subv`,
  - writes `pipeline/eval/golden_set.csv`: `sub_id, type_subv, url, subsidy_exists, expected_10kW, notes`,
  - prints the rows it could not match.
- Unmatched rows get their `sub_id` from a small hand-made file `pipeline/eval/manual_ids.csv` (url, type_subv, sub_id) that the script also reads. So the result is reproducible and the manual part is visible.
- Negative cases: `subsidy_exists = no`, `expected_10kW = 0`.
- Commit script, manual file and output, so each later correction shows in git.

### 2. Freeze the inputs (concepts: test fixtures, reproducibility)
- Run the scraper once for the golden `sub_id`s: `python run_pipeline.py --sub_id <id> --step scraper`.
- Keep those `texts/subID_*.md` files unchanged. Note which IDs gave no text; that is a scraping failure, counted separately.

### 3. Make the output comparable (concepts: output parsing; later: structured output)
- Move `clean_total_subsidy` into a small module that other scripts can import, and add a number parser (`"3,250 CHF"` → `3250.0`).
- No prompt change yet, so the baseline measures the pipeline as it is today.

### 4. Eval script (concepts: eval, metric, accuracy)
- New file `pipeline/eval/evaluate.py`: read `golden_set.csv` and `results/*_analysis.json`, compare per `sub_id`.
- Correct = within 1 CHF of expected. For negative cases, correct = pipeline says 0 / no subsidy.
- Three outcomes per row: correct, wrong, missing.
- Print `n correct / n total` and a table of the wrong and missing rows.

### 5. Baseline and run log (concepts: baseline, regression testing, experiment tracking)
- Run the LLM step on the golden IDs, then `evaluate.py`.
- Append one line per run to `pipeline/eval/runs.csv`: date, git commit, model, score, free-text label.
- That first score is the baseline every later change is compared with.

## Later, not now
- Structured JSON output from the LLM instead of text parsing.
- Score per subsidy type, and error categories (wrong maths, wrong page, no subsidy found).
- Repeat runs to measure LLM run-to-run variation.
- Scraping eval (did we fetch the right page) and end-to-end eval.
- Run the eval automatically with pytest / CI.

## Verification
- Step 1: `golden_set.csv` has 22 rows (20 with an amount, 2 negative), no duplicate `sub_id`, every `sub_id` exists in `url_type_dict.json`. Re-running the script gives an identical file.
- Step 4: with the two existing results (118 → 3250, 522 → 720), `evaluate.py` reports 2 correct and 20 missing.
- Step 5: `runs.csv` has one baseline line; re-running without changes gives a similar score.
