from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')
BASE_URL = os.environ.get('BASE_URL')
FMP_API_KEY = os.environ.get('FMP_API_KEY')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/eps_diluted?ticker=meli


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a stock ticker symbol from client, requests EPS DILUTED data from SEC api (https://www.sec.gov/edgar/sec-api-documentation) and 
    calculates EPS growth in 10 a 10 year period, by 3 year averages at the beginning and end and by increase of oldest to newest values. 
    Also requests live price data from ./price.py to calculate average earnings to price ratio. 
    """
    try:
        headers = {'User-Agent': f"{USER_AGENT}"}
        args = request.args
        ticker = args.get('ticker')
        cik = helpers.get_cik(ticker)
        """{"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}"""
        if cik is None:
            content = f"{ticker} is not a valid ticker symbol"
            return Response(content, status=404, mimetype='text/html')

        codeCIK = str(cik['cik_str'])
        modelCIK = 'CIK0000000000'
        newCIK = modelCIK[:-len(codeCIK)] + codeCIK
        # -------------------------------------------------------------------------
        compare_url = f"https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}"
        eps_diluted_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/EarningsPerShareDiluted.json", headers=headers)
        if eps_diluted_req.status_code == 200:
            j_eps_diluted = eps_diluted_req.json()
            eps_diluted = helpers.data_10K_regex(j_eps_diluted, "USD/shares")
            # growth_rates = helpers.extract_growth_rates(eps_diluted)
            eps_diluted_table = helpers.create_table(
                eps_diluted, compare_url, dollarsign=True)
        else:
            eps_diluted = "N/A"
            eps_diluted_table = "N/A"
        # ----------------------------------------------------------------------------
        # If SEC query retrieved enough EPS data, calculate EPS average growth and average EPS to price ratio.
        if type(eps_diluted) == dict:
            period_10Y = list(eps_diluted.values())
            if len(period_10Y) >= 10:
                avg_eps_last_3 = helpers.calc_average_earnings(period_10Y[0:3])
                avg_eps_growth_by_3 = helpers.calc_earnings_growth(period_10Y)
                avg_eps_growth_beginning_and_end = helpers.calc_earnings_growth(
                    period_10Y, by_3=False)
            elif len(period_10Y) <= 4:
                avg_eps_last_3 = helpers.calc_average_earnings(period_10Y[0:3])
            else:
                avg_eps_last_3 = None
            # -------------------------------------------------------
            # PRICE REQUEST:
            price_req = requests.get(
                f"https://financialmodelingprep.com/api/v3/quote-short/{ticker}?apikey={FMP_API_KEY}")
            if price_req.status_code == 200 and avg_eps_last_3:
                j_price = price_req.json()
                if len(j_price):
                    price_dict = j_price[0]
                    price = price_dict["price"]
                else:
                    price = "n/d"
                price_to_avg_eps_last_3_years_ratio = helpers.calc_price_to_average_earnings_last_3_years_ratio(
                    price, avg_eps_last_3)
            else:
                price_to_avg_eps_last_3_years_ratio = "n/a"
        else:
            avg_eps_last_3 = "n/a"
            price_to_avg_eps_last_3_years_ratio = "n/d"
            avg_eps_growth_by_3 = "n/d"
            avg_eps_growth_beginning_and_end = "n/d"

        result = {
            "price": f"${price}",
            "eps_diluted": eps_diluted_table,
            "eps_diluted_data": eps_diluted,
            "avg_eps_last_3_years": f"${avg_eps_last_3}",
            "price_to_avg_eps_last_3_years_ratio": f"{price_to_avg_eps_last_3_years_ratio}x",
            "eps_growth_avg_10_years_by_3": f"{avg_eps_growth_by_3}%",
            "eps_growth_avg_10_years_beginning_and_end": f"{avg_eps_growth_beginning_and_end}%"
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
