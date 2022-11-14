from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/shares_outstanding_and_net_assets_for_common?ticker=meli


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
        assets_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/Assets.json", headers=headers)
        if assets_req.status_code == 200:
            j_assets = assets_req.json()
            assets = helpers.data_10K_assets(j_assets, milli=False)
        else:
            assets = False

        shares_outstanding_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/CommonStockSharesOutstanding.json", headers=headers)
        if shares_outstanding_req.status_code == 200:
            j_shares_outstanding = shares_outstanding_req.json()
            shares_outstanding = helpers.track_data_last_quarter_of_year(
                j_shares_outstanding, "shares", False)
        else:
            shares_outstanding = False

        if assets and shares_outstanding:
            net_assets_for_common_stock = helpers.calculate_assets_for_common_stock(
                assets, shares_outstanding)
        else:
            net_assets_for_common_stock = "n/a"

        shares_outstanding_millified = helpers.millify_me(shares_outstanding)
        shares_outstanding_table = helpers.create_table(
            shares_outstanding_millified)

        result = {
            "shares_outstanding_history": shares_outstanding_table,
            "shares_outstanding_data": shares_outstanding_millified,
            "net_assets_for_common_data": net_assets_for_common_stock
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
