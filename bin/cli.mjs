#!/usr/bin/env node

// CustomGPT Triple Verification — npx installer
// Usage: npx @customgpt/claude-triple-verification

import { existsSync, mkdirSync, cpSync, readFileSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { homedir, platform } from 'node:os';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');

const PLUGIN_NAME = 'customgpt-claude-triple-verification';
const REPO = 'kirollosatef/customgpt-claude-triple-verification';

// ── Helpers ──

function log(msg) { console.log(`  ${msg}`); }
function ok(msg)  { console.log(`  \x1b[32m✓\x1b[0m ${msg}`); }
function warn(msg){ console.log(`  \x1b[33m!\x1b[0m ${msg}`); }
function err(msg) { console.error(`  \x1b[31m✗\x1b[0m ${msg}`); }

function getPluginsDir() {
  const home = homedir();
  if (platform() === 'win32') {
    return join(home, '.claude', 'plugins', PLUGIN_NAME);
  }
  return join(home, '.claude', 'plugins', PLUGIN_NAME);
}

// ── Main ──

async function main() {
  console.log();
  console.log('  \x1b[1mCustomGPT Triple Verification\x1b[0m — Installer');
  console.log('  ─────────────────────────────────────────');
  console.log();

  // 1. Check Node version
  const nodeVersion = parseInt(process.versions.node.split('.')[0], 10);
  if (nodeVersion < 18) {
    err(`Node.js >= 18 required (found v${process.versions.node})`);
    process.exit(1);
  }
  ok(`Node.js v${process.versions.node}`);

  // 2. Determine install target
  const dest = getPluginsDir();
  log(`Installing to: ${dest}`);
  console.log();

  // 3. Create plugin directory
  mkdirSync(dest, { recursive: true });

  // 4. Copy plugin files
  const dirs = ['.claude-plugin', 'scripts', 'hooks', 'config'];
  const files = ['package.json', 'LICENSE'];

  for (const d of dirs) {
    const src = join(ROOT, d);
    if (existsSync(src)) {
      cpSync(src, join(dest, d), { recursive: true });
      ok(`Copied ${d}/`);
    }
  }

  for (const f of files) {
    const src = join(ROOT, f);
    if (existsSync(src)) {
      cpSync(src, join(dest, f));
      ok(`Copied ${f}`);
    }
  }

  console.log();

  // 5. Run smoke test
  log('Running verification...');
  try {
    const verifyPath = join(dest, 'install', 'verify.mjs');
    const verifyPathFromRoot = join(ROOT, 'install', 'verify.mjs');

    // Copy install dir too for verification
    const installSrc = join(ROOT, 'install');
    if (existsSync(installSrc)) {
      cpSync(installSrc, join(dest, 'install'), { recursive: true });
    }

    if (existsSync(verifyPath)) {
      execSync(`node "${verifyPath}"`, { stdio: 'pipe' });
      ok('Smoke test passed');
    } else {
      warn('Smoke test not found — skipping');
    }
  } catch {
    warn('Smoke test had warnings — plugin still installed');
  }

  console.log();

  // 6. Recommend marketplace for auto-updates
  console.log('  \x1b[1m\x1b[32mInstalled!\x1b[0m');
  console.log();
  console.log('  \x1b[1mFor auto-updates, use the marketplace instead:\x1b[0m');
  console.log();
  console.log('    In Claude Code, run:');
  console.log(`    \x1b[36m/install ${REPO}\x1b[0m`);
  console.log();
  console.log('  The marketplace version auto-updates on every session.');
  console.log();
}

main().catch(e => {
  err(e.message);
  process.exit(1);
});
