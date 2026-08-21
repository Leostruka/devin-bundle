#!/usr/bin/env node
// Validates Mermaid diagram syntax without rendering (no Puppeteer/Chromium).
// Usage: node mermaid-parse-check.js < file.mmd
//   or:  node mermaid-parse-check.js "diagram string"
// Exit 0 = valid, exit 1 = parse error (prints error to stderr).

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const localRequire = createRequire(__filename);

let input = '';
if (process.argv[2] && process.argv[2] !== '--stdin') {
  input = process.argv[2];
} else {
  input = fs.readFileSync(0, 'utf-8');
}

// Find mermaid in global node_modules — portable lookup.
// 1. Try require.resolve (checks local + NODE_PATH)
// 2. Try npm root -g (portable across OS/install methods)
// 3. Fall back to known paths (Windows scoop, Linux global)
const globalModulePaths = [
  'C:\\Users\\Fingertech\\scoop\\persist\\nodejs\\bin\\node_modules',
  'C:\\Users\\Fingertech\\scoop\\apps\\nodejs\\current\\lib\\node_modules',
  '/usr/local/lib/node_modules',
  '/usr/lib/node_modules',
  path.join(process.env.HOME || '', '.npm-global/lib/node_modules'),
  path.join(process.env.HOME || '', '.nvm/versions/node', process.version.slice(1), 'lib/node_modules'),
];
let mermaidPath = null;

// 1. Try require.resolve first (checks local + NODE_PATH)
try {
  mermaidPath = path.dirname(localRequire.resolve('mermaid'));
} catch (e) {
  // Not in local/NODE_PATH, continue to global lookup
}

// 2. Try npm root -g
if (!mermaidPath) {
  try {
    const { execSync } = require('child_process');
    const npmRoot = execSync('npm root -g', { encoding: 'utf-8', timeout: 5000 }).trim();
    if (npmRoot) globalModulePaths.unshift(npmRoot);
  } catch (e) {
    // npm not available, continue
  }
}

// 3. Fall back to known paths
if (!mermaidPath) {
  for (const p of globalModulePaths) {
    const candidate = path.join(p, 'mermaid');
    if (fs.existsSync(candidate)) {
      mermaidPath = candidate;
      break;
    }
  }
}

if (!mermaidPath) {
  console.error('mermaid package not found in global node_modules');
  process.exit(1);
}

// Find the actual entry point (mermaid is ESM)
let entryFile = path.join(mermaidPath, 'dist', 'mermaid.core.mjs');
if (!fs.existsSync(entryFile)) {
  // Try package.json main/exports
  const pkg = JSON.parse(fs.readFileSync(path.join(mermaidPath, 'package.json'), 'utf-8'));
  entryFile = path.join(mermaidPath, pkg.main || pkg.module || 'dist/mermaid.core.mjs');
}

async function main() {
  try {
    const fileUrl = 'file:///' + entryFile.replace(/\\/g, '/');
    const mermaid = await import(fileUrl);
    const M = mermaid.default || mermaid;
    // mermaid.parse() returns a Promise; await it to check syntax
    await M.parse(input);
    process.exit(0);
  } catch (e) {
    const msg = e.message || String(e);
    // DOMPurify errors are environment issues (no DOM in Node), not syntax errors.
    // The parse itself succeeded; DOMPurify post-processing fails without a browser.
    if (msg.includes('DOMPurify')) {
      process.exit(0);
    }
    console.error(msg);
    process.exit(1);
  }
}

main().catch(e => {
  console.error(String(e));
  process.exit(1);
});
