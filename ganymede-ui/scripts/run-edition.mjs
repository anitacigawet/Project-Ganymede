import { spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';

const [edition = 'full', command = 'dev', ...nextArgs] = process.argv.slice(2);
if (!['full', 'showcase'].includes(edition)) {
  throw new Error('Edition must be full or showcase.');
}
if (!['dev', 'build', 'start'].includes(command)) {
  throw new Error('Command must be dev, build, or start.');
}

const nextBin = path.join(process.cwd(), 'node_modules', 'next', 'dist', 'bin', 'next');
const commandArgs = [nextBin, command, ...nextArgs];
if (command === 'build' && !nextArgs.some((arg) => arg === '--webpack' || arg === '--turbopack')) {
  commandArgs.push('--webpack');
}
const result = spawnSync(process.execPath, commandArgs, {
  cwd: process.cwd(),
  env: { ...process.env, GANYMEDE_EDITION: edition },
  stdio: 'inherit',
});

process.exit(result.status ?? 1);
