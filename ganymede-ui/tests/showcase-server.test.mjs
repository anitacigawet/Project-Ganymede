import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { Readable } from 'node:stream';
import test from 'node:test';
import { createShowcaseServer } from '../scripts/serve-showcase.mjs';

async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'ganymede-showcase-test-'));
  const root = path.join(directory, 'out');
  const outside = path.join(directory, 'out-private');
  await fs.mkdir(path.join(root, 'route'), { recursive: true });
  await fs.mkdir(path.join(root, 'empty'));
  await fs.mkdir(outside);
  await Promise.all([
    fs.writeFile(path.join(root, 'index.html'), 'PUBLIC'),
    fs.writeFile(path.join(root, '404.html'), 'MISSING'),
    fs.writeFile(path.join(root, 'route', 'index.html'), 'ROUTE'),
    fs.writeFile(path.join(root, 'style.css'), 'body {}'),
    fs.writeFile(path.join(root, 'space ü.txt'), 'UNICODE'),
    fs.writeFile(path.join(outside, 'secret.txt'), 'OUTSIDE_SENTINEL'),
  ]);
  const server = await createShowcaseServer(root);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  assert.equal(server.address().address, '127.0.0.1');
  t.after(async () => {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
    await fs.rm(directory, { recursive: true, force: true });
  });
  const get = (url, method = 'GET') => new Promise((resolve, reject) => {
    const request = http.request({ host: '127.0.0.1', port: server.address().port, path: url, method }, response => {
      let body = '';
      response.on('data', data => { body += data; });
      response.on('end', () => resolve({ status: response.statusCode, body, type: response.headers['content-type'] }));
      response.on('error', reject);
    });
    request.on('error', reject);
    request.setTimeout(3000, () => request.destroy(new Error('request timeout')));
    request.end();
  });
  return { root, outside, get };
}

test('serves exported routes, assets, encoded names and HEAD on loopback', async t => {
  const { get } = await fixture(t);
  for (const [url, expected] of [['/', 'PUBLIC'], ['/route/', 'ROUTE'], ['/route', 'ROUTE'], ['/space%20%C3%BC.txt', 'UNICODE'], ['/index.html?view=1', 'PUBLIC']]) {
    const response = await get(url);
    assert.equal(response.status, 200);
    assert.equal(response.body, expected);
  }
  assert.equal((await get('/style.css')).type, 'text/css');
  assert.equal((await get('/', 'HEAD')).body, '');
});

test('rejects traversal and alternate path representations without exposing siblings', async t => {
  const { get } = await fixture(t);
  const forbidden = [
    '/..%2fout-private/secret.txt', '/%2e%2e/out-private/secret.txt',
    '/..%5cout-private%5csecret.txt', '/..\\out-private\\secret.txt',
    '/route/../../out-private/secret.txt', '/%2f../out-private/secret.txt',
    '/C:/out-private/secret.txt', '/C%3a%5cout-private%5csecret.txt',
    '/index.html:secret', '/%5c%5chost%5cshare',
  ];
  for (const url of forbidden) {
    const response = await get(url);
    assert.equal(response.status, 403, url);
    assert.ok(!response.body.includes('OUTSIDE_SENTINEL'));
  }
  for (const url of ['//host/file', 'http://host/file', 'http://[invalid', '/%ZZ', '/%C0%AF', '/%00']) {
    assert.equal((await get(url)).status, 400, url);
  }
  // Double encoding is a literal filename; it must never be decoded twice.
  assert.equal((await get('/%252e%252e%252fout-private/secret.txt')).status, 404);
  assert.equal((await get('/')).body, 'PUBLIC');
});

test('contains symlinks and directory junctions, including the 404 fallback', async t => {
  const { root, outside, get } = await fixture(t);
  await fs.symlink(outside, path.join(root, 'escape'), process.platform === 'win32' ? 'junction' : 'dir');
  await fs.symlink(path.join(root, 'route'), path.join(root, 'inside'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.equal((await get('/escape/secret.txt')).status, 403);
  assert.equal((await get('/escape/')).status, 403);
  assert.equal((await get('/inside/')).body, 'ROUTE');
  await fs.unlink(path.join(root, '404.html'));
  await fs.symlink(outside, path.join(root, '404.html'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.equal((await get('/missing')).status, 403);
  assert.equal((await get('/')).body, 'PUBLIC');
});

test('missing files, absent 404 and directory replacements return controlled errors', async t => {
  const { root, get } = await fixture(t);
  await assert.rejects(createShowcaseServer(path.join(root, 'does-not-exist')), /build:showcase/);
  await assert.rejects(createShowcaseServer(path.join(root, 'index.html')), /build:showcase/);
  for (const url of ['/missing', '/empty/', '/style.css/child']) {
    const response = await get(url);
    assert.equal(response.status, 404);
    assert.equal(response.body, 'MISSING');
  }
  await fs.unlink(path.join(root, '404.html'));
  assert.equal((await get('/missing')).status, 404);
  await fs.mkdir(path.join(root, '404.html'));
  assert.equal((await get('/missing')).status, 404);
  await fs.mkdir(path.join(root, 'empty', 'index.html'));
  assert.equal((await get('/empty/')).status, 404);
  assert.equal((await get('/')).body, 'PUBLIC');
});

test('read-stream errors before and after headers do not terminate the HTTP helper', async t => {
  const { root, get } = await fixture(t);
  const handle = await fs.open(path.join(root, 'index.html'));
  const prototype = Object.getPrototypeOf(handle);
  const original = prototype.createReadStream;
  await handle.close();
  try {
    prototype.createReadStream = function () {
      const file = this;
      return new Readable({
        read() { this.destroy(new Error('synthetic read failure')); },
        destroy(error, callback) { file.close().then(() => callback(error), callback); },
      });
    };
    assert.equal((await get('/')).status, 500);
    prototype.createReadStream = function () {
      const file = this;
      let started = false;
      return new Readable({
        read() {
          if (started) return;
          started = true;
          this.push('partial');
          setTimeout(() => this.destroy(new Error('synthetic later read failure')), 10);
        },
        destroy(error, callback) { file.close().then(() => callback(error), callback); },
      });
    };
    await assert.rejects(get('/'), /aborted|reset|hang up/i);
  } finally {
    prototype.createReadStream = original;
  }
  assert.equal((await get('/')).body, 'PUBLIC');
});
