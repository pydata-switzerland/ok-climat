# Exploration Scripts

This folder contains early prototyping/exploration scripts written before the GovTech Hackathon, while getting familiar with the project and investigating what was possible.

**This code is not maintained and is not part of the documented pipeline** (see `pipeline/README.md` for the actual, maintained workflow). It's kept here for reference only — it may be out of date, may not run as-is, and shouldn't be relied on.

## Contents

- `scraper.py` — generic Selenium/HTML-parsing tutorial scraper, used to get familiar with web scraping (targets a demo sandbox site, not a real subsidy source)
- `scraper_okclimat.py` — earlier canton/francsenergie.ch-specific scraper prototype, superseded by `pipeline/scraper_okclimat.py`
- `test_ollama.py` — exploratory script using a local Ollama server (instead of OpenRouter) for LLM analysis
- `dict_ZH_PV.json`, `products.csv`, `ktzh_foerderprogramm_2026_results.json` — sample/scratch data used while prototyping
- `log_webScrabing.txt` — scratch log output from an early scraping run

## Web scraping resources

Getting started with this YouTube video: [Python Web Scraping Tutorial: Complete Guide 2026](https://www.youtube.com/watch?v=YrVRx2c72ig)
