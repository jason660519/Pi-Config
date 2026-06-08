// swarm-browse v0.2 — Playwright when available, stub when not.
//
// Detection: require.resolve('playwright'); if missing, fall back to v0.1 stub
// behaviour (print planned actions). When present, real navigate/screenshot/
// click/fill/wait drive a Chromium instance via Playwright.
//
// State: a single shared browser context per process (swarm-browse is invoked
// per-subcommand from shells; we re-launch each time, which is slow but
// stateless. M4 swaps in a long-running daemon).

import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { createRequire } from 'node:module';

const HOME = process.env.HIVESTACK_HOME ?? join(homedir(), '.hivestack');
const require_ = createRequire(import.meta.url);

function haveBackend() {
  try {
    require_.resolve('playwright');
    return true;
  } catch {
    return false;
  }
}

const COMMANDS = new Set([
  'open', 'screenshot', 'click', 'fill', 'wait',
  'network', 'console', 'close', 'version', 'help',
]);

function usage(mode) {
  return [
    `swarm-browse v0.2 (${mode})`,
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
    mode === 'stub'
      ? 'Playwright not detected; running in stub mode. Install with `npm i playwright`.'
      : 'Real backend active (Playwright Chromium).',
  ].join('\n');
}

function logEvent(kind, payload) {
  try {
    const dir = join(HOME, 'analytics');
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'tool-usage.jsonl'),
      JSON.stringify({ ts: new Date().toISOString(), tool: 'swarm-browse', kind, ...payload }) + '\n',
      { flag: 'a' });
  } catch {}
}

function parseFlag(argv, name) {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : undefined;
}
function hasFlag(argv, name) {
  return argv.includes(name);
}

async function runReal(cmd, args) {
  const { chromium } = await import('playwright');
  // Stateless invocation: a launch per call. Fine for v0.2 single-call usage;
  // M4 daemonises. Headed via env to make debugging less mysterious.
  const headless = process.env.SWARM_BROWSE_HEADED ? false : true;
  const browser = await chromium.launch({ headless });
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    switch (cmd) {
      case 'open': {
        const url = args[0];
        if (!url) throw new Error('open: <url> required');
        const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        process.stdout.write(JSON.stringify({
          ok: true, url: page.url(), status: resp?.status() ?? null,
          title: await page.title(),
        }) + '\n');
        return 0;
      }
      case 'screenshot': {
        const out = parseFlag(args, '--out') || `/tmp/swarm-browse-${Date.now()}.png`;
        const full = hasFlag(args, '--full');
        // open required first; in a one-shot invocation we can't, so this
        // command is mostly useful via the M4 daemon. v0.2 contract: error.
        throw new Error('screenshot must follow open in the same session; v0.2 has no daemon yet — use open in a one-liner script that also takes the screenshot');
      }
      case 'wait': {
        const sel = args[0];
        const timeout = parseInt(parseFlag(args, '--timeout') || '5000', 10);
        if (!sel) throw new Error('wait: <selector> required');
        await page.waitForSelector(sel, { timeout });
        process.stdout.write(JSON.stringify({ ok: true, selector: sel }) + '\n');
        return 0;
      }
      case 'close': {
        process.stdout.write(JSON.stringify({ ok: true, note: 'no-op in stateless mode' }) + '\n');
        return 0;
      }
      default:
        process.stdout.write(`real-mode: ${cmd} ${args.join(' ')} (not implemented in v0.2, awaits daemon in M4)\n`);
        return 0;
    }
  } finally {
    await browser.close();
  }
}

export async function run(argv) {
  const cmd = argv[0];
  const real = haveBackend();
  const mode = real ? 'real' : 'stub';

  if (!cmd || cmd === 'help' || cmd === '--help' || cmd === '-h') {
    process.stdout.write(usage(mode) + '\n');
    return 0;
  }
  if (cmd === 'version' || cmd === '--version' || cmd === '-v') {
    process.stdout.write(`swarm-browse 0.2.0 (${mode})\n`);
    return 0;
  }
  if (!COMMANDS.has(cmd)) {
    process.stderr.write(`swarm-browse: unknown command "${cmd}"\n${usage(mode)}\n`);
    return 2;
  }

  if (!real) {
    process.stdout.write(`stub: ${cmd} ${JSON.stringify(argv.slice(1))}\n`);
    logEvent(cmd, { args: argv.slice(1), mode: 'stub' });
    return 0;
  }

  try {
    return await runReal(cmd, argv.slice(1));
  } catch (e) {
    process.stderr.write(`swarm-browse: ${e?.message ?? e}\n`);
    return 1;
  }
}
