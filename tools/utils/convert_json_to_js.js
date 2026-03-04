const fs = require('fs');
const path = require('path');

// Paths relative to tools/utils/
const toolsDir = path.join(__dirname, '..');
const appStaticDir = path.join(__dirname, '../../app/static');
const dataDir = path.join(toolsDir, 'data');
const jsDir = path.join(appStaticDir, 'js');

if (!fs.existsSync(jsDir)) {
    fs.mkdirSync(jsDir, { recursive: true });
}

// Convert netem_full_list.json
const fullListPath = path.join(dataDir, 'netem_full_list.json');
const fullListJsPath = path.join(jsDir, 'data_full_list.js');
try {
    if (fs.existsSync(fullListPath)) {
        const data = fs.readFileSync(fullListPath, 'utf8');
        const content = `window.NETEM_FULL_LIST = ${data};`;
        fs.writeFileSync(fullListJsPath, content);
        console.log(`Converted netem_full_list.json to JS (${(fs.statSync(fullListJsPath).size / 1024 / 1024).toFixed(2)} MB)`);
    } else {
        console.warn(`Source not found: ${fullListPath}`);
    }
} catch (e) {
    console.error("Failed to convert full list:", e);
}

// Convert legacy_data.json
// Source is in app/static/legacy_data.json as it is the master copy for now
const legacyPath = path.join(appStaticDir, 'legacy_data.json');
const legacyJsPath = path.join(jsDir, 'data_legacy.js');
try {
    if (fs.existsSync(legacyPath)) {
        const data = fs.readFileSync(legacyPath, 'utf8');
        const content = `window.NETEM_LEGACY_DATA = ${data};`;
        fs.writeFileSync(legacyJsPath, content);
        console.log(`Converted legacy_data.json to JS (${(fs.statSync(legacyJsPath).size / 1024 / 1024).toFixed(2)} MB)`);
    } else {
        console.warn(`Source not found: ${legacyPath}`);
    }
} catch (e) {
    console.error("Failed to convert legacy data:", e);
}
