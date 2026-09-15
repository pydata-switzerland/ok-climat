import requests # library used to fetch pages
from selectolax.lexbor import LexborHTMLParser # html parsing
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# This scripts follow the tutorial in this youtube video : https://www.youtube.com/watch?v=YrVRx2c72ig
# It uses the first the request library to fetch the page, however, this is a less reliable method
# After this, the selenium library is used as it is more reliable than requests 
# The selectolax library is used to parse the data from the website
# This example is rather simple, and will only work on simple static websites 
# To do the scraping in this script one needs to know how the data is stored on the website, e.g.:
# 	- know that product is associated with the name "product-card", 
#	- know that the product title and price is associated with the names  ".title" and ".price-wrapper" 

# Challenges when doing real scraping include :
#	- java script rendering in the browser (dynamic data require java script to load)
#	- a simple get request will no longer be sufficient, because you will get a bunch of code instead of html
#	- solution is to automise the browser using a tool like selinium (better than request) 
# 	- get blocked, one should emulate browser with header  


#-----------------------------------------
# Retriving data from webpage (requests or selenium)

# webpage (made for practicing webscraping)
url = "https://sandbox.oxylabs.io/products"

# Open chrome browser in headless mode (run wo opening another window on your machine)
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get(url)

# Find all elements with the class "product-card" (e.g. <div class="product-card">)
WebDriverWait(driver, 10).until(
	EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-card"))
)

html = driver.page_source 
driver.quit()

# Initial retrieval with the requests library (less reliable)
# response = requests.get(url)
# html = response.text
# print(f"{html=}")


#-----------------------------------------
# Parsing data from webpage (selectolax)

tree = LexborHTMLParser(html)
print(f"\n{tree=}")

product_cards = tree.css(".product-card")

all_products = []

for card in product_cards:
	try:
		product_data = {
			"title" : card.css_first(".title").text(strip=True),
			"price" : card.css_first(".price-wrapper").text(strip=True)
		}
		all_products.append(product_data)
	except AttributeError:
		print("Skipping a product card with missing data")
		continue

print(f"\n{all_products}")

#-----------------------------------------
# Saving data in a structured way

# Save data to csv file using pandas data frame
df = pd.DataFrame(all_products)
df.to_csv("products.csv")