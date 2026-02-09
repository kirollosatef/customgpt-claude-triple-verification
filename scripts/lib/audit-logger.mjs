/**
 * Audit Logger — Writes JSONL structured logs for every tool operation.
 *
 * Log location priority:
 *   1. $PROJECT/.claude/triple-verify-audit/SESSION_ID.jsonl
 *   2. ~/.claude/triple-verify-audit/SESSION_ID.jsonl (fallback)
 *
 * Zero dependencies — Node.js built-ins only.
 */

import { appendFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { homedir } from 'node:os';
import { getSessionId, findProjectRoot } from './utils.mjs';

/**
 * Determine the audit log directory.
 */
function getAuditDir(config = {}) {
  // Config override
  if (config.auditDir) {
    return config.auditDir;
  }

  // Try project-level first
  const projectRoot = findProjectRoot(process.cwd());
  const projectAuditDir = resolve(projectRoot, '.claude', 'triple-verify-audit');

  // Check if .claude dir exists (or can be created) at project root
  const claudeDir = resolve(projectRoot, '.claude');
  if (existsSync(claudeDir)) {
    return projectAuditDir;
  }

  // Fallback to user home
  return resolve(homedir(), '.claude', 'triple-verify-audit');
}

/**
 * Get the full path to the current session's log file.
 */
function getLogFilePath(config = {}) {
  const dir = getAuditDir(config);
  const sessionId = getSessionId();
  return join(dir, `${sessionId}.jsonl`);
}

/**
 * Write a single audit log entry.
 *
 * @param {object} entry - The log entry data
 * @param {string} entry.event - Event type: 'pre-tool', 'post-tool', 'stop'
 * @param {string} entry.tool - Tool name (e.g. 'Write', 'Bash', 'Edit')
 * @param {string} entry.decision - 'approve' | 'block' | 'log-only'
 * @param {Array} [entry.violations] - Violations found (if any)
 * @param {object} [entry.metadata] - Additional context
 * @param {object} [config] - Config overrides
 */
export function logEntry(entry, config = {}) {
  try {
    const logPath = getLogFilePath(config);
    const dir = resolve(logPath, '..');

    // Ensure directory exists
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    const record = {
      timestamp: new Date().toISOString(),
      sessionId: getSessionId(),
      event: entry.event,
      tool: entry.tool,
      decision: entry.decision,
      violations: entry.violations || [],
      metadata: entry.metadata || {},
    };

    appendFileSync(logPath, JSON.stringify(record) + '\n', 'utf-8');
  } catch (err) {
    // Audit logging must never block operations
    process.stderr.write(`[triple-verify] Audit log error: ${err.message}\n`);
  }
}

/**
 * Log a pre-tool verification result.
 */
export function logPreTool(tool, decision, violations = [], metadata = {}, config = {}) {
  logEntry({
    event: 'pre-tool',
    tool,
    decision,
    violations,
    metadata
  }, config);
}

/**
 * Log a post-tool execution.
 */
export function logPostTool(tool, metadata = {}, config = {}) {
  logEntry({
    event: 'post-tool',
    tool,
    decision: 'log-only',
    metadata
  }, config);
}

/**
 * Log a stop verification result.
 */
export function logStop(decision, metadata = {}, config = {}) {
  logEntry({
    event: 'stop',
    tool: 'Stop',
    decision,
    metadata
  }, config);
}
