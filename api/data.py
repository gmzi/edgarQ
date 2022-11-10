from flask import Flask, Response, request
import os
import lib.helpers as helpers
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQUEST TEMPLATE: http://localhost:3000/api/data?ticker=vti


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route receives a stock ticker symbol from url, then: 
        1- Finds CIK number for the ticker symbol provided (reads the reference file /lib/cik_local.json).
        2- Makes a series of requests to SEC API, one request per each company concept.
        3- Combines the data from all requests and returns .json data to client. 
    (EDGAR SEC API documentation: https://www.sec.gov/edgar/sec-api-documentation
    """
    try:
        # HEADERS AND REQUEST SETUP:
        headers = {'User-Agent': f"{USER_AGENT}"}
        args = request.args
        ticker = args.get('ticker')
        # GET CIK FOR TICKER SYMBOL:
        cik = helpers.get_cik(ticker)
        """{"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}"""
        if cik is None:
            content = f"{ticker} is not a valid ticker symbol"
            return Response(content, status=404, mimetype='text/html')
        codeCIK = str(cik['cik_str'])
        modelCIK = 'CIK0000000000'
        newCIK = modelCIK[:-len(codeCIK)] + codeCIK

        # -------------------------------------------------------------------------
        # DATA REQUESTS:
        # -------------------------------------------------------------------------

        # SHARES OUTSTANDING
        shares_outstanding_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/CommonStockSharesOutstanding.json", headers=headers)
        if shares_outstanding_req.status_code == 200:
            j_shares_outstanding = shares_outstanding_req.json()
            last_shares_outstanding = j_shares_outstanding["units"]["shares"][-1]
            shares_outstanding = helpers.millify(
                last_shares_outstanding["val"])
        else:
            shares_outstanding = "N/A"

        # -------------------------------------------------------------------------
        # REVENUES
        revenues_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/Revenues.json", headers=headers)
        if revenues_req.status_code == 200:
            j_revenues = revenues_req.json()
            k_10_revenues = helpers.track_data_quarterly(
                j_revenues, "USD", True)
        else:
            k_10_revenues = "N/A"

        # -------------------------------------------------------------------------
        # NET INCOME
        net_income_loss_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/NetIncomeLoss.json", headers=headers)
        if net_income_loss_req.status_code == 200:
            j_net_income_loss = net_income_loss_req.json()
            # k_10_net_income_loss = helpers.data_10K(j_net_income_loss)
            k_10_net_income_loss = helpers.data_10K_regex(
                j_net_income_loss, "USD", milli=True)
        else:
            k_10_net_income_loss = "N/A"

        # -------------------------------------------------------------------------
        # DIVIDENDS
        dividends_history_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/CommonStockDividendsPerShareDeclared.json", headers=headers)
        if dividends_history_req.status_code == 200:
            j_dividends_history = dividends_history_req.json()
            data_10K = helpers.data_10K_regex(
                j_dividends_history, "USD/shares")
            data_10Q = helpers.data_10Q_regex(
                j_dividends_history, "USD/shares")
            if len(data_10K) > len(data_10Q):
                dividends_history = data_10K
            else:
                dividends_history = data_10Q
            # IF THE ABOVE REQUEST DOESN'T RETRIEVE ENOUGH DATA, TRY THIS ALTERNATE COMPANYCONCEPT REQUEST:
            if len(dividends_history) < 10:
                dividends_history_req_2 = requests.get(
                    f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/CommonStockDividendsPerShareCashPaid.json", headers=headers)
                j_dividends_history_2 = dividends_history_req_2.json()
                data_10K_2 = helpers.data_10K_regex(
                    j_dividends_history_2, "USD/shares")
                data_10Q_2 = helpers.data_10Q_regex(
                    j_dividends_history_2, "USD/shares")
                if len(data_10K_2) > len(data_10Q_2):
                    dividends_history = data_10K_2
                else:
                    dividends_history = data_10Q_2
        # ALTERNATE COMPANY CONCEPT IF FIRST CONCEPT FAILS:
        else:
            dividends_history_req = requests.get(
                f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/CommonStockDividendsPerShareCashPaid.json", headers=headers)
            if dividends_history_req.status_code == 200:
                j_dividends_history = dividends_history_req.json()
                dividends_history = helpers.track_data_quarterly(
                    j_dividends_history, "USD/shares")
            else:
                dividends_history = "N/A"
        # -------------------------------------------------------------------------
        # ASSETS
        assets_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/Assets.json", headers=headers)
        if assets_req.status_code == 200:
            j_assets = assets_req.json()
            assets = helpers.data_10K_assets(j_assets)
            # if problems arise with assets helper, try this alternate approach:
            # assets = helpers.data_10Q_regex(j_assets, "USD", milli=True)
        else:
            assets = "N/A"

        # -------------------------------------------------------------------------
        # LIABILITIES
        liabilities_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/Liabilities.json", headers=headers)
        if liabilities_req.status_code == 200:
            j_liabilities = liabilities_req.json()
            liabilities = helpers.data_10K_assets(j_liabilities)
            # if problems arise with liabilities helper, try this alternate approach:
            # liabilities = helpers.data_10Q_regex(j_assets, "USD", milli=True)
        else:
            liabilities = "N/A"

        # -------------------------------------------------------------------------
        # EPS DILUTED
        eps_diluted_req = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/{newCIK}/us-gaap/EarningsPerShareDiluted.json", headers=headers)
        if eps_diluted_req.status_code == 200:
            j_eps_diluted = eps_diluted_req.json()
            eps_diluted = helpers.data_10K_regex(j_eps_diluted, "USD/shares")
            # eps_diluted = helpers.track_data_quarterly(
            #     j_eps_diluted, "USD/shares")
        else:
            eps_diluted = "N/A"

        result = {
            "ticker": ticker,
            "cik": newCIK,
            "shares_outstanding": shares_outstanding,
            "total_revenue": k_10_revenues,
            "net_income_loss": k_10_net_income_loss,
            "dividends_history": dividends_history,
            "total_assets": assets,
            "total_liabilities": liabilities,
            "eps_diluted_history": eps_diluted
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
