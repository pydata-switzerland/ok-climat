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

# Script to scrape PV subsidy information for Swiss cantons
# This script is inspired by this youtube video : https://www.youtube.com/watch?v=YrVRx2c72ig

# For data retrieval :
# Selenium to navigate websites
# Selectolax to parse HTML
# pdfplumber/PyPDF2 to read pdf

# Run example :

# python scraper_okclimat.py -c ZH -s PV -B
# python scraper_okclimat.py -c ZH -s PV -S

def print_basic_html_info(html, driver):
    print(f"\n[DEBUG] Loaded HTML from {driver.current_url}")
    print(f"[DEBUG] HTML length: {len(html)} characters")
    print(f"[DEBUG] First 500 chars: {html[:500]}\n")  

def print_basic_svelta_info(svelte_div):
    if svelte_div:
        print(f"\n[DEBUG] Found Svelte div with data-svelte-props attribute")
        print(f"[DEBUG] data-svelte-props length: {len(svelte_div.attributes.get('data-svelte-props', ''))} characters")
        print(f"[DEBUG] First 500 chars of data-svelte-props: {svelte_div.attributes.get('data-svelte-props', '')[:500]}\n")
    else:
        print(f"\n[DEBUG] No Svelte div found with data-svelte-props attribute\n")

def scrape_base_page(base_url, canton, subsidy, cantons, subsidies, dict_out="dict_specific_canton_subsidy.json", verbose=False):
    """Scrape the root page of francsenergie.ch to extract subsidies information for a specific canton and subsidy type.
    Args:        
        base_url (str): The URL of the root page to start scraping from
        canton (str): The canton code to look for (e.g. "ZH" for Zurich)
        subsidy (str): The subsidy type to look for (e.g. "PV" for photovoltaic)
        cantons (dict): A dictionary containing information about the cantons, including their full name and key words to look for in the provider name
        subsidies (dict): A dictionary containing information about the subsidy types, including key words to look for in the subsidy name
        dict_out (str): The name of the output json file to save the extracted subsidies information (default: "dict_specific_canton_subsidy.json")
        verbose (bool): Whether to print detailed debug information during the scraping process (default: False)
    Returns:     None 
    Output:      A json file containing the extracted subsidies information for the specific canton and subsidy type, saved in the current working directory with the name specified by dict_out
    """

    # Define the steps to navigate to the subsidies page for the specific canton
    click_1 = "Recherche par canton"
    click_2 = f"{cantons[canton]['full_name']} ({canton})"
    click_3 = "ul.municipalities li a"

    #-----------------------------------------
    # Step 0: Navigate to francsenergie.ch 

    print(f"\nNavigating to {base_url} ...\n")

    # Create driver object that is my programmatic remote control for the Chrome browser
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(base_url)

    # Suspends execution for 3 seconds (wait for page to load)
    time.sleep(3)
    
    # Print basic info and first 500 chars of the HTML to check if it loaded correctly
    if verbose:
        html = driver.page_source
        print_basic_html_info(html, driver)

    #-----------------------------------------
    # Step 1: Go to canton search  
  
    print(f"\nClicking on '{click_1}' ...\n")

    # Find element "Recherche par canton" and click it by link text
    search_link = driver.find_element(By.LINK_TEXT, click_1)
    search_link.click()

    # Wait for the next page to load
    time.sleep(3)

    # Print basic info and first 500 chars of the HTML to check if it loaded correctly
    if verbose:
        html = driver.page_source
        print_basic_html_info(html, driver)

    #-----------------------------------------
    # Step 2: Click on specific canton 

    print(f"\nClicking on '{click_2}' ...\n")   

    # Find specific canton and click it by link text
    search_link = driver.find_element(By.LINK_TEXT, click_2)
    search_link.click()

    # Wait for the next page to load
    time.sleep(3)

    # Print basic info and first 500 chars of the HTML to check if it loaded correctly
    if verbose:
        html = driver.page_source
        print_basic_html_info(html, driver)

    #-----------------------------------------
    # Step 3: Click on first municipality (not important which one, when looking at the cantons.. )  

    print(f"\nClicking on first municipality in the list ...\n")

    # Get the first municipality by usinf the first link in the municipality list
    first_municipality_link = driver.find_element(By.CSS_SELECTOR, click_3)
    first_municipality_link.click()

    # Wait for the next page to load
    time.sleep(3)

    # Extract the HTML of the page 
    html = driver.page_source

    # Print basic info and first 500 chars of the HTML to check if it loaded correctly
    if verbose:
        print_basic_html_info(html, driver)
    
    # Close the browser
    driver.quit()

    #-----------------------------------------
    # Step 4: Extract subsidies information from the HTML 

    print(f"\nExtracting subsidies information from the HTML ...\n")

    # Extract JSON data from data-svelte-props using the library selectolax 
    tree = LexborHTMLParser(html)
    
    # Look for the div with the attribute data-svelte-component='subsidies' (this is where the data is stored in the HTML)
    # Svelte belongs to the JavaScript framework and is used to render dynamic content. Svelte stores the data as JSON in the data-svelte-props attribute.
    svelte_div = tree.css_first("[data-svelte-component='subsidies']")

    # Print basic info about the svelte div and its data-svelte-props attribute 
    if verbose:
        print_basic_svelta_info(svelte_div)

    # Make dict to hold subsidies data
    dict_specific_canton_subsidy = {} 
    sub_counter = 0
    
    if svelte_div:
        
        # Extracts the entire value of the data-svelte-props attribute from the HTML element.
        svelte_props_str = svelte_div.attributes.get("data-svelte-props")
        
        # Parse the JSON directly 
        data = json.loads(svelte_props_str)

        # Extract the list of subsidy categories (fields) from the parsed JSON data
        fields = data.get("town", {}).get("fields", [])

        # Iterating through all subsidy categories (fields) 
        for field in fields:
            
            # The sector represent the general area of the subsidy (e.g. building, mobility, development)
            sector = field.get("sector") 
            
            # The kind represent the type of beneficiary (e.g. personal, business, communes) 
            kind = field.get("kind")      
            
            # The name represent the specific category of subsidy (Génération de chaleur, Véhicules électriques)
            category = field.get("name")

            # print sector, kind and name for each field
            if verbose:
                print(f"\nSector : {sector}")
                print(f"Kind : {kind}")
                print(f"Category : {category}")

            # Iterating through all subsidies in the specific category (field)
            for subsidy_item in field.get("subsidies", []):

                # Extract relevant information about the subsidy
                subsidy_name = subsidy_item.get("name", "")
                contributor = subsidy_item.get("contributor", {})
                description = subsidy_item.get("description", "")  
                site_url = subsidy_item.get("site_url", "")

                # Extract relevant information about the provider (contributor)
                provider_name = contributor.get("name", "")
                provider_address = contributor.get("address", [])
                provider_phone = contributor.get("phone", "")
                provider_email = contributor.get("email", "")
                provider_url = contributor.get("url", "")

                if verbose:  
                    print(f"\n  - Subsidy name : {subsidy_name}")
                    print(f"    Contributor : {contributor}")
                    print(f"    Description : {description}")
                    print(f"    Site URL : {site_url}")
                    print(f"    Provider name : {provider_name}")
                    print(f"    Provider address : {provider_address}")
                    print(f"    Provider phone : {provider_phone}")
                    print(f"    Provider email : {provider_email}")
                    print(f"    Provider url : {provider_url}")

                # Check if the provider name contains any of the key words related to the canton we are looking for
                if any(key_word in provider_name for key_word in cantons[canton]["key_words"]):
                    
                    # Check if the subsidy name contains any of the key words related to the subsidy type we are looking for
                    if any(key_word in subsidy_name for key_word in subsidies[subsidy]["key_words"]):

                        print(f"\n--> Match found for subsidy '{subsidy_name}' from provider '{provider_name}' ! Saving it in our dict...")
                        
                        sub_counter += 1
                        
                        dict_specific_canton_subsidy[f"sub_{sub_counter}"] = {
                            "subsidy_category" : category,
                            "subsidy_name" : subsidy_name,
                            "description" : description,
                            "provider_name" : provider_name,
                            "provider_address" : provider_address,
                            "provider_phone" : provider_phone,
                            "provider_email" : provider_email,
                            "provider_url" : provider_url,
                            "site_url" : site_url,
                            "sector" : sector,
                            "kind" : kind
                        }

        # Print subsidies saved in our dict for the specific canton and subsidy type we are looking for
        print(f"\n\nSubsidies in {click_2} related to {subsidy} : \n")
        for sub_key, sub_info in dict_specific_canton_subsidy.items():
            print(f"{sub_key} : {sub_info}\n")
        print(f"We found a total of {sub_counter} subsidies in {click_2} related to {subsidy} !")

        # Dictionary holding unique subsidies, i.e. remove duplicate where subsidy_name and site_url is the same
        unique_subsidies = {}
        for sub_key, sub_info in dict_specific_canton_subsidy.items():
            # Make a unique key based on subsidy name and site url 
            unique_key = (sub_info["subsidy_name"], sub_info["site_url"])  # ← CHANGE THIS
            # If the unique key is not already in the unique_subsidies dict, add it to the unique_subsidies dict
            if unique_key not in unique_subsidies:
                unique_subsidies[unique_key] = sub_info

        # Change keys to not be tuples such that it can be saved in a json file (json does not allow tuples as keys, but only strings)
        unique_subsidies_toBeSaved = {}
        i=0
        for key, value in unique_subsidies.items():
            i += 1
            unique_subsidies_toBeSaved[f"sub_{i}"] = value

        # print result of unique subsidies
        print(f"\nUnique subsidies based on 'subsidy_name' and 'site_url' in {click_2} related to {subsidy} : \n")
        for unique_key, sub_info in unique_subsidies_toBeSaved.items():
            print(f"{unique_key} : {sub_info}\n")

        # Save unique subsidy dict to json file
        with open(dict_out, "w", encoding="utf-8") as f:
            json.dump(unique_subsidies_toBeSaved, f, ensure_ascii=False, indent=2)

        print(f"\nUnique subsidies saved to {dict_out} !\n")
        

