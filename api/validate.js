// http://localhost:3000/api/validate?ticker=meli
import { tickerSymbols } from '../lib/cik_local';

export default function handler(req, res) {
  const ticker = req.query.ticker.toLowerCase();
  const validTickers = Object.values(tickerSymbols);
  const isValid = validTickers.find((symbol) => {
    if (symbol.ticker.toLowerCase() === ticker) {
      return symbol;
    }
  });
  return res.status(200).json({ data: isValid });
}
