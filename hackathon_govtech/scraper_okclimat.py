from selectolax.lexbor import LexborHTMLParser
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import argparse
import requests
import pdfplumber
from pathlib import Path
from urllib.parse import urljoin
from docling.document_converter import DocumentConverter


# Script to scrape PV subsidy information for Swiss cantons

# Run example :

# python scraper_okclimat.py --sub_key sub_1

def scrape_page_for_keywords(url, keywords):
    """
    Visit a URL and search for keywords in the page content.
    Returns the raw HTML for further processing.
    """
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)  # Wait for page to load

        # Get the raw HTML (not just text)
        page_html = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, "body").text
        page_text_lower = page_text.lower()

        # Search for keywords (case-insensitive)
        found_keywords = [kw for kw in keywords if kw.lower() in page_text_lower]

        driver.quit()
        return found_keywords, page_html, page_text  # Return HTML for docling

    except Exception as e:
        print(f"[Page Scraping] Error visiting {url}: {e}")
        return [], None, None
    

def convert_html_to_markdown(html_content):
    """Convert HTML to Markdown using docling."""
    try:
        converter = DocumentConverter()
        # Create a temporary HTML file (docling expects a file path)
        temp_html_path = Path("temp_page.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        result = converter.convert(temp_html_path)
        markdown_content = result.document.export_to_markdown()

        # Clean up temp file
        temp_html_path.unlink(missing_ok=True)
        return markdown_content
    except Exception as e:
        print(f"[ERROR] Could not convert HTML to Markdown: {e}")
        return None

def save_page_text_to_file(sub_key, url, page_html, subsidy, row_num, found_keywords):
    """
    Save page HTML (converted to Markdown) to a file with metadata.
    """
    try:
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)
        url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:30]
        timestamp = int(time.time())
        base_filename = f"{sub_key}_{subsidy}_site_{timestamp}"
        md_path = texts_dir / f"{base_filename}.md"
        meta_path = texts_dir / f"{base_filename}_metaData.txt"

        # Convert HTML to Markdown
        markdown_content = convert_html_to_markdown(page_html)
        if not markdown_content:
            print("    ✗ Failed to convert HTML to Markdown")
            return None

        # Metadata header (YAML)
        metadata = f"""---
url: "{url}"
subsidy_type: "{subsidy}"
row_number: {row_num}
found_keywords: {found_keywords}
extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
---
"""

        # Write metadata to .txt file
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(metadata)

        # Write Markdown content to .md file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"    ✓ Saved Markdown to: {md_path}")
        print(f"    ✓ Saved metadata to: {meta_path}")
        return md_path

    except Exception as e:
        print(f"    ✗ Error saving Markdown: {e}")
        return None

def find_pdf_links_on_page(url):
    """
    Visit a URL and find all PDF links on the page.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        list: List of PDF URLs found on the page (absolute URLs, not relative)
    """
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Find all <a> tags with href attribute
        pdf_links = driver.find_elements(By.TAG_NAME, "a")
        
        pdf_urls = []
        for link in pdf_links:
            href = link.get_attribute("href")
            
            # Check if href contains .pdf
            if href and ".pdf" in href.lower():
                
                # Convert relative URLs to absolute URLs
                if href.startswith("http"):
                    pdf_urls.append(href)
                else:
                    # Handle relative URLs (e.g., "/documents/file.pdf")
                    absolute_url = urljoin(url, href)
                    pdf_urls.append(absolute_url)
        
        driver.quit()
        
        print(f"[PDF Discovery] Found {len(pdf_urls)} PDF(s) on {url}")
        for pdf_url in pdf_urls:
            print(f"  - {pdf_url}")
        
        return pdf_urls
        
    except Exception as e:
        print(f"[PDF Discovery] Error visiting {url}: {e}")
        return []


