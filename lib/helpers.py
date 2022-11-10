from newspaper import Article
from flask import Response
from bs4 import BeautifulSoup
from os.path import join
import math
import json


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
    """reads /lib/local_cik.json file and finds matching object for ticker symbol, returns CIK number
    or None"""
    with open(join('lib', 'cik_local.json'), 'r') as myfile:
        data = myfile.read()
        cik = json.loads(data)
    for obj in cik:
        if cik[obj]['ticker'] == f"{ticker.upper()}":
            return cik[obj]
    return None


def millify(n):
    """formats number using K for thousands, M for millions, B for billions and T for trillions"""
    millnames = ['', 'K', 'M', 'B', 'T']
    n = float(n)
    millidx = max(0, min(len(millnames)-1,
                         int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    """return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])"""
    return '{:,.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def data_10K(list_):
    """filters 10-k data objects, and builds a python dict with year and value """
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


def data_10K_assets(list_):
    """loops over a json object and brings 10-K data for assets"""
    group = dict()
    for obj in list_["units"]["USD"]:
        if obj["form"] == "10-K" or obj["form"] == "10-K/A":
            data = int(obj["val"])
            group[f"{obj['fy']}"] = millify(data)
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
