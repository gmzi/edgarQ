from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')
FMP_API_KEY = os.environ.get('FMP_API_KEY')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/price?ticker=meli


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a stock ticker symbol from client, requests data from SEC api (https://www.sec.gov/edgar/sec-api-documentation) and returns values
    to client.
    """
    try:
        args = request.args
        ticker = args.get('ticker')
        # -------------------------------------------------------------------------
        price_req = requests.get(
            f"https://financialmodelingprep.com/api/v3/quote-short/{ticker}?apikey={FMP_API_KEY}")
        if price_req.status_code == 200:
            price_list = price_req.json()
            if len(price_list):
                price_dict = price_list[0]
                price = price_dict["price"]
            else:
                price = "n/d"
        else:
            price = "N/A"

        result = {
            "price": price
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