def download_pdf(pdf_url, output_dir="./pdfs"):
    """Download a PDF from URL and save locally.
    Args:
        pdf_url (str): Direct PDF URL
        output_dir (str): Directory to save PDFs
    Returns:
        Path to downloaded PDF file, or None if download failed
    """
    try:
        Path(output_dir).mkdir(exist_ok=True)
        
        # Download the url content (here a PDF) and stores it in a variable called response (raw bytes)
        response = requests.get(pdf_url, timeout=10)
        # Check if the request was successful
        response.raise_for_status()
        
        # Saved PDF name based on extracted filename from URL (use last part of URL or generate a unique name if URL does not end with a filename)
        filename = pdf_url.split("/")[-1] or f"subsidy_{int(time.time())}.pdf"
        # Saved pdf file path
        filepath = Path(output_dir) / filename
        
        # Save the PDF content to a file
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        return filepath
        
    except Exception as e:
        print(f"  [ERROR] Could not download PDF: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """Extract markdown text from a PDF file using Docling.
    Args:
        pdf_path (Path): Path to PDF file (locally saved pdf)    
    Returns:
        str: Extracted Markdown text, or None if extraction failed
    """
    try:
        # Disable OCR for faster processing
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        return result.document.export_to_markdown()
    except Exception as e:
        print(f"  [ERROR] Could not extract markdown from PDF via Docling: {e}")
        # Fallback to pdfplumber in case docling fails
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            return text
        except Exception:
            return None


def is_pdf_relevant(pdf_url, subsidy_keywords):
    """Check if a PDF is relevant by downloading it and searching for subsidy keywords.
    Args:
        pdf_url (str): URL of the PDF to check
        subsidy_keywords (list): Keywords related to the subsidy type (e.g., ["Fotovoltaik", "Photovoltaik", "Solar"])    
    Returns:
        tuple: (is_relevant: bool, pdf_path: Path or None)
    """
    
    print(f"  Checking: {pdf_url.split('/')[-1]}...")
    
    # Download PDF
    pdf_path = download_pdf(pdf_url)
    if not pdf_path:
        return False, None
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return False, pdf_path
    
    # Search for subsidy keywords
    # Convert text to lower case for case-insensitive matching
    text_lower = text.lower()
    # Check if any of the subsidy keywords are present in the text (also convert keywords to lower case for matching)
    found_keywords = [kw for kw in subsidy_keywords if kw.lower() in text_lower]
    
    # Print found keywords 
    if found_keywords:
        print(f"    ✓ Relevant! Found keywords: {found_keywords}")
        return True, pdf_path
    else:
        print(f"    ✗ Not relevant for this subsidy type")
        return False, pdf_path

def save_pdf_text_to_file(sub_key, pdf_path, pdf_url, subsidy, row_num):
    """
    Extract text from PDF and save it to a markdown file with metadata.
    Metadata is saved in a separate .txt file with _metaData.txt suffix.
    """
    try:
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)
        markdown_content = extract_text_from_pdf(pdf_path)
        if not markdown_content:
            print(f"    ✗ Could not extract text from PDF")
            return None

        pdf_info = pdf_path.stem[:30]
        timestamp = int(time.time())
        base_filename = f"{sub_key}_{subsidy}_site_{timestamp}"
        md_path = texts_dir / f"{base_filename}.md"
        meta_path = texts_dir / f"{base_filename}_metaData.txt"

        # Metadata header (YAML)
        metadata = f"""---
pdf_url: "{pdf_url}"
pdf_path: "{pdf_path}"
subsidy_type: "{subsidy}"
row_number: {row_num}
extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
---
"""

        # Write metadata to .txt file
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(metadata)

        # Write only the main content to .md file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"    ✓ Saved markdown to: {md_path}")
        print(f"    ✓ Saved metadata to: {meta_path}")
        return md_path

    except Exception as e:
        print(f"    ✗ Error saving markdown: {e}")
        return None

def load_keywords_from_json(subsidy_type):
    """Load keywords for a specific subsidy type from keywords_dict.json
    Args:
        subsidy_type (str): The subsidy type (e.g., "PV", "PV-EauCd")
    Returns:
        list: List of keywords for the subsidy type
    """
    try:
        with open("keywords_dict.json", "r", encoding="utf-8") as f:
            keywords_dict = json.load(f)
        
        if subsidy_type not in keywords_dict:
            print(f"Error: Subsidy type '{subsidy_type}' not found in keywords_dict.json")
            return []
        
        return keywords_dict[subsidy_type]
    
    except FileNotFoundError:
        print("Error: keywords_dict.json not found")
        return []
    except Exception as e:
        print(f"Error loading keywords: {e}")
        return []


def load_url_type_dict(url_type_dict_path):
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


def load_pv_urls_from_json(row_num=None):
    """Load URLs filtered by PV subsidy type from url_type_dict.json
    Args:
        row_num (int): If specified, return only the URL at this row index (1-indexed)
    Returns:
        dict: Dictionary with URL as key and subsidy type as value, or single URL dict if row_num specified
    """
    try:
        with open("url_type_dict.json", "r", encoding="utf-8") as f:
            url_type_dict = json.load(f)
        
        # Filter only PV entries
        pv_urls = {url: subsidy_type for url, subsidy_type in url_type_dict.items() if subsidy_type == "PV"}
        
        if not pv_urls:
            print("Error: No PV URLs found in url_type_dict.json")
            return {}
        
        # If row_num is specified, return only that entry
        if row_num is not None:
            urls_list = list(pv_urls.items())
            if row_num < 1 or row_num > len(urls_list):
                print(f"Error: row_num {row_num} is out of range (1-{len(urls_list)})")
                return {}
            
            url, subsidy_type = urls_list[row_num - 1]
            return {url: subsidy_type}
        
        return pv_urls
    
    except FileNotFoundError:
        print("Error: url_type_dict.json not found")
        return {}
    except Exception as e:
        print(f"Error loading URLs: {e}")
        return {}
    
def save_no_subsidy_found(sub_key, url, subsidy_type, row_num, keywords):
    """
    Save a file with 'no subsidy found' text and metadata when no relevant content is found.
    """
    try:
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)
        url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:30]
        timestamp = int(time.time())
        base_filename = f"{sub_key}_{subsidy_type}_site_{timestamp}"
        md_path = texts_dir / f"{base_filename}.md"
        meta_path = texts_dir / f"{base_filename}_metaData.txt"

        # Content for the Markdown file
        no_subsidy_content = "no subsidy found"

        # Metadata header (YAML)
        metadata = f"""---
url: "{url}"
subsidy_type: "{subsidy_type}"
row_number: {row_num}
found_keywords: []
extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
---
"""

        # Write metadata to .txt file
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(metadata)

        # Write 'no subsidy found' to the Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(no_subsidy_content)

        print(f"    ✓ Saved 'no subsidy found' to: {md_path}")
        print(f"    ✓ Saved metadata to: {meta_path}")
        return md_path

    except Exception as e:
        print(f"    ✗ Error saving 'no subsidy found' file: {e}")
        return None

def scrape_subsidy_page(sub_key, pv_urls, keywords, row_num):
    """Scrape the URLs to look for PDFs and relevant information."""
    for url, subsidy_type in pv_urls.items():
        print(f"\n{'='*60}")
        print(f"sub_key: {sub_key}")
        print(f"Subsidy Type: {subsidy_type}")
        print(f"URL: {url}")
        print(f"{'='*60}")

        # Flag to track if any relevant content was found
        found_relevant_content = False

        # STEP 1: Search for keywords on the page itself
        print(f"\n[STEP 1] Searching for keywords on the website...")
        print(f"Looking for: {keywords}")
        found_keywords_on_page, page_html, page_text = scrape_page_for_keywords(url, keywords)

        if found_keywords_on_page:
            print(f"✓ Found relevant keywords on the page: {found_keywords_on_page}")
            # Save the page content as Markdown
            print(f"\n[STEP 1.5] Saving page content as Markdown...")
            md_path = save_page_text_to_file(sub_key, url, page_html, subsidy_type, row_num, found_keywords_on_page)
            if md_path:
                print(f"✓ Markdown saved to: {md_path}")
                found_relevant_content = True
        else:
            print(f"✗ No relevant keywords found on the page")

        # STEP 2: Look for all PDFs on the site
        print(f"\n[STEP 2] Discovering PDFs on the website...")
        all_pdf_urls = find_pdf_links_on_page(url)

        if not all_pdf_urls:
            print(f"✗ No PDFs found on this page")
        else:
            print(f"✓ Found {len(all_pdf_urls)} PDF(s) total")

            # STEP 3: Filter PDFs by checking their content for subsidy keywords
            print(f"\n[STEP 3] Filtering PDFs by content (looking for: {keywords})...")
            relevant_pdfs = []

            for pdf_url in all_pdf_urls:
                is_relevant, pdf_path = is_pdf_relevant(pdf_url, keywords)
                if is_relevant:
                    relevant_pdfs.append((pdf_url, pdf_path))

            print(f"\n[RESULT] {len(relevant_pdfs)} out of {len(all_pdf_urls)} PDFs are relevant")

            if relevant_pdfs:
                print(f"\nRelevant PDFs:")
                for pdf_url, pdf_path in relevant_pdfs:
                    pdf_name = pdf_url.split('/')[-1]
                    print(f"   ✓ {pdf_name}")
                    print(f"    Local path: {pdf_path}")

                    # STEP 4: Save extracted text to file with metadata
                    print(f"\n  [STEP 4] Saving extracted text...")
                    txt_path = save_pdf_text_to_file(sub_key, pdf_path, pdf_url, subsidy_type, row_num)

                    if txt_path:
                        print(f"  ✓ Text saved successfully")
                        found_relevant_content = True
                    else:
                        print(f"  ✗ Failed to save text")

                    print()
            else:
                print(f"\n✗ No relevant PDFs found for this URL\n")

        # If no relevant content was found, save a "no subsidy found" file
        if not found_relevant_content:
            print(f"\n[NO SUBSIDY FOUND] Saving 'no subsidy found' file...")
            save_no_subsidy_found(sub_key, url, subsidy_type, row_num, keywords)


def main_scraper(sub_key, url_type_dict_path="url_type_dict.json"):
    """Main function to run the scraper for a given sub_key."""
    
    # Load the url_type_dict
    url_type_dict = load_url_type_dict(url_type_dict_path)
    if not url_type_dict:
        return

    # Check if the sub_key exists
    if sub_key not in url_type_dict:
        print(f"✗ Error: Subsidy key '{sub_key}' not found in {url_type_dict_path}.")
        print(f"Available keys: {list(url_type_dict.keys())}")
        return

    # Extract URL and subsidy type
    sub_info = url_type_dict[sub_key]
    url = sub_info["url"]
    subsidy_type = sub_info["type_subv"]

    print(f"🔎 Running scraper for:")
    print(f"   - Subsidy Key: {sub_key}")
    print(f"   - URL: {url}")
    print(f"   - Subsidy Type: {subsidy_type}")


    #===========================================================
    # Run web scraping

    # Load keywords for PV
    keywords = load_keywords_from_json(subsidy_type)
    if not keywords:
        print(f"Failed to load keywords for {subsidy_type}")
        return
    
    print(f"Loaded keywords for {subsidy_type}: {keywords}\n")

    scrape_subsidy_page(sub_key, {url: subsidy_type}, load_keywords_from_json(subsidy_type), 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape subsidy information for a given sub_key.")
    parser.add_argument("--sub_key", required=True, help="Subsidy key (e.g., sub_1, sub_2, etc.).")
    parser.add_argument("--url_type_dict", default="url_type_dict.json", help="Path to url_type_dict.json file.")

    args = parser.parse_args()
    main_scraper(args.sub_key, args.url_type_dict)













# from selectolax.lexbor import LexborHTMLParser
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
# import time
# import json
# import argparse
# import requests
# import pdfplumber
# from pathlib import Path
# from urllib.parse import urljoin
# from docling.document_converter import DocumentConverter

# # Script to scrape PV subsidy information for Swiss cantons
# # This script is inspired by this youtube video : https://www.youtube.com/watch?v=YrVRx2c72ig

# # For data retrieval :
# # Selenium to navigate websites
# # Selectolax to parse HTML
# # pdfplumber/PyPDF2 to read pdf

# # Run example :

# # python scraper_okclimat.py -r 1 -s PV

# def scrape_page_for_keywords(url, keywords):
#     """
#     Visit a URL and search for keywords in the page content.
    
#     Args:
#         url (str): The URL to scrape
#         keywords (list): Keywords to search for in the page text
        
#     Returns:
#         tuple: (found_keywords: list, page_text: str or None)
#     """
#     try:
#         options = Options()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(options=options)
#         driver.get(url)
        
#         # Wait for page to load
#         time.sleep(3)
        
#         # Get the page text
#         page_text = driver.find_element(By.TAG_NAME, "body").text
#         page_text_lower = page_text.lower()
        
#         # Search for keywords (case-insensitive)
#         found_keywords = [kw for kw in keywords if kw.lower() in page_text_lower]
        
#         driver.quit()
        
#         return found_keywords, page_text
        
#     except Exception as e:
#         print(f"[Page Scraping] Error visiting {url}: {e}")
#         return [], None

# def save_page_text_to_file(url, page_text, subsidy, row_num, found_keywords):
#     """
#     Save page text to a file with metadata when keywords are found.
#     Metadata is saved in a separate .txt file with _metaData.txt suffix.
#     """
#     try:
#         texts_dir = Path("./texts")
#         texts_dir.mkdir(exist_ok=True)
#         url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:30]
#         timestamp = int(time.time())
#         base_filename = f"{subsidy}_site_{url_safe}_row{row_num}_{timestamp}"
#         md_path = texts_dir / f"{base_filename}.md"
#         meta_path = texts_dir / f"{base_filename}_metaData.txt"

#         # Metadata header (YAML)
#         metadata = f"""---
# url: "{url}"
# subsidy_type: "{subsidy}"
# row_number: {row_num}
# found_keywords: {found_keywords}
# extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
# ---
# """

#         # Write metadata to .txt file
#         with open(meta_path, "w", encoding="utf-8") as f:
#             f.write(metadata)

#         # Write only the main content to .md file
#         with open(md_path, "w", encoding="utf-8") as f:
#             f.write(page_text)

#         print(f"    ✓ Saved page content to: {md_path}")
#         print(f"    ✓ Saved metadata to: {meta_path}")
#         return md_path

#     except Exception as e:
#         print(f"    ✗ Error saving page content: {e}")
#         return None

# def find_pdf_links_on_page(url):
#     """
#     Visit a URL and find all PDF links on the page.
    
#     Args:
#         url (str): The URL to scrape
        
#     Returns:
#         list: List of PDF URLs found on the page (absolute URLs, not relative)
#     """
#     try:
#         options = Options()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(options=options)
#         driver.get(url)
        
#         # Wait for page to load
#         time.sleep(3)
        
#         # Find all <a> tags with href attribute
#         pdf_links = driver.find_elements(By.TAG_NAME, "a")
        
#         pdf_urls = []
#         for link in pdf_links:
#             href = link.get_attribute("href")
            
#             # Check if href contains .pdf
#             if href and ".pdf" in href.lower():
                
#                 # Convert relative URLs to absolute URLs
#                 if href.startswith("http"):
#                     pdf_urls.append(href)
#                 else:
#                     # Handle relative URLs (e.g., "/documents/file.pdf")
#                     absolute_url = urljoin(url, href)
#                     pdf_urls.append(absolute_url)
        
#         driver.quit()
        
#         print(f"[PDF Discovery] Found {len(pdf_urls)} PDF(s) on {url}")
#         for pdf_url in pdf_urls:
#             print(f"  - {pdf_url}")
        
#         return pdf_urls
        
#     except Exception as e:
#         print(f"[PDF Discovery] Error visiting {url}: {e}")
#         return []


# def download_pdf(pdf_url, output_dir="./pdfs"):
#     """Download a PDF from URL and save locally.
#     Args:
#         pdf_url (str): Direct PDF URL
#         output_dir (str): Directory to save PDFs
#     Returns:
#         Path to downloaded PDF file, or None if download failed
#     """
#     try:
#         Path(output_dir).mkdir(exist_ok=True)
        
#         # Download the url content (here a PDF) and stores it in a variable called response (raw bytes)
#         response = requests.get(pdf_url, timeout=10)
#         # Check if the request was successful
#         response.raise_for_status()
        
#         # Saved PDF name based on extracted filename from URL (use last part of URL or generate a unique name if URL does not end with a filename)
#         filename = pdf_url.split("/")[-1] or f"subsidy_{int(time.time())}.pdf"
#         # Saved pdf file path
#         filepath = Path(output_dir) / filename
        
#         # Save the PDF content to a file
#         with open(filepath, "wb") as f:
#             f.write(response.content)
        
#         return filepath
        
#     except Exception as e:
#         print(f"  [ERROR] Could not download PDF: {e}")
#         return None


# def extract_text_from_pdf(pdf_path):
#     """Extract markdown text from a PDF file using Docling.
#     Args:
#         pdf_path (Path): Path to PDF file (locally saved pdf)    
#     Returns:
#         str: Extracted Markdown text, or None if extraction failed
#     """
#     try:
#         # Disable OCR for faster processing
#         converter = DocumentConverter(ocr=False)
#         result = converter.convert(pdf_path)
#         return result.document.export_to_markdown()
#     except Exception as e:
#         print(f"  [ERROR] Could not extract markdown from PDF via Docling: {e}")
#         # Fallback to pdfplumber in case docling fails
#         try:
#             with pdfplumber.open(pdf_path) as pdf:
#                 text = "\n".join([page.extract_text() or "" for page in pdf.pages])
#             return text
#         except Exception:
#             return None


# def is_pdf_relevant(pdf_url, subsidy_keywords):
#     """Check if a PDF is relevant by downloading it and searching for subsidy keywords.
#     Args:
#         pdf_url (str): URL of the PDF to check
#         subsidy_keywords (list): Keywords related to the subsidy type (e.g., ["Fotovoltaik", "Photovoltaik", "Solar"])    
#     Returns:
#         tuple: (is_relevant: bool, pdf_path: Path or None)
#     """
    
#     print(f"  Checking: {pdf_url.split('/')[-1]}...")
    
#     # Download PDF
#     pdf_path = download_pdf(pdf_url)
#     if not pdf_path:
#         return False, None
    
#     # Extract text
#     text = extract_text_from_pdf(pdf_path)
#     if not text:
#         return False, pdf_path
    
#     # Search for subsidy keywords
#     # Convert text to lower case for case-insensitive matching
#     text_lower = text.lower()
#     # Check if any of the subsidy keywords are present in the text (also convert keywords to lower case for matching)
#     found_keywords = [kw for kw in subsidy_keywords if kw.lower() in text_lower]
    
#     # Print found keywords 
#     if found_keywords:
#         print(f"    ✓ Relevant! Found keywords: {found_keywords}")
#         return True, pdf_path
#     else:
#         print(f"    ✗ Not relevant for this subsidy type")
#         return False, pdf_path

# def save_pdf_text_to_file(pdf_path, pdf_url, subsidy, row_num):
#     """
#     Extract text from PDF and save it to a markdown file with metadata.
#     Metadata is saved in a separate .txt file with _metaData.txt suffix.
#     """
#     try:
#         texts_dir = Path("./texts")
#         texts_dir.mkdir(exist_ok=True)
#         markdown_content = extract_text_from_pdf(pdf_path)
#         if not markdown_content:
#             print(f"    ✗ Could not extract text from PDF")
#             return None

#         pdf_info = pdf_path.stem[:30]
#         timestamp = int(time.time())
#         base_filename = f"{subsidy}_pdf_{pdf_info}_row{row_num}_{timestamp}"
#         md_path = texts_dir / f"{base_filename}.md"
#         meta_path = texts_dir / f"{base_filename}_metaData.txt"

#         # Metadata header (YAML)
#         metadata = f"""---
# pdf_url: "{pdf_url}"
# pdf_path: "{pdf_path}"
# subsidy_type: "{subsidy}"
# row_number: {row_num}
# extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
# ---
# """

#         # Write metadata to .txt file
#         with open(meta_path, "w", encoding="utf-8") as f:
#             f.write(metadata)

#         # Write only the main content to .md file
#         with open(md_path, "w", encoding="utf-8") as f:
#             f.write("# Extracted PDF Content\n\n")
#             f.write(markdown_content)

#         print(f"    ✓ Saved markdown to: {md_path}")
#         print(f"    ✓ Saved metadata to: {meta_path}")
#         return md_path

#     except Exception as e:
#         print(f"    ✗ Error saving markdown: {e}")
#         return None

# def load_keywords_from_json(subsidy_type):
#     """Load keywords for a specific subsidy type from keywords_dict.json
#     Args:
#         subsidy_type (str): The subsidy type (e.g., "PV", "PV-EauCd")
#     Returns:
#         list: List of keywords for the subsidy type
#     """
#     try:
#         with open("keywords_dict.json", "r", encoding="utf-8") as f:
#             keywords_dict = json.load(f)
        
#         if subsidy_type not in keywords_dict:
#             print(f"Error: Subsidy type '{subsidy_type}' not found in keywords_dict.json")
#             return []
        
#         return keywords_dict[subsidy_type]
    
#     except FileNotFoundError:
#         print("Error: keywords_dict.json not found")
#         return []
#     except Exception as e:
#         print(f"Error loading keywords: {e}")
#         return []

# def load_pv_urls_from_json(row_num=None):
#     """Load URLs filtered by PV subsidy type from url_type_dict.json
#     Args:
#         row_num (int): If specified, return only the URL at this row index (1-indexed)
#     Returns:
#         dict: Dictionary with URL as key and subsidy type as value, or single URL dict if row_num specified
#     """
#     try:
#         with open("url_type_dict.json", "r", encoding="utf-8") as f:
#             url_type_dict = json.load(f)
        
#         # Filter only PV entries
#         pv_urls = {url: subsidy_type for url, subsidy_type in url_type_dict.items() if subsidy_type == "PV"}
        
#         if not pv_urls:
#             print("Error: No PV URLs found in url_type_dict.json")
#             return {}
        
#         # If row_num is specified, return only that entry
#         if row_num is not None:
#             urls_list = list(pv_urls.items())
#             if row_num < 1 or row_num > len(urls_list):
#                 print(f"Error: row_num {row_num} is out of range (1-{len(urls_list)})")
#                 return {}
            
#             url, subsidy_type = urls_list[row_num - 1]
#             return {url: subsidy_type}
        
#         return pv_urls
    
#     except FileNotFoundError:
#         print("Error: url_type_dict.json not found")
#         return {}
#     except Exception as e:
#         print(f"Error loading URLs: {e}")
#         return {}

# def scrape_subsidy_page(pv_urls, keywords, row_num):
#     """Scrape the URLs to look for PDFs and relevant information. 
#     Args:
#         pv_urls (dict): Dictionary containing URL and subsidy type pairs
#         keywords (list): Keywords to filter PDFs and page content
#         row_num (int): Row number (1-indexed) for metadata
#     Returns: 
#         None
#     """
    
#     # Check each URL
#     for url, subsidy_type in pv_urls.items():

#         print(f"\n{'='*60}")
#         print(f"Subsidy Type: {subsidy_type}")
#         print(f"Row Number: {row_num}")
#         print(f"URL: {url}")
#         print(f"{'='*60}")

#         # STEP 1: Search for keywords on the page itself
#         print(f"\n[STEP 1] Searching for keywords on the website...")
#         print(f"Looking for: {keywords}")
#         found_keywords_on_page, page_text = scrape_page_for_keywords(url, keywords)
        
#         if found_keywords_on_page:
#             print(f"✓ Found relevant keywords on the page: {found_keywords_on_page}")
            
#             # Save the page content to a text file
#             print(f"\n[STEP 1.5] Saving page content...")
#             txt_path = save_page_text_to_file(url, page_text, subsidy_type, row_num, found_keywords_on_page)
#             if txt_path:
#                 print(f"✓ Page content saved to: {txt_path}")
#         else:
#             print(f"✗ No relevant keywords found on the page")

#         # STEP 2: Look for all PDFs on the site
#         print(f"\n[STEP 2] Discovering PDFs on the website...")
#         all_pdf_urls = find_pdf_links_on_page(url)
        
#         if not all_pdf_urls:
#             print(f"✗ No PDFs found on this page")
#             continue
        
#         print(f"✓ Found {len(all_pdf_urls)} PDF(s) total")
        
#         # STEP 3: Filter PDFs by checking their content for subsidy keywords
#         print(f"\n[STEP 3] Filtering PDFs by content (looking for: {keywords})...")
#         relevant_pdfs = []
        
#         for pdf_url in all_pdf_urls:
#             is_relevant, pdf_path = is_pdf_relevant(pdf_url, keywords)
#             if is_relevant:
#                 relevant_pdfs.append((pdf_url, pdf_path))
        
#         print(f"\n[RESULT] {len(relevant_pdfs)} out of {len(all_pdf_urls)} PDFs are relevant")
        
#         if relevant_pdfs:
#             print(f"\nRelevant PDFs:")
#             for pdf_url, pdf_path in relevant_pdfs:
#                 pdf_name = pdf_url.split('/')[-1]
#                 print(f"   ✓ {pdf_name}")
#                 print(f"    Local path: {pdf_path}")
                
#                 # STEP 4: Save extracted text to file with metadata
#                 print(f"\n  [STEP 4] Saving extracted text...")
#                 txt_path = save_pdf_text_to_file(pdf_path, pdf_url, subsidy_type, row_num)
                
#                 if txt_path:
#                     print(f"  ✓ Text saved successfully")
#                 else:
#                     print(f"  ✗ Failed to save text")
                
#                 print()
#         else:
#             print(f"\n✗ No relevant PDFs found for this URL\n")

# def main_scraper(row_num, verbose, subsidy_type):
#     """Main function to run the web scraping process for a specific row
#     Args:
#         row_num (int): The row number (1-indexed) to scrape from url_type_dict.json
#         verbose (bool): Whether to print detailed debug information during the scraping process
#         subsidy_type (str): The subsidy type to load keywords for (e.g., "PV")
#     Returns:
#         None
#     """

#     #===========================================================
#     # Run web scraping

#     print(f"\nRunning web-scraping in verbose={verbose} with the input arguments: ")
#     print(f"- Row number  : {row_num}")
#     print(f"- Subsidy type : {subsidy_type}")

#     # Load keywords for PV
#     keywords = load_keywords_from_json(subsidy_type)
#     if not keywords:
#         print(f"Failed to load keywords for {subsidy_type}")
#         return
    
#     print(f"Loaded keywords for {subsidy_type}: {keywords}\n")

#     # Run the subsidy page scraper 
#     pv_urls = load_pv_urls_from_json(row_num)

#     if pv_urls:
#         scrape_subsidy_page(pv_urls, keywords, row_num)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Scrape subsidy information for a specific URL")
#     parser.add_argument("-r", "--row_num", type=int, default=None, help="Row number (1-indexed) of PV URL to scrape")
#     parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed debug information", default=False)
#     parser.add_argument("-s", "--subsidy_type", type=str, default="PV", help="Subsidy type to load keywords for (default: PV)")
#     args = parser.parse_args()
    
#     vars_dict = vars(args)

#     main_scraper(vars_dict["row_num"], vars_dict["verbose"], vars_dict["subsidy_type"])