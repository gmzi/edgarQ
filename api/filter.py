from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/filter?criterion=EPS&value=15


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a criterion and a value, and filters all US companies returning those companies that meet 
    the criterion.
    In order to perform the filtering, this route calls to SEC EDGAR API for the company concept matching the 
    filtering criterion.
    """
    try:
        headers = {'User-Agent': f"{USER_AGENT}"}
        args = request.args
        criterion = args.get('criterion')
        value = args.get('value')
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
        filter_results = "n/a"

        result = {
            "filter_results": filter_results
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
