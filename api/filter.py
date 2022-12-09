from flask import Flask, Response, request
import os
import lib.helpers as helpers
import lib.cik_local as data
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

        companies = data.companies_list

        def get_data_frames(concept, unit, period):
            """route returns multiple companies for a single concept"""
            try:
                make_req = requests.get(
                    f"https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/{unit}/{period}.json", headers=headers)
                if make_req.status_code == 200:
                    j_data = make_req.json()
                    return j_data
                else:
                    return False
            except Exception as e:
                return e

        # GET EPS_diluted data for four trailing quarters, and annual data.
        raw_EPS_year = get_data_frames(
            "EarningsPerShareDiluted", "USD-per-shares", "CY2022")
        raw_EPS_Q1 = get_data_frames(
            "EarningsPerShareDiluted", "USD-per-shares", "CY2022Q1")
        raw_EPS_Q2 = get_data_frames(
            "EarningsPerShareDiluted", "USD-per-shares", "CY2022Q2")
        raw_EPS_Q3 = get_data_frames(
            "EarningsPerShareDiluted", "USD-per-shares", "CY2022Q3")
        raw_EPS_Q4 = get_data_frames(
            "EarningsPerShareDiluted", "USD-per-shares", "CY2021Q4")

        EPS_year = raw_EPS_year["data"]
        EPS_Q1 = raw_EPS_Q1["data"]
        EPS_Q2 = raw_EPS_Q2["data"]
        EPS_Q3 = raw_EPS_Q3["data"]
        EPS_Q4 = raw_EPS_Q4["data"]

        TTM = helpers.track_data_TTM(EPS_Q1, EPS_Q2, EPS_Q3, EPS_Q4, EPS_year)

        """
        matches = filter TTM for results that match the criterion.
        tickers_and_ciks = for match in matches:
                            find match_cik in companies
                            return TICKER?
        """

        result = {
            # "EPS_TTM_len": len(TTM),
            # "EPS_Q2_len": len(EPS_Q2),
            # "EPS_Q1_len": len(EPS_Q1),
            # "EPS_Q3_len": len(EPS_Q3),
            # "EPS_Q4_len": len(EPS_Q4),
            # "all_companies": len(companies),
            # "EPS_Q1": EPS_Q1,
            # "EPS_Q2": EPS_Q2,
            # "EPS_Q3": EPS_Q3,
            # "EPS_Q4": EPS_Q4,
            # "EPS_year_2022": EPS_year,
            "EPS_TTM": TTM
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
