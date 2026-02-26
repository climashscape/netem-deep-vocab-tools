const fs = require('fs');
const path = require('path');

const staticDir = path.join(__dirname, 'explain_verbs/static');
const jsDir = path.join(staticDir, 'js');

if (!fs.existsSync(jsDir)) {
    fs.mkdirSync(jsDir, { recursive: true });
}

// Convert netem_full_list.json
const fullListPath = path.join(staticDir, 'netem_full_list.json');
const fullListJsPath = path.join(jsDir, 'data_full_list.js');
try {
    const data = fs.readFileSync(fullListPath, 'utf8');
    // Minimal minification: remove newlines/spaces if JSON structure allows, 
    // but JSON.stringify usually handles it well.
    const content = `window.NETEM_FULL_LIST = ${data};`;
    fs.writeFileSync(fullListJsPath, content);
    console.log(`Converted netem_full_list.json to JS (${(fs.statSync(fullListJsPath).size / 1024 / 1024).toFixed(2)} MB)`);
} catch (e) {
    console.error("Failed to convert full list:", e);
}

// Convert legacy_data.json
const legacyPath = path.join(staticDir, 'legacy_data.json');
const legacyJsPath = path.join(jsDir, 'data_legacy.js');
try {
    const data = fs.readFileSync(legacyPath, 'utf8');
    const content = `window.NETEM_LEGACY_DATA = ${data};`;
    fs.writeFileSync(legacyJsPath, content);
    console.log(`Converted legacy_data.json to JS (${(fs.statSync(legacyJsPath).size / 1024 / 1024).toFixed(2)} MB)`);
} catch (e) {
    console.error("Failed to convert legacy data:", e);
}
