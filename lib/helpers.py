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


def millify_me(dict_):
    group = dict()
    for key, value in dict_.items():
        group[key] = millify(value)
    return group


def create_table(dict_, source_url=False, dollarsign=False):
    newRows = ""
    if source_url:
        source = f"<a href={source_url} target='_blank' rel='noreferrer'>validate</a>"
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
    if type(dict_1) != dict or type(dict_2) != dict or type(dict_3) != dict:
        return "n/d"
    else:
        newRows = ""
        if source_url:
            source = f"<a href={source_url} target='_blank' rel='noreferrer'>validate</a>"
        else:
            source = ""
        if len(dict_1):
            for key, value in dict_1.items():
                year = key
                assets = f"${value}"
                if key in dict_2:
                    liabilities = f"""${dict_2[f"{key}"]}"""
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


def sanitize_data(dict_, reference_dict):
    """this function takes all results from quarterly data and compares it with
    a list of all current companies. Matching results are included in the result, with
    value, cik and ticker"""
    cik_keyed_dict = dict()
    not_in_reference = dict()
    result = dict()
    # make a dict_ with cik as keys, instead of arbitrary numbers:
    for key in reference_dict:
        cik = reference_dict[key]["cik_str"]
        cik_keyed_dict[cik] = reference_dict[key]
    # use cik_keyed_dict to check existence of dict_ values, throw unmatching values
    # in not_in_reference for further validation:
    for key in dict_:
        cik = int(key)
        EPS = dict_[key]
        if cik in cik_keyed_dict:
            result[cik] = cik_keyed_dict[cik]
            result[cik]["cik_str"] = str(cik)
            result[cik]["EPS_TTM"] = EPS
        else:
            not_in_reference[cik] = EPS
    return result


def make_cik_keyed_dict(list_):
    result = dict()
    for elem in list_:
        cik = elem["cik"]
        result[cik] = elem
    return result


def convert_reference_to_cik_keyed(reference):
    cik_keyed = dict()
    for key in reference:
        cik = reference[key]["cik_str"]
        cik_keyed[cik] = reference[key]
    return cik_keyed


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


def calc_average_earnings(list_):
    result = round(sum(list_) / 3, 2)
    return result


def calc_price_to_average_earnings_last_3_years_ratio(curr_price, avg_earnings,):
    result = round(curr_price / avg_earnings, 1)
    return result


def calc_percentage_increase(last_3, first_3):
    step_1 = (last_3 - first_3) / first_3
    percent = step_1 * 100
    result = round(percent, 2)
    return result


def calc_earnings_growth(list_, by_3=True):
    last_3_ = list_[0:3]
    first_3_ = list_[8:11]
    last_1 = list_[0]
    first_1 = list_[11]
    avg_last_3 = calc_average_earnings(last_3_)
    avg_first_3 = calc_average_earnings(first_3_)
    if by_3:
        avg_e_growth_by_3 = calc_percentage_increase(
            avg_last_3, avg_first_3)
        return avg_e_growth_by_3
    else:
        avg_e_growth_beginning_and_end = calc_percentage_increase(
            last_1, first_1)
        return avg_e_growth_beginning_and_end


def calc_price_to_book_value(price, bvps):
    step_1 = price / bvps
    result = round(step_1, 2)
    return result

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


def data_FP(list_, milli=True):
    group = dict()
    for obj in list_["units"]["USD"]:
        if obj["fp"] == "FY":
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


def process_dict(dict_, reference_dict, storage_dict):
    """if company exists in yearly dict, skip company,
    else add quarterly values to storage dict"""
    cik = dict_["cik"]
    val = dict_["val"]
    if cik not in reference_dict:
        if cik in storage_dict:
            storage_dict[cik] += val
        else:
            storage_dict[cik] = val


def track_data_TTM(Q1, Q2, Q3, Q4, YEAR):
    """take four lists for quarterly data, and one list for yearly data"""
    year = dict()
    group = dict()

    """unpack yearly data in a single dict"""
    for dict_ in YEAR:
        cik = dict_["cik"]
        val = dict_["val"]
        start = dict_["start"]
        end = dict_["end"]
        data = dict({"val": val, "year": {"start": start, "end": end}})
        year[cik] = data

    """loop over quarterly data"""
    for dict_ in Q1:
        process_dict(dict_, year, group)
    for dict_ in Q2:
        process_dict(dict_, year, group)
    for dict_ in Q3:
        process_dict(dict_, year, group)
    for dict_ in Q4:
        process_dict(dict_, year, group)

    """format data and round values from group dict"""
    for key, value in group.items():
        data = dict({"val": round(value, 2), "year": False})
        group[key] = data

    """merge and sort"""
    result = {**year, **group}
    sorted_result = {k: result[k] for k in sorted(result.keys(), reverse=True)}
    return sorted_result


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


def calculate_assets_minus_liabilities(assets_dict, liabilities_dict, latest=True):
    group = dict()
    for key, value in assets_dict.items():
        assets = value
        if key in liabilities_dict:
            liabilities = liabilities_dict[f"{key}"]
            assets_minus_liabilities = assets - liabilities
            group[key] = round(assets_minus_liabilities, 1)
    sorted_group = {k: group[k] for k in sorted(group.keys(), reverse=True)}
    if latest:
        latest_dict = {list(sorted_group.keys())[
            0]: list(sorted_group.values())[0]}
        return latest_dict
    else:
        return sorted_group
