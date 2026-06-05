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


# Global dictionary to track file counts per sub_id
file_counters = {}

# Script to scrape PV subsidy information for Swiss cantons

# Run example :

# python scraper_okclimat.py --sub_key sub_1

def scrape_page_for_keywords(url, keywords):
    """
    Visit a URL and search for keywords in the page content.
    Returns the raw HTML for further processing.
    """
    try:
        # Set up Selenium with headless Chrome
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # This allows the page to load with a timeout of 10 seconds, and waits until the body tag is present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Get the raw HTML (not just text)
        page_html = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, "body").text
        page_text_lower = page_text.lower()

        # Search for keywords (case-insensitive)
        found_keywords = [kw for kw in keywords if kw.lower() in page_text_lower]

        # Close the browser
        driver.quit()

        return found_keywords, page_html, page_text  # Return HTML for docling

    except Exception as e:
        print(f"[Page Scraping] Error visiting {url}: {e}")
        return [], None, None
    

def convert_html_to_markdown(html_content):
    """Convert HTML to Markdown using docling."""
    try:

        # Create a DocumentConverter instance 
        converter = DocumentConverter()
        
        # Create a temporary HTML file (docling expects a file path)
        temp_html_path = Path("temp_page.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Convert the HTML file to Markdown
        result = converter.convert(temp_html_path)
        markdown_content = result.document.export_to_markdown()

        # Clean up temp file
        temp_html_path.unlink(missing_ok=True)
        
        return markdown_content
    
    except Exception as e:
        print(f"[ERROR] Could not convert HTML to Markdown: {e}")
        return None

def save_page_text_to_file(url, page_html, subsidy_type, sub_id, file_number, found_keywords):
    """
    Save ONLY the page content (as Markdown) to a file.
    Filename: subID_{sub_id}_site_{file_number}.md
    """
    try:

        # Create texts directory to hold the extracted text files
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)

        # Create a markdown filename based on the sub_id and file number (e.g., subID_2041_site_1.md)
        base_filename = f"subID_{sub_id}_site_{file_number}"
        md_path = texts_dir / f"{base_filename}.md"

        # Convert HTML to Markdown
        markdown_content = convert_html_to_markdown(page_html)
        
        # If conversion fails, return None and print an error message
        if not markdown_content:
            print("✗ Failed to convert HTML to Markdown")
            return None

        # Write ONLY the Markdown content to the file 
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✓ Saved Markdown to: {md_path}")

        # Save metadata to a separate file
        save_meta_data_to_file(base_filename, url, subsidy_type, sub_id, found_keywords)

        return md_path

    except Exception as e:
        print(f"✗ Error saving Markdown: {e}")
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
        # Set up Selenium with headless Chrome
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        # Visit the URL and wait for the page to load
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
 
        # Find all <a> tags with href attribute
        pdf_links = driver.find_elements(By.TAG_NAME, "a")
        
        # List to store discovered PDF URLs
        pdf_urls = []
        
        # Run through all links and check if they contain .pdf in the href attribute
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
        
        # Close the browser
        driver.quit()
        
        print(f"[PDF Discovery] Found {len(pdf_urls)} PDF(s) on {url}")
        for pdf_url in pdf_urls:
            print(f"  - {pdf_url}")
        
        return pdf_urls
        
    except Exception as e:
        print(f"[PDF Discovery] Error visiting {url}: {e}")
        return []


