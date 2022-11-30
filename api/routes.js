const fs = require('fs');
const routes = fs.readdirSync('./api');

export default function handler(req, res) {
    
  res.status(200).json({ routes: routes });
}
