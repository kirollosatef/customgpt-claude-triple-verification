#!/usr/bin/env node

/**
 * Post-Tool Audit — Non-blocking audit logger for every tool operation.
 *
 * This PostToolUse hook:
 *   1. Reads the tool execution result from stdin
 *   2. Logs the operation to the JSONL audit trail
 *   3. Always exits 0 (never blocks)
 *
 * This provides full auditability of every Claude Code operation.
 */

import { readStdinJSON, isResearchFile, failOpen } from './lib/utils.mjs';
import { logPostTool } from './lib/audit-logger.mjs';

await failOpen(async () => {
  const input = await readStdinJSON();
  if (!input) {
    process.exit(0);
  }

  const toolName = input.tool_name || 'unknown';
  const toolInput = input.tool_input || {};

  // Extract relevant metadata (avoid logging full content for privacy)
  const metadata = {};

  if (toolInput.file_path) {
    metadata.filePath = toolInput.file_path;
  }
  if (toolInput.command) {
    // Log first 200 chars of command for auditability without excessive data
    metadata.command = toolInput.command.slice(0, 200);
  }
  if (toolInput.url) {
    metadata.url = toolInput.url;
  }
  if (toolInput.pattern) {
    metadata.pattern = toolInput.pattern;
  }

  // Add applicable cycles context based on file type
  if (toolInput.file_path) {
    metadata.applicableCycles = isResearchFile(toolInput.file_path)
      ? 'Cycle 4 (Research Verification)'
      : 'Cycles 1-3';
  }

  // Log the tool use
  logPostTool(toolName, metadata);

  // Always exit cleanly — never block
  process.exit(0);
});
