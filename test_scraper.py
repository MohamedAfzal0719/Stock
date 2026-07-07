import requests
import re

def test_google():
    res = requests.get('https://www.google.com/finance/quote/GOLDBEES:NSE')
    # Search for something like data-last-price="118.68"
    match = re.search(r'data-last-price="([0-9\.]+)"', res.text)
    if match:
        print("Google Finance:", match.group(1))
    else:
        print("Google Finance: Not found")

def test_yahoo():
    res = requests.get('https://finance.yahoo.com/quote/GOLDBEES.NS', headers={'User-Agent': 'Mozilla/5.0'})
    # Search for current price in yahoo HTML
    match = re.search(r'data-value="([0-9\.]+)"', res.text)
    if match:
        print("Yahoo HTML:", match.group(1))
    else:
        print("Yahoo HTML: Not found")

test_google()
test_yahoo()
