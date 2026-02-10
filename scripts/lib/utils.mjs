/**
 * Shared utilities for triple verification hooks.
 * Zero dependencies — Node.js built-ins only.
 */

import { resolve, dirname } from 'node:path';
import { existsSync } from 'node:fs';

/**
 * Read all of stdin as a string. Returns parsed JSON.
 * Claude Code pipes hook input as a single JSON blob on stdin.
 */
export async function readStdinJSON() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks).toString('utf-8').trim();
  if (!raw) return null;
  return JSON.parse(raw);
}

/**
 * Output a blocking denial to stdout.
 * Claude Code reads this and prevents the tool call.
 */
export function deny(reason) {
  const output = {
    decision: 'block',
    reason
  };
  process.stdout.write(JSON.stringify(output));
}

/**
 * Output approval to stdout.
 */
export function approve() {
  const output = { decision: 'approve' };
  process.stdout.write(JSON.stringify(output));
}

/**
 * Detect file extension from a file path string.
 * Returns lowercase extension with dot (e.g. ".py", ".js") or "" if none.
 */
export function getFileExtension(filePath) {
  if (!filePath || typeof filePath !== 'string') return '';
  const lastDot = filePath.lastIndexOf('.');
  if (lastDot === -1 || lastDot === filePath.length - 1) return '';
  return filePath.slice(lastDot).toLowerCase();
}

/**
 * Check if a file path is a research markdown file.
 * Returns true if extension is .md AND path contains /research/ or filename contains "research".
 * Normalizes backslashes for cross-OS support.
 */
export function isResearchFile(filePath) {
  if (!filePath || typeof filePath !== 'string') return false;
  const normalized = filePath.replace(/\\/g, '/').toLowerCase();
  if (!normalized.endsWith('.md')) return false;
  // Path contains a /research/ directory segment OR filename contains "research"
  const fileName = normalized.split('/').pop() || '';
  return normalized.includes('/research/') || fileName.includes('research');
}

/**
 * Determine the project root directory.
 * Walks up from CWD looking for .git, package.json, or .claude directory.
 * Falls back to CWD.
 */
export function findProjectRoot(startDir) {
  let dir = startDir || process.cwd();
  const markers = ['.git', 'package.json', '.claude'];

  for (let i = 0; i < 20; i++) {
    for (const marker of markers) {
      if (existsSync(resolve(dir, marker))) {
        return dir;
      }
    }
    const parent = dirname(dir);
    if (parent === dir) break; // reached filesystem root
    dir = parent;
  }
  return startDir || process.cwd();
}

/**
 * Get the plugin's own root directory (two levels up from scripts/lib/).
 */
export function getPluginRoot() {
  return resolve(dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '..', '..');
}

/**
 * Generate a session ID from environment or timestamp.
 * Cached per process so all log entries go to the same file.
 */
let _cachedSessionId = null;
export function getSessionId() {
  if (!_cachedSessionId) {
    _cachedSessionId = process.env.CLAUDE_SESSION_ID || `session-${Date.now()}`;
  }
  return _cachedSessionId;
}

/**
 * Safe wrapper — catches errors and exits cleanly (fail-open).
 * If the hook crashes, the operation proceeds rather than blocking Claude.
 */
export async function failOpen(fn) {
  try {
    await fn();
  } catch (err) {
    // Fail open: print nothing (or approve), exit 0
    // Log error to stderr for debugging but don't block
    process.stderr.write(`[triple-verify] Error (fail-open): ${err.message}\n`);
    process.exit(0);
  }
}
