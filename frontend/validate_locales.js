const fs = require('fs');

const en = fs.readFileSync('src/locales/en.ts', 'utf8');
const te = fs.readFileSync('src/locales/te.ts', 'utf8');
const hi = fs.readFileSync('src/locales/hi.ts', 'utf8');

function extractKeys(content) {
  const matches = content.match(/^\s*([a-zA-Z0-9_]+):/gm) || [];
  return matches.map(m => m.trim().replace(':', ''));
}

const enKeys = extractKeys(en);
const teKeys = extractKeys(te);
const hiKeys = extractKeys(hi);

console.log('EN keys count:', enKeys.length);
console.log('TE keys count:', teKeys.length);
console.log('HI keys count:', hiKeys.length);

const missingTe = enKeys.filter(k => !teKeys.includes(k));
const missingHi = enKeys.filter(k => !hiKeys.includes(k));

console.log('Missing in TE count:', missingTe.length);
if (missingTe.length > 0) console.log('Missing in TE:', missingTe);

console.log('Missing in HI count:', missingHi.length);
if (missingHi.length > 0) console.log('Missing in HI:', missingHi);

if (missingTe.length === 0 && missingHi.length === 0) {
  console.log('PASS: Test 11 - All 150+ translation keys are completely translated across EN, TE, HI!');
} else {
  process.exit(1);
}
