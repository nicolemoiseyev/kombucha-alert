import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os
import time

in_prod = os.environ.get("IS_HEROKU") == "True"
print(in_prod)

# Load config variables
config = {
        "SLACK_TOKEN": os.environ.get("SLACK_TOKEN"),
        "ZIPCODE": os.environ.get("ZIPCODE"),
        "CHROME_DRIVER_PATH": os.environ.get("CHROME_DRIVER_PATH"),
        "GOOGLE_CHROME_BIN": os.environ.get("GOOGLE_CHROME_BIN")
}


# parameters to send the notification through slack
SLACK_TOKEN = config["SLACK_TOKEN"]

'''
Check if we already sent a message about this product in the last n_hours
'''
def check_if_message_sent(n_hours, product):
    product_name = product["product_name"]
    channel = product["channel"]

    conversations_endpt = "https://slack.com/api/conversations.list"

    # Get list of Slack channels to retrieve this channel's ID
    channels = requests.get(conversations_endpt, headers = {"Authorization": f"Bearer {SLACK_TOKEN}"})
    channels = channels.json()["channels"]

    channel_id = ""
    for result in channels:
        if result["name"] == channel:
            channel_id = result["id"]
            break

    history_endpt = "https://slack.com/api/conversations.history"
    messages = requests.get(history_endpt, params = {"channel": channel_id}, headers = {"Authorization": f"Bearer {SLACK_TOKEN}"})
    messages = messages.json()["messages"]

    if (len(messages) == 0): return False # no messages ever sent

    last_message = messages[0]
    time_stamp = float(last_message["ts"])

    curr_time = time.time()
    sec_per_hour = 60*60
    seconds_elapsed = curr_time - time_stamp

    if (seconds_elapsed / sec_per_hour < n_hours):
        print(f"Last message sent at {time_stamp}")
        return True

    return False

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
        wait = WebDriverWait(item, 5)
        img = wait.until(EC.presence_of_element_located((By.XPATH, ".//img")))
        img_src = img.get_attribute("src");
        available_products.append({"name": item_name, "img": img_src})

    driver.quit()
    return available_products

def product_is_available(product_name, available_products):
    for item in available_products:
        if item["name"] == product_name: return item
    return False


'''
Send notification through slack
'''
def send_notification(product, available_products):

    product_name = product["product_name"]
    item = product_is_available(product_name, available_products)

    if item:
        message = f":boom: KOMBUCHA ALERT! :boom: \n*{product_name}* is available on Whole Foods PrimeNow!"
    else:
        return "No message sent"

    params = {
        "token": SLACK_TOKEN,
        "channel": "#" + product["channel"],
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                },
            },
            {
              "type": "image",
              "title": {
                "type": "plain_text",
                "text": product["product_name"]
              },
              "image_url": item["img"],
              "alt_text": "Product image"
            }
        ]
    }


    slack_endpt = "https://slack.com/api/chat.postMessage"
    message = requests.post(slack_endpt, data = json.dumps(params), headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_TOKEN}"
    })

    return message.json()

if __name__ == "__main__":

    n_hours = 5


    products = [
        {
            "search": "GT Kombucha",
            "product_name": "GT's, Organic Raw Kombucha Lemonade, 16.2 Ounce",
            "channel": "lemonade"
        }
    ]

    for item in products:
        if not check_if_message_sent(n_hours, item):
            available_products = get_products(item["search"])
            message = send_notification(item, available_products)
            print(message)

    '''
    {
        "search": "Green Mountain Gringo, Medium Salsa, 16 Ounce",
        "product": "Green Mountain Gringo, Medium Salsa, 16 Ounce"
    },
    '''