def scrape_with_keywords(url, keywords):
    """
    Check if a URL contains relevant information using keyword matching
    Now with the corrected URL from redirect resolution!
    Args:
        url (str): The URL to scrape
        keywords (list): A list of keywords to look for in the page text        
    Returns:
        dict: A dictionary containing the URL, the found keywords, and a preview of the page text if any keywords are found; otherwise, None
    """
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get the page text
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Check if any keyword exists on the page
        found_keywords = [kw for kw in keywords if kw.lower() in page_text]
        
        driver.quit()
        
        if found_keywords:
            return {
                "url": url,
                "found_keywords": found_keywords,
                "page_text_preview": page_text[:500]
            }

        return None
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
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
                    from urllib.parse import urljoin
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

# def scrape_subsidy_page(unique_subsidies, subsidies, subsidy):
#     """Scrape the URLs of the unique subsidies to look for PDFs and relevant information
#     Args:
#         unique_subsidies (dict): A dictionary containing the unique subsidies information
#         subsidies (dict): A dictionary containing information about the subsidy types
#         subsidy (str): The subsidy type to look for (e.g. "PV" for photovoltaic)
#     Returns: 
#         None
#     """
    
#     # Key words to identify text concerning subsidies 
#     keywords = subsidies[subsidy]['key_words']
#     keywords.extend(['förder','unterstützt','subvention','finanziell','beitrag','beihilfe'])

