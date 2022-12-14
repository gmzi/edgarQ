import requests
import json
import os

"""
This script updates the list of CIKs that flask routes will consume.
It requests the new CIKS from SEC api and rewrites `lib/cik_local.json` and `lib/cik_local.js` 
with updated data. 
Run with these commands:
                    1. Make backups of /lib/cik_local.json and /lib/cik_local.js.
                    1. `cd utilities`
                    2. `python3 update_ciks.py`
"""

USER_AGENT = os.environ.get('USER_AGENT')


headers = {'User-Agent': f"{USER_AGENT}"}

tickers_cik = requests.get(
    "https://www.sec.gov/files/company_tickers.json", headers=headers)

cik = tickers_cik.json()

cik_data = json.dumps(cik)

# Create lib/cik_local.json:
f = open("../lib/cik_local.json", "w")
f.write(cik_data)
f.close()

# Create lib/cik_local.js:
doc_body = f"""export const tickerSymbols = {cik_data}"""
f = open("../lib/cik_local.js", "w")
f.write(doc_body)
f.close()

# Create lib/cik_local.py:
# doc_body = f"""tickerSymbols = {cik_data}"""
# data_list = list(cik.values())
doc_body = f"""companies_dict = {cik}"""
f = open("../lib/cik_local.py", "w")
f.write(doc_body)
f.close()

print("done! I've updated /lib/cik_local.json, cik_local.js and cik_local.py")
