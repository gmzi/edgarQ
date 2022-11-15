from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/assets_vs_liabilities?ticker=meli


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a stock ticker symbol from url, requests data from SEC api (https://www.sec.gov/edgar/sec-api-documentation) and returns values
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
            assets_millified = helpers.millify_me(assets)
        else:
            assets = "N/A"
            assets_millified = "N/A"
        # -------------------------------------------------------------------------
        liabilities_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/Liabilities.json", headers=headers)
        if liabilities_req.status_code == 200:
            j_liabilities = liabilities_req.json()
            liabilities = helpers.data_10K_assets(j_liabilities, milli=False)
            liabilities_millified = helpers.millify_me(liabilities)
        else:
            liabilities = "N/A"
            liabilities_millified = "N/A"

        if type(assets) == dict and type(liabilities) == dict:
            assets_to_liabilities = helpers.calculate_assets_to_liabilities(
                assets, liabilities)
        else:
            assets_to_liabilities = "n/a"

        assets_vs_liabilities = helpers.create_table_multi(
            assets_millified, liabilities_millified, assets_to_liabilities)

        result = {
            "assets_vs_liabilities": assets_vs_liabilities,
            "assets_to_liabilities_data": assets_to_liabilities,
            "assets_data": assets_millified,
            "liabilities_data": liabilities_millified
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