def download_pdf(pdf_url, counter=0, output_dir="./pdfs"):
    """Download a PDF from URL and save locally.
    Args:
        pdf_url (str): Direct PDF URL
        output_dir (str): Directory to save PDFs
    Returns:
        Path to downloaded PDF file, or None if download failed
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Download the url content (here a PDF) and stores it in a variable called response (raw bytes)
        response = requests.get(pdf_url, stream=True, timeout=10)
        # Check if the request was successful
        response.raise_for_status()
        
        # Saved PDF name based on extracted filename from URL (use last part of URL or generate a unique name if URL does not end with a filename)
        filename = pdf_url.split("/")[-1] or f"subsidy_{int(time.time())}.pdf"
        # filename = f"subsidy_PDF_{counter}.pdf"

        # Saved pdf file path
        filepath = Path(output_dir) / filename

        # Write the PDF content to a local file
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
        
    except Exception as e:
        print(f"  [ERROR] Could not download PDF: {e}")
        return None
        
    except Exception as e:
        print(f"  [ERROR] Could not download PDF: {e}")
        return None


def extract_text_from_pdf(pdf_path, as_markdown=False):
    """
    Extract text from a PDF file.
    If as_markdown is True, use Docling to extract Markdown.
    If False, use pdfplumber to extract plain text (faster).
    """
    pdf_path = Path(pdf_path)

    # 1. Check if the file is a valid PDF (by extension or magic bytes)
    is_pdf = False
    try:
        # Check file extension
        if pdf_path.suffix.lower() == ".pdf":
            is_pdf = True
        # Check magic bytes (first 4 bytes should be %PDF)
        with open(pdf_path, "rb") as f:
            header = f.read(4)
            if header == b"%PDF":
                is_pdf = True
    except Exception as e:
        print(f"  [WARNING] Could not verify PDF: {e}")

    if not is_pdf:
        print(f"  [WARNING] File does not appear to be a PDF: {pdf_path}")
        # Try pdfplumber anyway (might work for some non-PDF files)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            return text
        except Exception as e:
            print(f"  [ERROR] Could not extract text: {e}")
            return None

    # 2. Try Docling (with fallback to pdfplumber)
    if as_markdown:
        try:
            converter = DocumentConverter()
            # Try to force PDF format (if Docling supports it)
            # Note: Docling doesn't currently support forcing the format, but we can try passing the path as a string
            result = converter.convert(str(pdf_path.absolute()))
            return result.document.export_to_markdown()
        except Exception as e:
            print(f"  [ERROR] Docling failed (likely filetype issue): {e}")
            # Fall through to pdfplumber

    # 3. Fallback to pdfplumber (for plain text or if Docling fails)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        # If as_markdown is True, wrap the text in Markdown formatting
        if as_markdown:
            return f"# Extracted Text\n\n{text}"
        return text
    except Exception as e:
        print(f"  [ERROR] pdfplumber failed: {e}")
        return None


def is_pdf_relevant(pdf_url, subsidy_keywords, counter=0):
    """
    Check if a PDF is relevant by downloading it and searching for subsidy keywords.
    Only extract plain text for speed.
    """

    print(f"Checking this pdf url: {pdf_url}...")

    # Step 1: Download the PDF to a local file
    pdf_path = download_pdf(pdf_url, counter)
    if not pdf_path:
        return False, None, None

    # Step 2: Extract text from the PDF (as plain text for speed)
    text = extract_text_from_pdf(pdf_path, as_markdown=False)
    if not text:
        return False, pdf_path
    # Convert text to lowercase for case-insensitive search
    text_lower = text.lower()
    
    # Step 3: Search for subsidy keywords (case-insensitive)
    found_keywords = [kw for kw in subsidy_keywords if kw.lower() in text_lower]
    if found_keywords:
        print(f"✓ Relevant! Found keywords: {found_keywords}")
        return True, pdf_path, found_keywords
    else:
        print(f"✗ Not relevant for this subsidy type")
        return False, pdf_path, found_keywords
    

def save_pdf_text_to_file(pdf_path, sub_id, file_number, url=None, subsidy_type=None, keywords=None):
    """
    Save ONLY the PDF content (as Markdown) to a file.
    Only now do the slow Markdown extraction.
    """
    try:
        # Create texts directory to hold the extracted text files
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)

        # Create a markdown filename based on the sub_id and file number (e.g., subID_2041_pdf_1.md)
        base_filename = f"subID_{sub_id}_pdf_{file_number}"
        md_path = texts_dir / f"{base_filename}.md"

        # Convert pdf to markdown (this is the slow step, so we only do it if the PDF is relevant)
        markdown_content = extract_text_from_pdf(pdf_path, as_markdown=True)
        if not markdown_content:
            print(f"✗ Could not extract text from PDF")
            return None

        # Save the extracted Markdown content to a file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✓ Saved Markdown to: {md_path}")

        # Save metadata to a separate file
        save_meta_data_to_file(base_filename, url, subsidy_type, sub_id, keywords)

        return md_path

    except Exception as e:
        print(f"✗ Error saving Markdown: {e}")
        return None


def save_meta_data_to_file(base_filename, url, subsidy_type, sub_id, found_keywords):
    """Save metadata to a .txt file with the same base filename as the Markdown file."""
    try:
        # Create texts directory if it doesn't exist
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)

        # Create a metadata filename based on the base filename (e.g., subID_2041_site_1_metaData.txt)
        meta_path = texts_dir / f"{base_filename}_metaData.txt"

        # Create metadata content
        metadata = f"""