#     # Check the URLs of the unique subsidies
#     for _ , sub_info in unique_subsidies.items():
        
#         subsidy_name = sub_info["subsidy_name"]
#         url = sub_info["site_url"]  

#         print(f"\n{'='*60}")
#         print(f"Checking subsidy: '{subsidy_name}'")
#         print(f"URL: {url}")
#         print(f"{'='*60}")

#         # STEP 1: Look for PDFs on the site
#         print(f"\n[STEP 1] Looking for PDFs on the site...")
#         pdf_urls = find_pdf_links_on_page(url)
        
#         if pdf_urls:
#             print(f"✓ Found {len(pdf_urls)} PDF(s) - these will be processed next")
#         else:
#             print(f"✗ No PDFs found on this page")

import pdfplumber
import requests
from pathlib import Path

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
    """Extract all text from a PDF file.
    Args:
        pdf_path (Path): Path to PDF file (locally saved pdf)    
    Returns:
        str: Extracted text, or None if extraction failed
    """
    
    try:
        # Use pdfplumber library to open pdf 
        with pdfplumber.open(pdf_path) as pdf:
            # Loops through each page in the PDF, extracts the text from each page, and joins all the page texts together into a single string with newline characters in between.
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        # Returns the extracted text (all pages combined as one string)
        return text
   
    except Exception as e:
        print(f"  [ERROR] Could not extract text from PDF: {e}")
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

