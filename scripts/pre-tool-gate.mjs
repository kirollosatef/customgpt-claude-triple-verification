#!/usr/bin/env node

/**
 * Pre-Tool Gate — Cycle 1 (Code Quality) + Cycle 2 (Security) enforcement.
 *
 * This is the main PreToolUse hook dispatcher. It:
 *   1. Reads the hook input from stdin (JSON)
 *   2. Extracts the content to verify based on tool type
 *   3. Runs Cycle 1 (quality) and Cycle 2 (security) rules
 *   4. Outputs { decision: "block", reason: "..." } on violation
 *   5. Logs the decision to the audit trail
 *   6. Fails open on any crash (operation proceeds)
 *
 * Supported tools:
 *   - Write (content field)
 *   - Edit (new_string field)
 *   - Bash (command field)
 *   - MCP tools (input fields)
 *   - WebFetch/WebSearch (url field)
 */

import { readStdinJSON, deny, approve, getFileExtension, isResearchFile, failOpen } from './lib/utils.mjs';
import { runCycle1, runCycle2 } from './lib/rules-engine.mjs';
import { runCycle4 } from './lib/research-verifier.mjs';
import { logPreTool } from './lib/audit-logger.mjs';
import { loadConfig } from './lib/config-loader.mjs';

await failOpen(async () => {
  const input = await readStdinJSON();
  if (!input) {
    approve();
    process.exit(0);
  }

  const config = loadConfig();
  const toolName = input.tool_name || '';
  const toolInput = input.tool_input || {};

  // Determine what content to verify and what context to use
  const { content, context, fileExt, filePath } = extractContent(toolName, toolInput);

  if (!content) {
    // No content to verify — approve
    logPreTool(toolName, 'approve', [], { reason: 'no-content' });
    approve();
    process.exit(0);
  }

  // Route to the appropriate verification cycles
  let allViolations;

  if (isResearchFile(filePath) && config.cycle4?.enabled !== false) {
    // Research files → Cycle 4 only
    allViolations = runCycle4(content, filePath, config);
  } else {
    // All other files → Cycles 1 + 2
    const cycle1Violations = runCycle1(content, fileExt, context, config);
    const cycle2Violations = runCycle2(content, fileExt, context, config);
    allViolations = [...cycle1Violations, ...cycle2Violations];
  }

  if (allViolations.length > 0) {
    // Format violation messages
    const reasons = allViolations.map(v =>
      `[Cycle ${v.cycle} - ${v.ruleId}] ${v.message}`
    );
    const reasonText = `Triple Verification BLOCKED this operation:\n\n${reasons.join('\n\n')}\n\nFix these issues and try again.`;

    logPreTool(toolName, 'block', allViolations, { fileExt, context });
    deny(reasonText);
  } else {
    logPreTool(toolName, 'approve', [], { fileExt, context });
    approve();
  }
});

/**
 * Extract verifiable content from tool input based on tool type.
 */
function extractContent(toolName, toolInput) {
  const normalized = toolName.toLowerCase();

  const filePath = toolInput.file_path || '';

  // Write tool — verify file content
  if (normalized === 'write') {
    return {
      content: toolInput.content || '',
      context: 'file-write',
      fileExt: getFileExtension(filePath),
      filePath
    };
  }

  // Edit tool — verify new_string
  if (normalized === 'edit') {
    return {
      content: toolInput.new_string || '',
      context: 'file-write',
      fileExt: getFileExtension(filePath),
      filePath
    };
  }

  // Bash tool — verify command
  if (normalized === 'bash') {
    return {
      content: toolInput.command || '',
      context: 'bash',
      fileExt: '',
      filePath: ''
    };
  }

  // WebFetch / WebSearch — verify URL
  if (normalized === 'webfetch' || normalized === 'websearch') {
    return {
      content: toolInput.url || toolInput.query || '',
      context: 'web',
      fileExt: '',
      filePath: ''
    };
  }

  // MCP tools (prefixed with mcp__) — verify all input values
  if (normalized.startsWith('mcp__') || normalized.startsWith('mcp_')) {
    const values = Object.values(toolInput)
      .filter(v => typeof v === 'string')
      .join('\n');
    return {
      content: values,
      context: 'mcp',
      fileExt: '',
      filePath: ''
    };
  }

  // Unknown tool — nothing to verify
  return { content: '', context: 'unknown', fileExt: '', filePath: '' };
}
