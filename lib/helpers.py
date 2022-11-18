from flask import Response
from os.path import join
import math
import json
import requests

# ----------------------------------------------------------------------------
# UTILS
# ----------------------------------------------------------------------------


def handleException(e, trace):
    msg = str(e)
    trace = str(trace)
    body = {"error": msg, "trace": trace}
    j_body = json.dumps(body)
    response = Response(j_body, status=404, mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def makeResponse(j_data, status=200):
    response = Response(j_data, status=status, mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def get_cik(ticker):
    with open(join('lib', 'cik_local.json'), 'r') as myfile:
        data = myfile.read()
        cik = json.loads(data)
    for obj in cik:
        if cik[obj]['ticker'] == f"{ticker.upper()}":
            return cik[obj]
    return None


def millify(n):
    """K for thousands, M for millions, B for billions and T for trillions"""
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    # return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
    return '{:,.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def create_table(dict_, source_url=False, dollarsign=False):
    newRows = ""
    if source_url:
        source = f"<a href={source_url} target='_blank' rel='noreferrer'>check</a>"
    else:
        source = ""
    if len(dict_):
        for key, value in dict_.items():
            if dollarsign == True:
                newRow = f"<tr><td>{key}</td><td>${value}</td></tr>"
            else:
                newRow = f"<tr><td>{key}</td><td>{value}</td></tr>"
            newRows += newRow
    else:
        newRows = f"<tr><td>No data</td></tr>"
    result = f"""<table><tbody>{newRows}</tbody></table>{source}"""
    return result


def create_table_multi(dict_1, dict_2, dict_3, source_url=False):
    newRows = ""
    if source_url:
        source = f"<a href={source_url} target='_blank' rel='noreferrer'>check</a>"
    else:
        source = ""
    if len(dict_1):
        for key, value in dict_1.items():
            year = key
            assets = value
            if key in dict_2:
                liabilities = dict_2[f"{key}"]
                assets_to_liabilities = f"""{dict_3[f"{key}"]}x"""
            else:
                liabilities = "n/a"
                assets_to_liabilities = "n/a"
            newRow = f"<tr><td>{year}</td><td>{assets_to_liabilities}</td><td>{assets}</td><td>{liabilities}</td></tr>"
            newRows += newRow
    else:
        newRows = f"<tr><td>No data</td></tr>"
    result = f"""<table><tbody><thead><tr><th>Year</th><th>Assets to liabilities</th><th>Assets</th><th>Liabilities</th></tr></thead>{newRows}</tbody></table>{source}"""
    return result

# ----------------------------------------------------------------------------
# FINANCIAL METHODS
# ----------------------------------------------------------------------------


def calculate_EPS_growth_percentage(EPS_final, EPS_initial):
    if EPS_final > 0 and EPS_initial > 0:
        diference = EPS_final - EPS_initial
        division = diference / EPS_initial
        result = division * 100
        return round(result, 2)
    else:
        return 0


def calculate_EPS_growth_rate(EPS_final, EPS_initial, number_of_periods):
    if EPS_final > 0 and EPS_initial > 0:
        exponent = 1 / number_of_periods
        division = EPS_final / EPS_initial
        exponencial = pow(division, exponent)
        result = (exponencial - 1) * 100
        return round(result, 2)
    else:
        return 0

# print(calculate_EPS_growth_percentage(-3.31, 1))
# print(calculate_EPS_growth_rate(1, 2, 9))

# ----------------------------------------------------------------------------
# DATA EXTRACTION METHODS
# ----------------------------------------------------------------------------


def data_10K(list_):
    """loops over a json object and brings 10-K data"""
    group = dict()
    for obj in list_["units"]["USD"]:
        if obj["form"] == "10-K":
            if "-01-01" in obj['start'] and "-12-31" in obj['end']:
                data = int(obj["val"])
                group[f"{obj['fy']}"] = millify(data)
    # For some edge cases
    if not len(group):
        for obj in list_["units"]["USD"]:
            if obj["form"] == "10-K":
                if "frame" in obj and "Q" not in obj["frame"]:
                    data = int(obj["val"])
                    group[f"{obj['fy']}"] = millify(data)
    reversedGroup = dict(reversed(list(group.items())))
    return reversedGroup


def data_10K_assets(list_, milli=True):
    """loops over a json object and brings 10-K data"""
    group = dict()
    for obj in list_["units"]["USD"]:
        if obj["form"] == "10-K" or obj["form"] == "10-K/A":
            data = int(obj["val"])
            if milli == True:
                group[f"{obj['fy']}"] = millify(data)
            else:
                group[f"{obj['fy']}"] = data
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    return sorted_group


def data_10K_dividends(list_):
    """loops over a json object and brings 10-K data"""
    group = dict()
    for obj in list_["units"]["USD/shares"]:
        if obj["form"] == "10-K":
            if "-01-01" in obj['start'] and "-12-31" in obj['end']:
                data = obj["val"]
                # if f"{obj['fy']}" in group:
                #     group[f"{obj['fy']}"] += data
                # else:
                #     group[f"{obj['fy']}"] = data
                group[f"{obj['fy']}"] = data
    # For some edge cases
    if not len(group):
        for obj in list_["units"]["USD"]:
            if obj["form"] == "10-K":
                if "frame" in obj and "Q" not in obj["frame"]:
                    data = int(obj["val"])
                    group[f"{obj['fy']}"] = millify(data)
    return group


def data_10K_regex(list_, key_, milli=False):
    """loops over a json object and brings 10-K data"""
    group = dict()
    # for obj in list_["units"]["USD/shares"]:
    # FILTER for 'frame:CY1234 and 'form:10' or 'form:10K/A' only:
    for obj in list_["units"][key_]:
        if obj["form"] == "10-K" and "frame" in obj and "CY" in obj["frame"] and "Q" not in obj["frame"] or obj["form"] == "10-K/A" and "frame" in obj and "CY" in obj["frame"] and "Q" not in obj["frame"] or obj["form"] == "8-K" and "frame" in obj and "CY" in obj["frame"] and "Q" not in obj["frame"] or obj["form"] == "8-K/A" and "frame" in obj and "CY" in obj["frame"] and "Q" not in obj["frame"]:
            # data = float(obj["val"])
            data = obj["val"]
            year = obj["frame"][2:]
            if milli == True:
                group[f"{year}"] = millify(data)
            else:
                group[f"{year}"] = data
    # sort group by year, backwards
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    return sorted_group


def data_10Q_regex(list_, key_, milli=False):
    """loops over a json object and brings 10-Q data"""
    group = dict()
    for obj in list_["units"][key_]:
        if obj["form"] == "10-K" and "frame" in obj and "CY" in obj["frame"] and "Q" in obj["frame"] or obj["form"] == "10-K/A" and "frame" in obj and "CY" in obj["frame"] and "Q" in obj["frame"] or obj["form"] == "8-K" and "frame" in obj and "CY" in obj["frame"] and "Q" in obj["frame"] or obj["form"] == "8-K/A" and "frame" in obj and "CY" in obj["frame"] and "Q" in obj["frame"]:
            data = obj["val"]
            year = obj["frame"][2:6]
            if year in group:
                group[year].append(data)
            else:
                group[year] = [data]
    for key, value in group.items():
        if milli == True:
            group[key] = millify(sum(value))
        else:
            group[key] = round(sum(value), 2)
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    return sorted_group


def track_data_quarterly(list_, key_, milli=False):
    group = dict()
    for obj in list_["units"][key_]:
        if "frame" in obj:
            year = obj["frame"][2:6]
            data = obj["val"]
            if year in group:
                group[year] += data
            else:
                group[year] = data
    for key, value in group.items():
        if milli == True:
            group[key] = millify(value)
        else:
            group[key] = round(value, 2)
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    return sorted_group


def track_data_last_quarter_of_year(list_, key_, milli=False):
    group = dict()
    for obj in list_["units"][key_]:
        if "frame" in obj:
            year = obj["frame"][2:6]
            data = obj["val"]
            group[year] = data
    for key, value in group.items():
        if milli == True:
            group[key] = millify(value)
        else:
            group[key] = value
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    return sorted_group


def calculate_assets_for_common_stock(assets_dict, shares_dict):
    group = dict()
    for key, value in assets_dict.items():
        assets = value
        if key in shares_dict:
            shares = shares_dict[f"{key}"]
            net_assets_for_common = assets / shares
            group[key] = round(net_assets_for_common, 3)
    return group


def calculate_assets_to_liabilities(assets_dict, liabilities_dict):
    group = dict()
    for key, value in assets_dict.items():
        assets = value
        if key in liabilities_dict:
            liabilities = liabilities_dict[f"{key}"]
            assets_to_liabilities = assets / liabilities
            group[key] = round(assets_to_liabilities, 1)
    return group


def millify_me(dict_):
    group = dict()
    for key, value in dict_.items():
        group[key] = millify(value)
    return group