def save_pdf_text_to_file(pdf_path, pdf_url, subsidy, canton):
    """
    Extract text from PDF and save it to a text file with metadata.
    
    Args:
        pdf_path (Path): Path to the downloaded PDF
        pdf_url (str): Original URL of the PDF
        subsidy (str): Subsidy type (e.g., "PV")
        canton (str): Canton code (e.g., "ZH")
    
    Returns:
        Path to saved text file, or None if failed
    """
    try:
        # Create texts directory if it doesn't exist
        texts_dir = Path("./texts")
        texts_dir.mkdir(exist_ok=True)
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"    ✗ Could not extract text from PDF")
            return None
        
        # Generate output filename (same as PDF but with .txt extension)
        pdf_filename = pdf_path.name
        txt_filename = pdf_filename.replace(".pdf", ".txt").replace(".PDF", ".txt")
        txt_path = texts_dir / txt_filename
        
        # Create metadata header
        metadata = f"""================================================================================
EXTRACTED PDF TEXT WITH METADATA
================================================================================

PDF URL: {pdf_url}
PDF Path: {pdf_path}
Subsidy Type: {subsidy}
Canton: {canton}
Extracted at: {time.strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
TEXT CONTENT
================================================================================

"""
        
        # Write metadata + text to file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(metadata)
            f.write(text)
        
        print(f"    ✓ Saved text to: {txt_path}")
        return txt_path
        
    except Exception as e:
        print(f"    ✗ Error saving text: {e}")
        return None

def scrape_subsidy_page(unique_subsidies, subsidies, subsidy):
    """Scrape the URLs of the unique subsidies to look for PDFs and relevant information. 
    Args:
        unique_subsidies (dict): Dictionary containing subsidy information
        subsidies (dict): Dictionary with subsidy type details
        subsidy (str): The subsidy type to look for (e.g. "PV")    
    Returns: 
        None
    """
    
    # Keywords specific to the subsidy type (used to filter PDFs)
    subsidy_keywords = subsidies[subsidy]['key_words']
    
    # Check each unique subsidy
    for _ , sub_info in unique_subsidies.items():
        
        subsidy_name = sub_info["subsidy_name"]
        url = sub_info["site_url"]
        canton = "ZH"  # ← Add canton parameter (you might want to pass this as argument)

        print(f"\n{'='*60}")
        print(f"Checking subsidy: '{subsidy_name}'")
        print(f"URL: {url}")
        print(f"{'='*60}")

        # STEP 1: Look for all PDFs on the site
        print(f"\n[STEP 1] Discovering PDFs on the website...")
        all_pdf_urls = find_pdf_links_on_page(url)
        
        if not all_pdf_urls:
            print(f"✗ No PDFs found on this page")
            continue
        
        print(f"✓ Found {len(all_pdf_urls)} PDF(s) total")
        
        # STEP 2: Filter PDFs by checking their content for subsidy keywords
        print(f"\n[STEP 2] Filtering PDFs by content (looking for: {subsidy_keywords})...")
        relevant_pdfs = []
        
        for pdf_url in all_pdf_urls:
            is_relevant, pdf_path = is_pdf_relevant(pdf_url, subsidy_keywords)
            if is_relevant:
                relevant_pdfs.append((pdf_url, pdf_path))
        
        print(f"\n[RESULT] {len(relevant_pdfs)} out of {len(all_pdf_urls)} PDFs are relevant")
        
        if relevant_pdfs:
            print(f"\nRelevant PDFs:")
            for pdf_url, pdf_path in relevant_pdfs:
                pdf_name = pdf_url.split('/')[-1]
                print(f"   ✓ {pdf_name}")
                print(f"    Local path: {pdf_path}")
                
                # NEW: Save extracted text to file with metadata
                print(f"\n  [STEP 3] Saving extracted text...")
                txt_path = save_pdf_text_to_file(pdf_path, pdf_url, subsidy, canton)
                
                if txt_path:
                    print(f"  ✓ Text saved successfully")
                else:
                    print(f"  ✗ Failed to save text")
                
                print()
        else:
            print(f"\n✗ No relevant PDFs found for '{subsidy_name}'\n")

