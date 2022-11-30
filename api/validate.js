// http://localhost:3000/api/routes?ticker=abc
const fs = require('fs');

export default function handler(req, res) {
  const ticker = req.query.ticker;
  const routes = fs.readdirSync('./api');
  fs.readFile('./lib/cik_local.json', 'utf-8', (error, data) => {
    if (error) {
      console.log(error);
      return res.status(500).json({ error: 'failed when reading json file' });
    }
    const obj_tickerSymbols = JSON.parse(data);
    const tickerSymbols = Object.values(obj_tickerSymbols);
    const isValid = tickerSymbols.find((symbol) => {
      if (symbol.ticker.toLowerCase() === ticker.toLowerCase()) {
        return symbol;
      }
    });
    return res.status(200).json({ routes: routes, data: isValid });
  });
}
