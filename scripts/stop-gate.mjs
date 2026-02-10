#!/usr/bin/env node

/**
 * Stop Gate — Cycle 4 research file scan at session end.
 *
 * This Stop (command) hook:
 *   1. Finds research .md files in docs/research/, research/, and docs/ directories
 *   2. Reads each file and runs Cycle 4 verification
 *   3. Blocks session end if any violations are found
 *   4. Respects config.cycle4.enabled toggle
 *   5. Fails open on any crash (session proceeds)
 *
 * Zero dependencies — Node.js built-ins only.
 */

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { deny, approve, isResearchFile, failOpen, findProjectRoot } from './lib/utils.mjs';
import { runCycle4 } from './lib/research-verifier.mjs';
import { loadConfig } from './lib/config-loader.mjs';

await failOpen(async () => {
  const config = loadConfig();

  // Check if Cycle 4 is enabled
  if (config.cycle4?.enabled === false) {
    approve();
    process.exit(0);
  }

  const projectRoot = findProjectRoot(process.cwd());

  // Directories to scan for research files
  const searchDirs = [
    resolve(projectRoot, 'docs', 'research'),
    resolve(projectRoot, 'research'),
    resolve(projectRoot, 'docs')
  ];

  const violations = [];

  for (const dir of searchDirs) {
    if (!existsSync(dir)) continue;

    const files = findMarkdownFiles(dir, 5);
    for (const filePath of files) {
      if (!isResearchFile(filePath)) continue;

      try {
        const content = readFileSync(filePath, 'utf-8');
        const fileViolations = runCycle4(content, filePath, config);
        if (fileViolations.length > 0) {
          violations.push({ filePath, violations: fileViolations });
        }
      } catch {
        // Skip unreadable files
      }
    }
  }

  if (violations.length > 0) {
    const summary = violations.map(({ filePath, violations: vs }) => {
      const msgs = vs.map(v => `  [Cycle ${v.cycle} - ${v.ruleId}] ${v.message}`).join('\n');
      return `File: ${filePath}\n${msgs}`;
    }).join('\n\n');

    deny(`Triple Verification BLOCKED session completion:\n\n${summary}\n\nFix these research file issues before completing.`);
  } else {
    approve();
  }
});

/**
 * Recursively find .md files in a directory, up to maxDepth levels.
 * Skips node_modules and dot-directories.
 */
function findMarkdownFiles(dir, maxDepth, currentDepth = 0) {
  if (currentDepth >= maxDepth) return [];

  const results = [];

  try {
    const entries = readdirSync(dir);
    for (const entry of entries) {
      // Skip node_modules and dot-directories
      if (entry === 'node_modules' || entry.startsWith('.')) continue;

      const fullPath = join(dir, entry);
      try {
        const stat = statSync(fullPath);
        if (stat.isDirectory()) {
          results.push(...findMarkdownFiles(fullPath, maxDepth, currentDepth + 1));
        } else if (stat.isFile() && entry.endsWith('.md')) {
          results.push(fullPath);
        }
      } catch {
        // Skip inaccessible entries
      }
    }
  } catch {
    // Skip inaccessible directories
  }

  return results;
}
