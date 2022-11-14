# edgarQ

Query [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation) by company concept using python. A serverless Flask route and helper functions to send requests and process responses. Information is not accurate and there's a lot to explore. Please fork / refactor / contribute.

## Usage

1. Create an .env file in project root, and add this:  
   USER_AGENT="[your email of choice]"
2. Run locally with `vercel dev` command. (You might have to install the vercel CLI, if so you can find instructions [here](https://vercel.com/docs/cli)).
3. Make queries with either of these two urls:
   - `http://localhost:3000/pages?` to see a basic form, add a ticker symbol and submit to retrieve data.
   - `http://localhost:3000/api/data?ticker=--example--` (replace "--example--" with a valid ticker symbol) to see data in json format.
4. Data returned in .json format and as an html string formatted with table tags.

## Updates

In case the list of CIK numbers stored locally at /lib/cik_local.json needs to be updated, you can find a script to automatically do so in /utilities/update_ciks.py
