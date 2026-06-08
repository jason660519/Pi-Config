// swarm-browse v0.1 stub. Prints planned actions to stdout so /qa and /design-review
// can wire against the real API today; M1.5 swaps in a Playwright backend without
// touching callers.

import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const HOME = process.env.HIVESTACK_HOME ?? join(homedir(), '.hivestack');

const COMMANDS = new Set([
  'open', 'screenshot', 'click', 'fill', 'wait',
  'network', 'console', 'close', 'version', 'help',
]);

function usage() {
  return [
    'swarm-browse v0.1 (stub)',
    '',
    'Usage:',
    '  swarm-browse open <url>',
    '  swarm-browse screenshot [--out <path>] [--full]',
    '  swarm-browse click <selector>',
    '  swarm-browse fill <selector> <value>',
    '  swarm-browse wait <selector> [--timeout <ms>]',
    '  swarm-browse network [--since <ts>]',
    '  swarm-browse console [--since <ts>]',
    '  swarm-browse close',
    '  swarm-browse version',
    '',
    'Stub mode: prints planned actions, does not launch a browser yet.',
    'Real backend lands in M1.5 (Playwright + CDP).',
  ].join('\n');
}

function writeStubEvent(kind, payload) {
  try {
    const dir = join(HOME, 'analytics');
    mkdirSync(dir, { recursive: true });
    const line = JSON.stringify({
      ts: new Date().toISOString(),
      tool: 'swarm-browse',
      kind,
      ...payload,
    }) + '\n';
    writeFileSync(join(dir, 'tool-usage.jsonl'), line, { flag: 'a' });
  } catch {
    // best effort; never fail the caller because of telemetry
  }
}

export async function run(argv) {
  const cmd = argv[0];
  if (!cmd || cmd === 'help' || cmd === '--help' || cmd === '-h') {
    process.stdout.write(usage() + '\n');
    return 0;
  }
  if (cmd === 'version' || cmd === '--version' || cmd === '-v') {
    process.stdout.write('swarm-browse 0.1.0 (stub)\n');
    return 0;
  }
  if (!COMMANDS.has(cmd)) {
    process.stderr.write(`swarm-browse: unknown command "${cmd}"\n${usage()}\n`);
    return 2;
  }
  const args = argv.slice(1);
  process.stdout.write(`stub: ${cmd} ${args.join(' ')}\n`);
  writeStubEvent(cmd, { args });
  return 0;
}
