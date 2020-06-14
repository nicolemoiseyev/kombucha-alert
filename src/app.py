import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os

in_prod = os.environ.get("IS_HEROKU") == "True"
print(in_prod)

# Load config variables
config = {
        "SLACK_TOKEN": os.environ.get("SLACK_TOKEN"),
        "ZIPCODE": os.environ.get("ZIPCODE"),
        "CHROME_DRIVER_PATH": os.environ.get("CHROME_DRIVER_PATH"),
        "GOOGLE_CHROME_BIN": os.environ.get("GOOGLE_CHROME_BIN")
}

# product we want to search for on whole foods
search_query = "GT Kombucha"
product_name = "GT's, Organic Raw Kombucha Lemonade, 16.2 Ounce"

# parameters to send the notification through slack
SLACK_TOKEN = config["SLACK_TOKEN"]
SLACK_CHANNEL = "#lemonade"

'''
if not in_prod:
    import yaml
    with open("../config.yml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
'''

'''
Get available products list
'''
def get_products(search_query):
    # Run the driver in headless mode
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless");
    chrome_options.add_argument("--disable-gpu");
    chrome_options.add_argument("--no-sandbox");
    if in_prod:
        chrome_options.binary_location = config["GOOGLE_CHROME_BIN"]
    driver = webdriver.Chrome(executable_path=config["CHROME_DRIVER_PATH"], chrome_options=chrome_options)

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
    product_search.send_keys(search_query) # enter search
    product_search.send_keys(Keys.ENTER) # submit search

    # get the list of products after waiting up to 5s for the search to load
    # we're assuming the product we want is on the first page
    products_list = wait.until(
        EC.presence_of_element_located((By.XPATH, "//ul[@class='product_grid__grid__1CpnV']/li")))

    # iterate over existing products
    available_products = []
    for item in driver.find_elements_by_class_name('product_grid__item__1eRlB'): # product li elements
        item_name = item.find_element_by_class_name('asin_card__title__1Oc6S').text
        img_src = item.find_element_by_xpath(".//img").get_attribute("src");
        available_products.append({"name": item_name, "img": img_src})

    print(available_products)
    driver.quit()
    return available_products

def product_is_available(product_name, available_products):
    for item in available_products:
        if item["name"] == product_name: return item
    return False


'''
Send notification through slack
'''
def send_notification(product_name, available_products):
    item = product_is_available(product_name, available_products)
    if item:
        message = f":boom: KOMBUCHA ALERT! :boom: \n*{product_name}* is available on Whole Foods PrimeNow!"
    else:
        return "No message sent"

    params = {
        "token": SLACK_TOKEN,
        "channel": SLACK_CHANNEL,
        "blocks": [
            {
    			"type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                },
                "accessory": {
    				"type": "image",
    				"image_url": item["img"],
    				"alt_text": "Product image"
    		    }
            }
        ]
    }


    slack_endpt = "https://slack.com/api/chat.postMessage"
    message = requests.post(slack_endpt, params = params)

    return message

if __name__ == "__main__":
    available_products = get_products(search_query)
    message = send_notification(product_name, available_products)
    print(message)