--- Metadata---
url: "{url}"
subsidy_type: "{subsidy_type}"
sub_id: "{sub_id}"
found_keywords: {found_keywords}
extracted_at: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
---------------
"""
        # Save metadata to the file
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(metadata)
        print(f"✓ Saved metadata to: {meta_path}")
        
        return meta_path  

    except Exception as e:
        print(f"✗ Error saving metadata: {e}")
        return None
    

def save_no_subsidy_found(url, subsidy_type, sub_id, keywords):
    """
    Save a file with 'no subsidy found' text and metadata when no relevant content is found.
    Filename: subID_{sub_id}_site_1.md
    """
    try:
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)

        base_filename = f"subID_{sub_id}_site_1"
        md_path = texts_dir / f"{base_filename}.md"

        # Content for the Markdown file
        no_subsidy_content = "no subsidy found"

        # Write 'no subsidy found' to the Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(no_subsidy_content)
        print(f"✓ Saved 'no subsidy found' to: {md_path}")

        # Save metadata to a separate file
        save_meta_data_to_file(base_filename, url, subsidy_type, sub_id, keywords)
  
        return md_path

    except Exception as e:
        print(f"✗ Error saving 'no subsidy found' file: {e}")
        return None

def scrape_subsidy_page(url_type_dict, keywords_dict, sub_id):
    """
    Scrape the URL for a given sub_id and save the results.
    """
    
    # Check if sub_id exists in url_type_dict
    if sub_id not in url_type_dict:
        print(f"✗ Error: Subsidy ID '{sub_id}' not found in url_type_dict.")
        return

    # Extract the URL and subsidy type for the given sub_id
    sub_info = url_type_dict[sub_id]
    url = sub_info["site_url"]
    subsidy_type = sub_info["type_subv"]

    # Load keywords for the subsidy type
    keywords = keywords_dict.get(subsidy_type, [])
    if not keywords:
        print(f"✗ Error: No keywords found for subsidy type '{subsidy_type}'.")
        return

    # Find out if the URL is valid and get the content type, i.e. is it a PDF or a website?
    content_type = ""
    try:
        # Make a request to the URL to check if it's accessible and to get the content type
        response = requests.get(url)
        content_type = response.headers.get("Content-Type", "")
    except Exception as e:
        print(f"✗ Error accessing {url}: {e}")
        save_no_subsidy_found(url, subsidy_type, sub_id, keywords)
        return
    print(f"Content-Type of the URL: {content_type}")

    # Set a flag if the URL points directly to a PDF based on the content type
    flag_pdf = False
    if "pdf" in content_type.lower():
        flag_pdf = True
        print(f"\n[INFO] The URL {url} for sub_id {sub_id} points directly to a PDF document.")

    # Initialize file counters for this sub_id, it is used to create unique filenames for each saved pdf file associated with one sub_id 
    if sub_id not in file_counters:
        file_counters[sub_id] = {"site": 0, "pdf": 0}

    # Flag to track if any relevant content was found
    found_relevant_content = False

    #--------------------------------------------------------------------------------------
    # Extract info from web site (if the URL does not point directly to a PDF)
    #--------------------------------------------------------------------------------------

    if flag_pdf == False:

        #--------------------------------------------------------------------------------------
        # STEP 1: Search for keywords on the page itself 
        #--------------------------------------------------------------------------------------
        
        print(f"\n[STEP 1] Searching for keywords on the website...")
        print(f"Looking for: {keywords}")

        # Visit the URL and search for keywords in the page content (case-insensitive)
        time_keywords_start = time.time()
        found_keywords_on_page, page_html, page_text = scrape_page_for_keywords(url, keywords)
        time_keywords_end = time.time()
        print(f"\nKeyword search took {time_keywords_end - time_keywords_start:.2f} seconds")

        # If keywords are found on the page, save the page content as Markdown
        if found_keywords_on_page:

            #--------------------------------------------------------------------------------------
            # STEP 1.5 : Save web page content as Markdown 
            #--------------------------------------------------------------------------------------
            
            print(f"✓ Found relevant keywords on the page: {found_keywords_on_page}")
            
            # Increment site counter
            file_counters[sub_id]["site"] += 1
            
            # Save the page content as Markdown
            print(f"\n[STEP 1.5] Saving page content as Markdown...")
            
            # Save the page content as Markdown 
            time_save_start = time.time()
            md_path = save_page_text_to_file(
                url, page_html, subsidy_type, sub_id,
                file_counters[sub_id]["site"], found_keywords_on_page
            )
            time_save_end = time.time()
            print(f"Saving page content took {time_save_end - time_save_start:.2f} seconds")

            # If the Markdown was saved successfully, mark that we found relevant content
            if md_path:
                found_relevant_content = True

        else:
            print(f"✗ No relevant keywords found on the page")

        # --------------------------------------------------------------------------------------
        # STEP 2: Look for all PDFs on the site
        # --------------------------------------------------------------------------------------

        print(f"\n[STEP 2] Discovering PDFs on the website...")

        # Use Selenium to find all PDF links on the page and convert relative URLs to absolute URLs
        time_find_pdfs_start = time.time()
        all_pdf_urls = find_pdf_links_on_page(url)
        time_find_pdfs_end = time.time()
        print(f"PDF discovery took {time_find_pdfs_end - time_find_pdfs_start:.2f} seconds")

        if not all_pdf_urls:
            print(f"✗ No PDFs found on this page")
        
        else:
            print(f"✓ Found {len(all_pdf_urls)} PDF(s) total")
    
            # Remove duplicates and print the unique PDF URLs
            unique_pdf_urls = list(set(all_pdf_urls))
            print(f"✓ {len(unique_pdf_urls)} unique PDF(s) after removing duplicates")
            for pdf_url in unique_pdf_urls:
                print(f"  - {pdf_url}")

            # --------------------------------------------------------------------------------------
            # STEP 3: Filter PDFs by checking their content for subsidy keywords
            # --------------------------------------------------------------------------------------

            print(f"\n[STEP 3] Filtering PDFs by content (looking for: {keywords})...")
            
            # List to store relevant PDFs and their local paths
            relevant_pdfs = []

            # Run through all discovered PDF URLs
            counter = 0  # Counter to create unique filenames for downloaded PDFs
            for pdf_url in unique_pdf_urls:

                counter += 1

                print(f"\nChecking PDF: {pdf_url}")
                
                # Check if the PDF is relevant by downloading it and searching for subsidy keywords
                time_relevance_start = time.time()
                is_relevant, pdf_path, found_keywords = is_pdf_relevant(pdf_url, keywords, counter)
                time_relevance_end = time.time()
                print(f"Relevance check took {time_relevance_end - time_relevance_start:.2f} seconds")

                # If the PDF is relevant, add it to the list of relevant PDFs along with its local path
                if is_relevant:
                    relevant_pdfs.append((pdf_url, pdf_path, found_keywords))

            print(f"\n[RESULT] {len(relevant_pdfs)} out of {len(unique_pdf_urls)} PDFs are relevant")
            print(f"Relevant PDFs:")
            for pdf_url, pdf_path, found_keywords in relevant_pdfs:
                #pdf_name = pdf_url.split('/')[-1]
                # print(f"   ✓ {pdf_name}")
                print(f"\n    URL: {pdf_url}")
                print(f"    Local path: {pdf_path}")
                print(f"    Found keywords: {found_keywords}")

            # If there are relevant PDFs, print their URLs and local paths
            if relevant_pdfs:

                # --------------------------------------------------------------------------------------
                # STEP 4: For each relevant PDF, save the extracted text to a file with metadata
                # --------------------------------------------------------------------------------------

                print(f"\n[STEP 4] Saving extracted text from PDFs...")

                print(f"\nRelevant PDFs:")
                for pdf_url, pdf_path, found_keywords in relevant_pdfs:
                    
                    pdf_name = pdf_url.split('/')[-1]
                    print(f"   ✓ {pdf_name}")
                    print(f"    URL: {pdf_url}")
                    print(f"    Local path: {pdf_path}")
                    print(f"    Found keywords: {found_keywords}")

                    # Increment PDF counter
                    file_counters[sub_id]["pdf"] += 1
                    
                    # Save extracted text to markdown file with metadata
                    time_save_start = time.time()
                    txt_path = save_pdf_text_to_file(pdf_path, sub_id, file_counters[sub_id]["pdf"], url=pdf_url, subsidy_type=subsidy_type, keywords=found_keywords)  
                    time_save_end = time.time()
                    print(f"    Saving extracted text took {time_save_end - time_save_start:.2f} seconds")

                    if txt_path:
                        found_relevant_content = True
                    else:
                        print(f"✗ Failed to save text")

                    print()
            else:
                print(f"\n✗ No relevant PDFs found for this URL\n")

    #--------------------------------------------------------------------------------------
    # If the URL points directly to a PDF, check if it's relevant and save the text if it is
    #--------------------------------------------------------------------------------------

    if flag_pdf == True:

        print(f"\n[PDF URL] The URL points directly to a PDF. Checking relevance...\n")

        # Check if the PDF is relevant by downloading it and searching for subsidy keywords
        time_relevance_start = time.time()
        is_relevant, pdf_path, found_keywords = is_pdf_relevant(url, keywords)
        time_relevance_end = time.time()
        print(f"Relevance check took {time_relevance_end - time_relevance_start:.2f} seconds")

        # If the PDF is relevant, save the extracted text to a file with metadata
        if is_relevant:
            
            print(f"\n✓ The PDF at {url} is relevant.")
            
            # Increment PDF counter
            file_counters[sub_id]["pdf"] += 1

            # Save extracted text to markdown file with metadata
            time_save_start = time.time()
            txt_path = save_pdf_text_to_file(pdf_path, sub_id, file_counters[sub_id]["pdf"], url=url, subsidy_type=subsidy_type, keywords=found_keywords)
            time_save_end = time.time()
            print(f"Saving extracted text took {time_save_end - time_save_start:.2f} seconds")
            
            if txt_path:
                found_relevant_content = True
            else:
                print(f"✗ Failed to save text")
        
        else:
            
            print(f"✗ The PDF at {url} is not relevant.")

    # --------------------------------------------------------------------------------------
    # If no relevant content was found, save a "no subsidy found" file
    # --------------------------------------------------------------------------------------

    # If no relevant content was found, save a "no subsidy found" file
    if not found_relevant_content:
        print(f"\n[NO SUBSIDY FOUND] Saving 'no subsidy found' file...")
        save_no_subsidy_found(url, subsidy_type, sub_id, keywords=[])


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

def load_keywords_from_json_dict(keywords_dict_path):
    """Load the keywords_dict.json file."""
    try:
        with open(keywords_dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: {keywords_dict_path} not found.")
        return {}
    except Exception as e:
        print(f"✗ Error loading {keywords_dict_path}: {e}")
        return {}
    

def main_scraper(sub_id, url_type_dict_path="url_type_dict.json", keywords_dict_path="keywords_dict.json"):
    """Main function to run the scraper for a given sub_id."""
    
    # Load the url_type_dict and keywords_dict
    url_type_dict = load_url_type_dict(url_type_dict_path)
    keywords_dict = load_keywords_from_json_dict(keywords_dict_path)

    # Check if the URL and keywords were loaded successfully
    if not url_type_dict or not keywords_dict:
        return

    # Extract the URL and subsidy type for the given sub_id
    url_sub_id = url_type_dict[sub_id]["site_url"]
    type_subv = url_type_dict[sub_id]["type_subv"]

    # Print the information about the subsidy being processed
    print("\n" + "="*60)
    print(f"Perform web-scraping for:  \n  sub_id : {sub_id} \n  website : {url_sub_id}\n  type_subv : {type_subv}\n  keywords : ")
    for keyword in keywords_dict[type_subv]:
        print(f"  - {keyword}") 
    print("" + "="*60)

    # Call scrape_subsidy_page with the sub_id
    scrape_subsidy_page(url_type_dict, keywords_dict, sub_id)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape subsidy information for a given sub_id.")
    parser.add_argument("--sub_id", required=True, help="Unique identifier for the subsidy (e.g., 2041).")
    parser.add_argument("--url_type_dict", default="url_type_dict.json", help="Path to url_type_dict.json file.")
    parser.add_argument("--keywords_dict", default="keywords_dict.json", help="Path to keywords_dict.json file.")

    args = parser.parse_args()
    main_scraper(args.sub_id, args.url_type_dict, args.keywords_dict)


#  python run_pipeline.py -ni 0 -nf 0 --step "scraper"

# Things to consider for next steps:
# If more pdfs, download in parallel and create only one request session per page 
# Save in seperate file basic data for each sub_id, such as url-sites and url-pdfs, matching keywords, language? limited keyword list and language can be used to fucus pompt
# if no info found, maybe don't save file, but add to basic info list such that LLM can skip it
# Open only one browser instance per page, and keep it open while downloading all pdfs from the page, instead of opening a new instance for each pdf link (if we need to check the content of the pdfs to filter them) 