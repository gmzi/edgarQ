# edgarQ

Query [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation) by company concept using python. A serverless Flask route and helper functions to send requests and process responses. Live price data is requested from [FMP](https://site.financialmodelingprep.com) and used to calculate EPS to price ratios.

Information is not accurate and there's a lot to explore. Please fork / refactor / contribute.

## Usage

1. Create an .env file in project root, and add this:  
   BASE_URL="http://localhost:3000/api"
   USER_AGENT="[your email of choice]"
   FMP_API_KEY="your api key". (Obtain yours [here](https://site.financialmodelingprep.com))
2. Run locally with `vercel dev` command. (You might have to install the vercel CLI, if so you can find instructions [here](https://vercel.com/docs/cli)).
3. Make queries with either of these two urls:
   - `http://localhost:3000` to see a basic form, add a ticker symbol and submit to display all data as a prettified json.
   - `http://localhost:3000/api/<function>?ticker=<example>` to display a particular company concept. (replace `<function>` with any of the file names inside /api, and `<example>` with a valid ticker symbol).
     - Sample request: `http://localhost:3000/api/net_income?ticker=meli`
     - Sample response: `{"net_income_data": {"2021": "83.30M", "2020": "-707.00K", "2019": "-172.00M", "2018": "-36.59M", "2017": "13.78M", "2016": "136.37M", "2015": "105.79M", "2014": "72.58M", "2013": "117.51M", "2012": "101.25M", "2011": "76.80M", "2010": "56.03M", "2009": "33.21M", "2008": "18.81M"}}`
     - Data is returned as a .json object with two fields: `_data` is pure .json data, and `name` is the same data formatted as an html string with `html <table>` tags added.

## Updates

In case the list of CIK numbers stored locally at /lib/cik_local.json needs to be updated, you can find a script to automatically do so in /utilities/update_ciks.py
