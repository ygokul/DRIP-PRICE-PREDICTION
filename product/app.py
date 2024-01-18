from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from googlesearch import search
from itertools import islice
import json
import re

app = Flask(__name__)

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
    return script_content




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']

        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                   'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/json', 'tz': 'GMT+00:00'}

        webpage = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(webpage.content, 'html.parser')

        prod_price_element = soup.find("div", class_="price__current price__current--on-sale").find("span", class_="money")
        prod_price = prod_price_element.text.strip()[4:] if prod_price_element else "N/A"

        prod_features_element = soup.find("div", class_="product-description rte")
        prod_features = prod_features_element.text.strip() if prod_features_element else "N/A"

        img_src_element = soup.find("img", class_="product-gallery--loaded-image")
        img_src = img_src_element["src"] if img_src_element else "N/A"

        nltk.download('punkt')
        nltk.download('stopwords')

        keywords = extract_keywords(prod_features, num_keywords=25)

        search_results = search_product(keywords, num_results=5)

        drip_pricing_detected = check_drip_pricing(prod_features)

        # Extracting script content
        script_content = extract_script_content(soup)

        actual_drip_pricing_detected = check_actual_drip_pricing(script_content)

        # Calculate predicted_price
        if prod_price != "N/A":
            prod_price_numeric = float(prod_price.replace(',', ''))
            predicted_price = prod_price_numeric + (prod_price_numeric * 0.18) + 99 + 17.82
            predicted_price = round(predicted_price, 2)
        else:
            predicted_price = "N/A"

        return render_template('result.html', url=url, prod_price=prod_price, prod_features=prod_features,
                               search_results=search_results, drip_pricing_detected=drip_pricing_detected,
                               actual_drip_pricing_detected=actual_drip_pricing_detected, 
                               predicted_price=predicted_price, img_src=img_src)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
