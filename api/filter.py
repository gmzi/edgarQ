from flask import Flask, Response, request
import os
import lib.helpers as helpers
import lib.cik_local as data
import requests
import json
import traceback

USER_AGENT = os.environ.get('USER_AGENT')

app = Flask(__name__)

# REQ MODEL: http://192.168.1.9:3000/api/filter?criterion=EPS&min_value=15


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """
    This route takes a criterion (EPS) and a value, and filters all US companies returning those companies whose EPS is 
    greater than or equal to the provided value. In order to perform the filtering, this route performs five requests 
    to data.sec.gov/api/xbrl/frames/, which returns the same concept for multiple companies. One request is for yearly data
    and the other four are for trailing quarters. Yearly values are the output for a company when they exist, and 
    a sum of quarterly data is performed when no yearly data is available. 
    """
    try:
        headers = {'User-Agent': f"{USER_AGENT}"}
        args = request.args
        criterion = args.get('criterion')
        if criterion == 'EPS':
            criterion = "EarningsPerShareDiluted"
        value_str = args.get('min_value')
        value = float(value_str)
        companies = data.companies_dict

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

        # Obtain time data
        time_params = helpers.make_time_frame()

        # GET EPS_diluted data, both annually and four trailing quarters.
        raw_EPS_year = get_data_frames(
            criterion, "USD-per-shares", time_params["year"])
        raw_latest = get_data_frames(
            criterion, "USD-per-shares", time_params["latest"])
        raw_one_to_latest = get_data_frames(
            criterion, "USD-per-shares", time_params["one_to_latest"])
        raw_two_to_latest = get_data_frames(
            criterion, "USD-per-shares", time_params["two_to_latest"])
        raw_three_to_latest = get_data_frames(
            criterion, "USD-per-shares", time_params["three_to_latest"])

        EPS_year = raw_EPS_year["data"]
        EPS_latest = raw_latest["data"]
        EPS_one_to_latest = raw_one_to_latest["data"]
        EPS_two_to_latest = raw_two_to_latest["data"]
        EPS_three_to_latest = raw_three_to_latest["data"]

        raw_TTM = helpers.track_data_TTM(
            EPS_latest, EPS_one_to_latest, EPS_two_to_latest, EPS_three_to_latest, EPS_year)

        TTM_EPS = helpers.sanitize_data(raw_TTM, companies)

        filtered_results = {
            k: v for (k, v) in TTM_EPS.items() if v["EPS_TTM"]["val"] >= value}

        result = {
            "filtered_results": {
                "min_value": value,
                "results_count": len(filtered_results),
                "results": filtered_results
            },
            "unfiltered_results": TTM_EPS
        }

        j_result = json.dumps(result)
        response = helpers.makeResponse(j_result)
        return response
    except Exception as e:
        trace = traceback.format_exc()
        response = helpers.handleException(e, trace)
        return response
