const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { buildSite } = require('./build_vercel_site.cjs');

test('deployment keeps browser resources and excludes polluted build workspace', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vercel-site-'));
  const source = path.resolve(__dirname, '..');
  try {
    for (const entry of ['index.html', 'ticker.html', 'history.html', 'manifest.webmanifest', 'assets', 'data']) {
      fs.cpSync(path.join(source, entry), path.join(root, entry), { recursive: true });
    }
    for (const entry of ['.env', '.github/workflows/test.yml', '.vercel_python_packages/numpy/core.so', 'api/private.js', 'dist/stale.js']) {
      const target = path.join(root, entry);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, 'must not be published');
    }
    const result = buildSite(root);
    const output = path.join(root, 'dist');
    assert(result.bytes < 5_000_000, 'unexpected static output growth');
    assert.deepEqual(fs.readdirSync(output).sort(), ['assets', 'data', 'history.html', 'index.html', 'manifest.webmanifest', 'ticker.html']);
    for (const page of ['index.html', 'ticker.html', 'history.html']) {
      const html = fs.readFileSync(path.join(output, page), 'utf8');
      for (const match of html.matchAll(/(?:src|href)="\.\/([^"?#]+)(?:[?#][^"]*)?"/g)) {
        assert(fs.existsSync(path.join(output, match[1])), `${page} missing ${match[1]}`);
      }
    }
    const manifest = JSON.parse(fs.readFileSync(path.join(output, 'manifest.webmanifest')));
    for (const icon of manifest.icons) assert(fs.existsSync(path.join(output, icon.src)));
    for (const file of ['latest.json', 'history.json', 'market-brief.json']) {
      assert.deepEqual(fs.readFileSync(path.join(output, 'data', file)), fs.readFileSync(path.join(source, 'data', file)));
    }
    assert(!fs.existsSync(path.join(output, 'stale.js')));
    assert.equal(JSON.parse(fs.readFileSync(path.join(source, 'vercel.json'))).outputDirectory, 'dist');
    // API source stays at the repository root for Vercel's separate Function build.
    for (const file of ['company.js', 'focus-list.js', 'ticker/[ticker].js', 'watchlist/latest.js']) {
      assert.equal(typeof require(path.join(source, 'api', file)), 'function');
    }
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
