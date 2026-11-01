const fs = require('node:fs');
const path = require('node:path');

// Publish an explicit site boundary, never the repository/build workspace.
const SITE_FILES = ['index.html', 'ticker.html', 'history.html', 'manifest.webmanifest',
  'data/latest.json', 'data/history.json', 'data/market-brief.json'];
const ASSET_EXTENSIONS = new Set(['.js', '.css', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.ico', '.woff', '.woff2']);

function buildSite(root = path.resolve(__dirname, '..')) {
  const output = path.join(root, 'dist');
  fs.rmSync(output, { recursive: true, force: true });
  let bytes = 0;
  let count = 0;
  function copy(relative) {
    const source = path.join(root, relative);
    if (!fs.lstatSync(source).isFile()) throw new Error(`Expected a regular site file: ${relative}`);
    const target = path.join(output, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(source, target);
    bytes += fs.statSync(target).size;
    count++;
  }
  SITE_FILES.forEach(copy);
  function assets(relative) {
    for (const entry of fs.readdirSync(path.join(root, relative), { withFileTypes: true })) {
      if (entry.name.startsWith('.')) continue;
      const file = path.join(relative, entry.name);
      if (entry.isDirectory()) assets(file);
      else if (entry.isFile() && ASSET_EXTENSIONS.has(path.extname(entry.name))) copy(file);
      else throw new Error(`Unexpected static asset: ${file}`);
    }
  }
  assets('assets');
  console.log(`Static site: ${count} files, ${bytes} bytes in dist/`);
  return { count, bytes };
}

if (require.main === module) buildSite();
module.exports = { buildSite };
