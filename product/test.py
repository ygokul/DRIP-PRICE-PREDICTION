from bs4 import BeautifulSoup
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from googlesearch import search
from itertools import islice
import json
import re

def extract_keywords(text, num_keywords=25):
    words = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_words = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]
    return filtered_words[:num_keywords]

def search_product(keywords, num_results=5):
    query = ' '.join(keywords)
    search_results = list(islice(search(query), num_results))
    return search_results

def check_drip_pricing(prod_features):
    drip_indicators = ["fee", "charge", "tax", "shipping", "total"]
    return any(indicator in prod_features.lower() for indicator in drip_indicators)

def check_actual_drip_pricing(script_content):
    if isinstance(script_content, list) and script_content:
        for element in script_content:
            if "requires_shipping" in element and "taxable" in element:
                requires_shipping = str(element["requires_shipping"]).lower()
                taxable = str(element["taxable"]).lower()

                if requires_shipping == "true" and taxable == "true":
                    return True

    return False

def extract_script_content(soup):
    script_element = soup.find("script", id="em_product_variants", type="application/json")
    script_content = []
    if script_element:
        try:
            script_content = json.loads(script_element.string)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            print("JSON Content:", script_element.string)
    else:
        print("No script element with ID 'em_product_variants' found")

    return script_content


def analyze_product(url):
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
               'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/json', 'tz': 'GMT+00:00'}

    webpage = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, 'html.parser')

    prod_price_element = soup.find("div", class_="price__current price__current--on-sale").find("span", class_="money")
    prod_price = prod_price_element.text.strip() if prod_price_element else "N/A"

    prod_features_element = soup.find("div", class_="product-description rte")
    prod_features = prod_features_element.text.strip() if prod_features_element else "N/A"

    nltk.download('punkt')
    nltk.download('stopwords')

    keywords = extract_keywords(prod_features, num_keywords=25)

    search_results = search_product(keywords, num_results=5)

    drip_pricing_detected = check_drip_pricing(prod_features)

    # Extracting script content
    script_content = extract_script_content(soup)
    
    print("\nScript Content:")
    print(script_content)

    actual_drip_pricing_detected = check_actual_drip_pricing(script_content)

    return prod_price, prod_features, search_results, drip_pricing_detected, actual_drip_pricing_detected

if __name__ == '__main__':
    url = "https://deodap.in/products/0733-stainless-steel-cloth-drying-stand?variant=45514437361974"
    prod_price, prod_features, search_results, drip_pricing_detected, actual_drip_pricing_detected = analyze_product(url)

    print("Product Price:", prod_price)
    print("Product Features:", prod_features)

    print("\nSearch Results:")
    for result in search_results:
        print(result)

    print("\nDrip Pricing Detection:")
    if drip_pricing_detected:
        print("Potential drip pricing detected!")
    else:
        print("No potential drip pricing detected.")

    print("\nActual Drip Pricing:")
    if actual_drip_pricing_detected:
        print("Actual drip pricing detected based on script attribute!")
    else:
        print("No actual drip pricing detected based on script attribute.")
