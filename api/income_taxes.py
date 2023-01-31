from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/income_taxes?ticker=meli


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
        validation_url = f"https://apps.cnbc.com/view.asp?symbol={ticker}&uid=stocks/financials&view=cashFlowStatement"
        income_taxes_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/IncomeTaxesPaidNet.json", headers=headers)
        if income_taxes_req.status_code == 200:
            j_income_taxes = income_taxes_req.json()
            # k_10_income_taxes_loss = helpers.data_10K(j_income_taxes)
            income_taxes = helpers.data_10K_regex(
                j_income_taxes, "USD", milli=True)
            income_taxes_table = helpers.create_table(
                income_taxes, validation_url)
        else:
            income_taxes_table = "N/A"
            income_taxes = "n/d"

        result = {
            "income_taxes": income_taxes_table,
            "income_taxes_data": income_taxes
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
