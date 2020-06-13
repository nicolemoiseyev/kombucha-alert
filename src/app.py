import requests
import yaml
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load config
config = yaml.safe_load(open("./config.yml"))

'''
Get available product info
'''

# product we want to search for on whole foods
search_query = "GT Kombucha"
product_name = "GT's, Organic Raw Kombucha Lemonade, 16.2 Ounce"

# Run the driver in headless mode on a server
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
driver = webdriver.Chrome(options=options,executable_path=config["CHROME_DRIVER_PATH"])

#driver = webdriver.Chrome(executable_path=config["CHROME_DRIVER_PATH"])
driver.get("https://primenow.amazon.com/")

# Locate the zipcode input field and enter the appropriate store zipcode
zipcode = driver.find_element_by_id("lsPostalCode")
zipcode.send_keys(config["ZIPCODE"])
submit_zipcode = driver.find_element_by_id("a-autoid-1").click()

# wait up to 5s until the following page loads with the product search field
wait = WebDriverWait(driver, 5)
product_search = wait.until(
    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search Whole Foods Market']")))

# Enter the product and submit the search
product_search.send_keys(search_query)
submit_search = driver.find_element_by_xpath(
    "//button[@class='page_header_search_wrapper__searchButton__2Vo9i']").click()

# get the list of products after waiting up to 5s for the search to load
# we're assuming the product we want is on the first page
products_list = wait.until(
    EC.presence_of_element_located((By.XPATH, "//ul[@class='product_grid__grid__1CpnV']/li")))

# iterate over existing products
available_products = []
for item in driver.find_elements_by_class_name('asin_card__title__1Oc6S'): # class of elements corresponding to product names
    item_name = item.find_element_by_xpath('.//div/div').text
    available_products.append(item_name)

def product_is_available(product):
    return product in available_products


'''
Send notification through slack
'''

# parameters to send the notification through slack
SLACK_TOKEN = config["SLACK_TOKEN"]
SLACK_CHANNEL = "#lemonade"

if product_is_available(product_name):
    message = f"*{product_name}* is available on Whole Foods PrimeNow!"
else:
    message = "Product not available"

params = {
    "token": SLACK_TOKEN,
    "channel": SLACK_CHANNEL,
    "text": message
}

slack_endpt = "https://slack.com/api/chat.postMessage"
message = requests.post(slack_endpt, params = params)

print(message.json())