def main_scraper(canton, subsidy, verbose, scrape_base_page_flag, scrape_subsidy_page_flag):
    """Main function to run the web scraping process for a specific canton and subsidy type
    Args:
        canton (str): The canton code to look for (e.g. "ZH" for Zurich)"
        subsidy (str): The subsidy type to look for (e.g. "PV" for photovoltaic)
        verbose (bool): Whether to print detailed debug information during the scraping process (default: False)
        scrape_base_page_flag (bool): Whether to run the base page scraper to extract subsidies information from the root page of francsenergie.ch (default: False)
        scrape_subsidy_page_flag (bool): Whether to run the subsidy page scraper to check the URLs of the unique subsidies for relevant information using keyword matching (default: False)
    Returns:
        None
    Output: 
        If scrape_base_page_flag is True, a json file containing the extracted subsidies information for the specific canton and subsidy type will be saved in the current working directory with the name "dict_{canton}_{subsidy}.json". If scrape_subsidy_page_flag is True, the URLs of the unique subsidies will be checked for relevant information using keyword matching, and the found keywords and a preview of the page text will be printed in the console.
    """

    #============================================================
    # Define parameters and variables

    # Base homepage where all subsidy information is stored and from which we will navigate to the specific canton and subsidy pages
    base_url = "https://www.francsenergie.ch/fr"

    # Canton dictionary
    cantons = {
        "ZH" : {
            "full_name" : "Zurich",
            "key_words" : ["Zürich","Zurich","Zürisee","Zürisee","Züri","Züri-See","Zürisee"]
            }
        }

    # Subsidy dictionary
    subsidies = {
        "PV" : {
            "key_words" : ["Solaranlage","Photovoltaïques","Photovoltaik"]}
    }

    # json dict to hold subsidy info retrieved from the base page (francenergie.ch) 
    json_dict_out = f"dict_{canton}_{subsidy}.json"

    #===========================================================
    # Run web scraping

    print(f"\nRunning web-scraping in verbose={verbose} with the input arguments: ")
    print(f"- Canton  : {canton} (key_words={cantons[canton]['key_words']})")
    print(f"- Subsidy : {subsidy} (key_words={subsidies[subsidy]['key_words']})") 
    print(f"- Scrape base page : {scrape_base_page_flag}")
    print(f"- Scrape subsidy page : {scrape_subsidy_page_flag}\n")

    # Run the base pager scraper
    if scrape_base_page_flag:
        scrape_base_page(base_url, canton, subsidy, cantons, subsidies, json_dict_out, verbose)

    # Run the subsidy page scraper 
    if scrape_subsidy_page_flag:

        # Check if file exist before trying to open it
        try:
            with open(json_dict_out, "r", encoding="utf-8") as f:
                unique_subsidies = json.load(f)
                scrape_subsidy_page(unique_subsidies, subsidies, subsidy)
        except FileNotFoundError:
            print(f"\nError: The file '{json_dict_out}' was not found. Please run the base page scraper first to create this file.\n")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape subsidy information for a specific canton and subsidy type")
    parser.add_argument("-c", "--canton", type=str, default="ZH", help="Canton code (default: ZH)")
    parser.add_argument("-s", "--subsidy", type=str, default="PV", help="Subsidy type (default: PV)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed debug information", default=False)
    parser.add_argument("-B", "--scrape_base_page", action="store_true", help="Scrape base page, i.e. francenergie.ch", default=False)
    parser.add_argument("-S", "--scrape_subsidy_page", action="store_true", help="Scrape subsidy page obtained from francenergie.ch", default=False)

    args = parser.parse_args()
    
    vars = vars(args)

    main_scraper(vars["canton"], vars["subsidy"], vars["verbose"], vars["scrape_base_page"], vars["scrape_subsidy_page"])   
