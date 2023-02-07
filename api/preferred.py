from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/preferred?ticker=meli


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
        preferred_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/PreferredStockSharesOutstanding.json", headers=headers)
        # preferred_req = requests.get(
        #     f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/PreferredStockSharesIssued.json", headers=headers)
        if preferred_req.status_code == 200:
            j_preferred = preferred_req.json()
            preferred_shares = helpers.track_data_last_quarter_of_year(
                j_preferred, "shares", False)
            preferred_shares_latest = list(preferred_shares.values())[0]
            preferred_shares_latest_millified = helpers.millify(
                preferred_shares_latest)
        else:
            preferred_shares = "n/a"
            preferred_shares_latest_millified = "n/a"

        if type(preferred_shares) == dict:
            preferred_shares_outstanding_millified = helpers.millify_me(
                preferred_shares)
            preferred_shares_outstanding_table = helpers.create_table(
                preferred_shares_outstanding_millified)
        else:
            preferred_shares_outstanding_millified = "n/a"
            preferred_shares_outstanding_table = f"<table><tbody><tr><td>N/A</td></tr></tbody></table>"

        result = {
            "preferred_shares_latest": preferred_shares_latest_millified,
            "preferred_shares_outstanding_history": preferred_shares_outstanding_table,
            "preferred_shares_outstanding_data": preferred_shares_outstanding_millified,
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
