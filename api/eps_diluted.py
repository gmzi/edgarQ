from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/eps_diluted?ticker=meli


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a stock ticker symbol from client, requests data from SEC api (https://www.sec.gov/edgar/sec-api-documentation) and returns values
    to client.
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
            eps_diluted_table = helpers.create_table(eps_diluted, compare_url)
            # eps_diluted = helpers.track_data_quarterly(
            #     j_eps_diluted, "USD/shares")
        else:
            eps_diluted_table = "N/A"

        result = {
            "eps_diluted": eps_diluted_table,
            "eps_diluted_data": eps_diluted
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
