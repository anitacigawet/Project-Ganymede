const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

// Execute the checked-in TypeScript without a build or another test dependency.
module.exports = function sourceLoader(overrides = {}) {
  const root = path.resolve(__dirname, '../src');
  const cache = new Map();
  function load(filename) {
    const resolved = path.isAbsolute(filename) ? filename : path.join(root, filename);
    const file = [resolved, `${resolved}.ts`, `${resolved}.tsx`].find(candidate => fs.existsSync(candidate) && fs.statSync(candidate).isFile());
    if (!file) throw new Error(`Source module missing: ${resolved}`);
    if (cache.has(file)) return cache.get(file).exports;
    const module = { exports: {} };
    cache.set(file, module);
    const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
      fileName: file,
    }).outputText;
    const localRequire = name => {
      if (Object.hasOwn(overrides, name)) return overrides[name];
      if (name.startsWith('@/')) return load(path.join(root, name.slice(2)));
      if (name.startsWith('.')) return load(path.resolve(path.dirname(file), name));
      return require(name);
    };
    new Function('require', 'module', 'exports', compiled)(localRequire, module, module.exports);
    return module.exports;
  }
  return load;
};
