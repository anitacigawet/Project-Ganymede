import { open, realpath, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const types = { '.css': 'text/css', '.html': 'text/html', '.ico': 'image/x-icon', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml' };

function contained(root, file) {
  const relative = path.relative(root, file);
  return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

function httpError(status) {
  return Object.assign(new Error(`HTTP ${status}`), { status });
}

async function realFile(root, file) {
  if (!contained(root, file)) throw httpError(403);
  const resolved = await realpath(file);
  if (!contained(root, resolved)) throw httpError(403);
  return resolved;
}

function sendError(res, status) {
  if (res.destroyed) return;
  if (res.headersSent) {
    res.destroy();
    return;
  }
  res.removeHeader('Content-Length');
  res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end(status === 400 ? 'Bad request' : status === 403 ? 'Forbidden' : status === 404 ? 'Not found' : 'Unable to read file');
}

export async function createShowcaseServer(exportRoot = path.resolve(process.cwd(), 'out')) {
  let root;
  try {
    root = await realpath(exportRoot);
  } catch (error) {
    if (error.code === 'ENOENT') throw new Error('Run npm run build:showcase first.');
    throw error;
  }
  if (!(await stat(root)).isDirectory()) throw new Error('Run npm run build:showcase first.');

  return createServer(async (req, res) => {
    let handle;
    try {
      const target = req.url ?? '/';
      // Decode before filesystem normalization so dot segments, separators,
      // Windows drive paths and ADS cannot become aliases. Accept origin-form only.
      if (!target.startsWith('/') || target.startsWith('//')) throw httpError(400);
      let pathname;
      try {
        new URL(target, 'http://127.0.0.1');
        pathname = decodeURIComponent(target.split(/[?#]/, 1)[0]);
      } catch {
        throw httpError(400);
      }
      if (pathname.includes('\0')) throw httpError(400);
      if (/[\\:]/.test(pathname) || pathname.split('/').includes('..')) throw httpError(403);

      let file = path.resolve(root, `.${pathname}`);
      let status = 200;
      try {
        file = await realFile(root, file);
        if ((await stat(file)).isDirectory()) file = await realFile(root, path.join(file, 'index.html'));
      } catch (error) {
        if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
        status = 404;
        file = await realFile(root, path.join(root, '404.html'));
      }

      if (!(await stat(file)).isFile()) throw httpError(404);
      handle = await open(file, 'r');
      if (!(await handle.stat()).isFile()) throw httpError(404);
      res.statusCode = status;
      res.setHeader('Content-Type', types[path.extname(file)] ?? 'application/octet-stream');
      if (req.method === 'HEAD') {
        await handle.close();
        handle = undefined;
        res.end();
        return;
      }
      const stream = handle.createReadStream();
      handle = undefined; // The stream owns and closes the open file.
      stream.on('error', () => sendError(res, 500));
      res.on('close', () => stream.destroy());
      stream.pipe(res);
    } catch (error) {
      if (handle) await handle.close().catch(() => {});
      const status = error.status ?? (['ENOENT', 'ENOTDIR', 'EISDIR'].includes(error.code) ? 404 : ['EACCES', 'EPERM'].includes(error.code) ? 403 : 500);
      sendError(res, status);
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const server = await createShowcaseServer();
  server.listen(3000, '127.0.0.1', () => {
    console.log('Project Ganymede showcase: http://127.0.0.1:3000');
  });
}
