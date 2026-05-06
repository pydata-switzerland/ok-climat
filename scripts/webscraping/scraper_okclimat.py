from selectolax.lexbor import LexborHTMLParser
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json

# Script to scrape PV subsidy information for Swiss cantons
# This script is inspired by this youtube video : https://www.youtube.com/watch?v=YrVRx2c72ig

# For data retrieval :
# Selenium to navigate websites
# Selectolax to parse HTML
# pdfplumber/PyPDF2 to read pdf

# Starting with Zurich as a test case


# Canton dictionaries
cantons = {
	"ZH" : "Zurich"}

# Subsidy dictionary
subsidies = {
	"PV" : {
		"key_words" : ["Solaranlage","Photovoltaïques","Photovoltaik"]}
}

# Input arguments
canton = "ZH"
subsidy = "PV"

# Homepage and mandatory steps:
base_url = "https://www.francsenergie.ch/fr"
step_1 = "Recherche par canton"
step_2 = f"{cantons[canton]} ({canton})"
step_3 = "ul.municipalities li a"

print("\nInput : ")
print(f"- Canton  : {cantons[canton]} ({canton})")
print(f"- Subsidy : {subsidy} (key_words={subsidies[subsidy]['key_words']})\n")

#-----------------------------------------
# Step 0: Navigate to francsenergie.ch 

# Create driver object that is my programmatic remote control for the Chrome browser
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get(base_url)

# Suspends execution for 3 seconds (wait for page to load)
time.sleep(3)

# Now print the page source to inspect what loaded
html = driver.page_source
# print(html)

#-----------------------------------------
# Step 1: Go to canton search    

# Find element "Recherche par canton" and click it by link text (simplest)
search_link = driver.find_element(By.LINK_TEXT, step_1)
search_link.click()

# Wait for the next page to load
time.sleep(3)

# Now you're on the search page - get the HTML
html = driver.page_source
# print(html)

#-----------------------------------------
# Step 2: Click on specific canton    

# Find element "Zurich" and click it by link text (simplest)
search_link = driver.find_element(By.LINK_TEXT, step_2)
search_link.click()

# Wait for the next page to load
time.sleep(3)

# Now you're on the search page - get the HTML
html = driver.page_source
# print(html)

#-----------------------------------------
# Step 3: Click on first municipality (not important which one, when looking at the cantons.. )  

# Get the first municipality
# Option 1: Find the first link in the municipalities list (simplest)
first_municipality_link = driver.find_element(By.CSS_SELECTOR, step_3)
first_municipality_link.click()

# Wait for the subsidies page to load
time.sleep(3)

# Now you're on the first municipality's subsidies page - get the HTML
html = driver.page_source
# print(html)


#-----------------------------------------
# Step 4: Extract subsidy matches from page 


# Extract JSON data from data-svelte-props using the library selectolax 
tree = LexborHTMLParser(html)
svelte_div = tree.css_first("[data-svelte-component='subsidies']")
# print(svelte_div.text())
# print(" ")
# print(svelte_div.attributes)
print(" ")

if svelte_div:
    # extracts the entire value of the data-svelte-props attribute from the HTML element.
    svelte_props_str = svelte_div.attributes.get("data-svelte-props")
    # print(svelte_props_str)
    
    # Parse the JSON directly 
    data = json.loads(svelte_props_str)
    # print(data)
    
    # Now you can access the data
    # print("TOWN : ", data["town"]["name"])
    # print("--------------------")
    # print("FIELDS : ", data["town"]["fields"])

    fields = data.get("town", {}).get("fields", [])

    for field in fields:

        print(f"field : {field}\n")
#-----------------------------------------

# Don't forget to close the browser
driver.quit()



#===================================================================
# #-----------------------------------------
# # Retriving data from webpage (requests or selenium)

# # webpage (made for practicing webscraping)
# url = "https://sandbox.oxylabs.io/products"

# # Open chrome browser in headless mode (run wo opening another window on your machine)
# options = Options()
# options.add_argument("--headless")
# driver = webdriver.Chrome(options=options)
# driver.get(url)

# # Find all elements with the class "product-card" (e.g. <div class="product-card">)
# WebDriverWait(driver, 10).until(
# 	EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-card"))
# )

# html = driver.page_source 
# driver.quit()

# # Initial retrieval with the requests library (less reliable)
# # response = requests.get(url)
# # html = response.text
# # print(f"{html=}")


# #-----------------------------------------
# # Parsing data from webpage (selectolax)

# tree = LexborHTMLParser(html)
# print(f"\n{tree=}")

# product_cards = tree.css(".product-card")

# all_products = []

# for card in product_cards:
# 	try:
# 		product_data = {
# 			"title" : card.css_first(".title").text(strip=True),
# 			"price" : card.css_first(".price-wrapper").text(strip=True)
# 		}
# 		all_products.append(product_data)
# 	except AttributeError:
# 		print("Skipping a product card with missing data")
# 		continue

# print(f"\n{all_products}")

# #-----------------------------------------
# # Saving data in a structured way

# # Save data to csv file using pandas data frame
# df = pd.DataFrame(all_products)
# df.to_csv("products.csv")