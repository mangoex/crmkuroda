const fs = require('fs');
const app = fs.readFileSync('static/app.js', 'utf8');
app.split('\n').forEach((l, i) => {
  if (l.includes('.includes("@")')) console.log(i + 1, l.trim());
});
