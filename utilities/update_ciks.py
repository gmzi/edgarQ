import requests
import json
import os

"""
This script updates the list of CIKs that flask route will consume.
It requests the new CIKS from SEC api and rewrites `lib/cik_local.json`. 
Run with these commands:
                    1. Make a backup of /lib/cik_local.json
                    1. `cd utilities`
                    2. `python3 update_ciks.py`
"""

USER_AGENT = os.environ.get('USER_AGENT')


headers = {'User-Agent': f"{USER_AGENT}"}

tickers_cik = requests.get(
    "https://www.sec.gov/files/company_tickers.json", headers=headers)

cik = tickers_cik.json()

result = json.dumps(cik)
f = open("../lib/cik_local.json", "w")
f.write(result)
f.close()

print('done')
