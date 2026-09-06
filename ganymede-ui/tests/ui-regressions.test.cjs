const test = require('node:test');
const assert = require('node:assert/strict');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const sourceLoader = require('./load-source.cjs');

const load = sourceLoader();
const { isGSSState } = load('lib/gss.ts');
const { iterationStrokeLimit, runSession } = load('lib/sessionRun.ts');
const { EXAMPLES_BY_PATHWAY } = load('data/examples.ts');
const examples = Object.values(EXAMPLES_BY_PATHWAY).flat();
const valid = examples[0].gss;
const stroke = (number, audit_kind = null) => ({ stroke_number: number, pathway: audit_kind ? 'mirror_audit' : 'cleanroom', raw_response: `Stroke ${number}`, audit_kind, started_at: 'now', completed_at: 'now' });
const event = (type, payload = {}, stroke_number = null) => ({ type, payload, stroke_number, emitted_at: 'now' });

function malformedFixtures() {
  const mutate = fn => { const copy = structuredClone(valid); fn(copy); return copy; };
  return [null, [], 7, {}, { topological_entities: {}, physics_logic: {} },
    mutate(c => { c.metadata = null; }),
    mutate(c => { c.metadata.classification = { crash: true }; }),
    mutate(c => { c.environmental_baseline.unit = 2; }),
    mutate(c => { c.environmental_baseline.recharge_rate = '2'; }),
    mutate(c => { c.legislative_framework.mitigation_coefficient = '0.5'; }),
    mutate(c => { c.legislative_framework.status = 'other'; }),
    mutate(c => { c.topological_entities = {}; }),
    mutate(c => { c.topological_entities[0] = null; }),
    mutate(c => { c.topological_entities[0].coordinates = []; }),
    mutate(c => { c.topological_entities[0].coordinates.x = '0'; }),
    mutate(c => { c.topological_entities[0].type = 'unknown'; }),
    mutate(c => { c.topological_entities[0].node_id = 7; }),
    mutate(c => { c.topological_entities[0].luminosity = Infinity; }),
    mutate(c => { c.physics_logic.failure_threshold = NaN; }),
    JSON.parse(JSON.stringify(valid).replace(/"ambient_depletion":-?[\d.]+/, '"ambient_depletion":1e309')),
  ];
}

test('nested GSS validation rejects malformed JSON shapes and nonfinite values; all presets remain valid', () => {
  assert.ok(examples.length >= 5);
  examples.forEach(example => assert.equal(isGSSState(example.gss), true, example.id));
  malformedFixtures().forEach((value, index) => assert.equal(isGSSState(value), false, `fixture ${index}`));
});

function harness(componentName, overrides = {}) {
  const state = [];
  let cursor = 0;
  const hooks = { ...React,
    useState: initial => { const slot = cursor++; if (!(slot in state)) state[slot] = typeof initial === 'function' ? initial() : initial; return [state[slot], next => { state[slot] = typeof next === 'function' ? next(state[slot]) : next; }]; },
    useRef: initial => { const slot = cursor++; if (!(slot in state)) state[slot] = { current: initial }; return state[slot]; },
    useEffect: () => {}, useMemo: fn => fn(), useCallback: fn => fn,
  };
  const loader = sourceLoader({ react: hooks, ...overrides });
  const Component = loader(`components/${componentName}.tsx`)[componentName];
  return props => { cursor = 0; return Component(props); };
}
function elements(tree) {
  if (Array.isArray(tree)) return tree.flatMap(elements);
  if (!tree || typeof tree !== 'object') return [];
  return [tree, ...elements(tree.props?.children)];
}
function content(tree) {
  if (Array.isArray(tree)) return tree.map(content).join('');
  if (tree == null || typeof tree === 'boolean') return '';
  return typeof tree === 'object' ? content(tree.props?.children) : String(tree);
}
const button = (tree, text) => elements(tree).find(node => node.type === 'button' && content(node).includes(text));

test('actual clipboard Apply rejects invalid nested input and accepts a complete preset', () => {
  const render = harness('DevOverlay');
  const applied = [];
  const alerts = [];
  const priorAlert = global.alert;
  global.alert = message => alerts.push(message);
  try {
    const props = { isOpen: true, onOpenChange() {}, onApplyGSS: config => applied.push(config) };
    for (const value of [{ topological_entities: {}, physics_logic: {} }, valid]) {
      const input = elements(render(props)).find(node => node.type === 'textarea' && !node.props.readOnly);
      input.props.onChange({ target: { value: JSON.stringify(value) } });
      button(render(props), 'Apply To Topology').props.onClick();
    }
    assert.equal(alerts.length, 1);
    assert.deepEqual(applied, [valid]);
  } finally { global.alert = priorAlert; }
});

test('actual Canvas render safely handles invalid props and preserves valid presets', () => {
  const loader = sourceLoader({
    '@react-three/fiber': { Canvas: () => React.createElement('div', null, 'canvas') },
    '@react-three/drei': { OrbitControls: () => null, Stars: () => null },
    './GravityWell': { GravityWell: () => null },
  });
  const { PhysicsCanvas } = loader('components/PhysicsCanvas.tsx');
  for (const value of malformedFixtures().filter(value => value !== null)) {
    const html = renderToStaticMarkup(React.createElement(PhysicsCanvas, { scanTrigger: 0, gssConfig: value }));
    assert.match(html, /Invalid topology data/);
  }
  for (const example of examples) {
    const html = renderToStaticMarkup(React.createElement(PhysicsCanvas, { scanTrigger: 0, gssConfig: example.gss }));
    assert.ok(html.includes(example.gss.metadata.classification));
  }
});

class FakeSocket {
  static CLOSED = 3;
  constructor() { this.readyState = 0; FakeSocket.current = this; queueMicrotask(() => { this.readyState = 1; this.onopen?.(); }); }
  emit(value) { this.onmessage?.({ data: JSON.stringify(value) }); }
  close() { if (this.readyState === 3) return; this.readyState = 3; this.onclose?.(); }
}
const response = data => ({ ok: true, status: 200, json: async () => data, text: async () => JSON.stringify(data) });
const tick = () => new Promise(resolve => setImmediate(resolve));

async function runFixture({ endpoint = 'run-full-loop', signal = 'session_complete', status = 'complete', failComplete = false }) {
  const requests = [];
  const updates = [];
  const events = [];
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  global.WebSocket = FakeSocket;
  global.fetch = async (url, init = {}) => {
    requests.push([url, init.method || 'GET']);
    if (url.endsWith(`/${endpoint}`)) {
      setImmediate(() => {
        if (signal === 'close') FakeSocket.current.close();
        else if (signal === 'socket-error') FakeSocket.current.onerror?.();
        else FakeSocket.current.emit(event(signal, { message: 'Synthetic failure' }));
      });
      if (endpoint !== 'run-full-loop') return new Promise(() => {});
      return response({ status: 'running' });
    }
    if (url.endsWith('/strokes')) return response({ strokes: [stroke(1)] });
    if (url.endsWith('/complete')) {
      if (failComplete) return { ok: false, status: 409, text: async () => 'cannot complete' };
      return response({ final_resolution: { final_text: 'Final synthesis', strokes: [stroke(1)] } });
    }
    return response({ status, error_message: status === 'error' ? 'Synthetic failure' : null });
  };
  try {
    let result, error;
    try { result = await runSession({ backendUrl: 'http://synthetic.invalid', sessionId: 'fixture', endpoint, body: {}, onSocket() {}, onEvent: value => events.push(value), onStrokes: value => updates.push(value) }); }
    catch (caught) { error = caught; }
    return { result, error, requests, updates, events };
  } finally { Object.assign(global, saved); }
}

test('full session settles terminal completion, cancellation, server errors and both socket-loss signals', async () => {
  for (const [signal, status, success] of [
    ['session_complete', 'complete', true], ['session_cancelled', 'cancelled', false],
    ['error', 'error', false], ['close', 'running', false], ['socket-error', 'running', false],
    ['close', 'complete', true], ['socket-error', 'cancelled', false],
  ]) {
    const observed = await runFixture({ signal, status });
    assert.equal(!!observed.result, success, signal);
    assert.equal(!!observed.error, !success, signal);
    assert.equal(observed.requests.some(([url]) => url.endsWith('/complete')), success, signal);
    assert.deepEqual(observed.updates.at(-1), [stroke(1)], signal);
  }
  const rejectedCompletion = await runFixture({ failComplete: true });
  assert.match(rejectedCompletion.error.message, /409/);
});

test('blocking quick run also settles on cancellation or transport loss with partial strokes', async () => {
  for (const signal of ['session_cancelled', 'close', 'socket-error']) {
    const result = await runFixture({ endpoint: 'iterate', signal, status: signal === 'session_cancelled' ? 'cancelled' : 'running' });
    assert.ok(result.error);
    assert.equal(result.requests.some(([url]) => url.endsWith('/complete')), false);
    assert.deepEqual(result.updates.at(-1), [stroke(1)]);
  }
});

test('quick iteration refreshes recorded strokes while its HTTP response is still pending', async () => {
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  global.WebSocket = FakeSocket;
  let releaseDrive;
  let persisted = [];
  let finalizing = false;
  const updates = [];
  global.fetch = async url => {
    if (url.endsWith('/iterate')) return new Promise(resolve => { releaseDrive = () => resolve(response({ strokes: persisted })); });
    if (url.endsWith('/strokes')) return response({ strokes: [...persisted] });
    if (url.endsWith('/complete')) { finalizing = true; return response({ final_resolution: { final_text: 'Revision', strokes: persisted } }); }
    return response({ status: 'running' });
  };
  try {
    const pending = runSession({ backendUrl: 'http://synthetic.invalid', sessionId: 'fixture', endpoint: 'iterate', body: {}, onSocket() {}, onEvent() {}, onStrokes: value => updates.push(value) });
    await tick();
    for (const [number, kind] of [[1, null], [2, 'mirror_auditor'], [3, 'bridge'], [4, null]]) {
      persisted.push(stroke(number, kind));
      FakeSocket.current.emit(event('stroke_completed', {}, number));
      await tick();
      assert.equal(updates.at(-1).length, number);
      assert.equal(finalizing, false);
    }
    releaseDrive();
    assert.equal((await pending).final_text, 'Revision');
  } finally { Object.assign(global, saved); }
});

test('iteration budget preserves revision with Bridge and without Bridge', () => {
  assert.equal(iterationStrokeLimit(true, true), 4);
  assert.equal(iterationStrokeLimit(true, false), 3);
  assert.equal(iterationStrokeLimit(false, true), 1);
});

test('both actual quick-run entry points request the complete Bridge or no-Bridge stroke budget', async () => {
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  global.WebSocket = FakeSocket;
  try {
    for (const componentName of ['DispatcherPanel', 'RunnerPanel']) {
      for (const includeBridge of [true, false]) {
        const render = harness(componentName, { '@/data/demoMode': { ...load('data/demoMode.ts'), GANYMEDE_DEMO_MODE: false } });
        const requests = [];
        global.fetch = async (url, init = {}) => {
          requests.push({ url, body: init.body ? JSON.parse(init.body) : null });
          if (url.endsWith('/dispatch')) return response({ pathway: 'cleanroom', confidence: 1, scenario: { question: 'Synthetic question' }, needs_external_knowledge: false, rationale: 'Fixture', clarifying_questions: [] });
          if (url.endsWith('/sessions')) return response({ session_id: 'fixture' });
          if (url.endsWith('/iterate')) return response({ strokes: [stroke(1)] });
          if (url.endsWith('/strokes')) return response({ strokes: [stroke(1)] });
          if (url.endsWith('/complete')) return response({ final_resolution: { final_text: 'Revision', strokes: [stroke(1)] } });
          return response({ status: 'running' });
        };
        const props = { backendUrl: 'http://synthetic.invalid' };
        let tree = render(props);
        if (componentName === 'DispatcherPanel') {
          elements(tree).find(node => node.type === 'textarea').props.onChange({ target: { value: 'Synthetic question' } });
        } else {
          elements(tree).find(node => node.props?.label === 'Question').props.onChange('Synthetic question');
          elements(tree).find(node => node.props?.value === 'synthesis' && node.props?.title).props.onChange('synthesis');
        }
        tree = render(props);
        const checkboxes = elements(tree).filter(node => node.type === 'input' && node.props.type === 'checkbox');
        checkboxes[0].props.onChange({ target: { checked: true } });
        checkboxes[1].props.onChange({ target: { checked: includeBridge } });
        if (componentName === 'DispatcherPanel') {
          await button(render(props), 'Classify intent').props.onClick();
          await button(render(props), 'Run with this').props.onClick();
        } else {
          await button(render(props), 'Run Synthesis').props.onClick();
        }
        assert.equal(requests.find(request => request.url.endsWith('/sessions')).body.max_strokes, includeBridge ? 4 : 3);
        assert.equal(requests.find(request => request.url.endsWith('/iterate')).body.include_bridge, includeBridge);
      }
    }
  } finally { Object.assign(global, saved); }
});

test('actual Dispatcher always audits supplied Mirror analysis regardless of the research flag', async () => {
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  global.WebSocket = FakeSocket;
  try {
    for (const needsExternalKnowledge of [true, false]) {
      for (const iterative of [true, false]) {
        const render = harness('DispatcherPanel', { '@/data/demoMode': { ...load('data/demoMode.ts'), GANYMEDE_DEMO_MODE: false } });
        const requests = [];
        const audit = { ...stroke(1, 'mirror_auditor'), raw_response: 'Fixture audit output' };
        global.fetch = async (url, init = {}) => {
          requests.push({ url, body: init.body ? JSON.parse(init.body) : null });
          if (url.endsWith('/dispatch')) return response({ pathway: 'mirror_audit', confidence: 1, scenario: { prior_resolution: 'Supplied analysis to audit' }, needs_external_knowledge: needsExternalKnowledge, rationale: 'Fixture', clarifying_questions: [] });
          if (url.endsWith('/sessions')) return response({ session_id: 'fixture' });
          if (url.endsWith('/run-full-loop')) throw new Error('Mirror Audit must not start research');
          if (url.endsWith('/iterate')) return response({ strokes: [audit] });
          if (url.endsWith('/synthesize')) return response({ stroke: audit });
          if (url.endsWith('/strokes')) return response({ strokes: [audit] });
          if (url.endsWith('/complete')) return response({ final_resolution: { final_text: audit.raw_response, strokes: [audit] } });
          return response({ status: 'running' });
        };
        const props = { backendUrl: 'http://synthetic.invalid' };
        let tree = render(props);
        elements(tree).find(node => node.type === 'textarea').props.onChange({ target: { value: 'Audit this supplied analysis' } });
        elements(tree).find(node => node.type === 'input' && node.props.type === 'checkbox').props.onChange({ target: { checked: iterative } });
        await button(render(props), 'Classify intent').props.onClick();
        tree = render(props);
        assert.ok(content(tree).includes('Audit supplied analysis'));
        assert.equal(content(tree).includes('Knowledge harvest path'), false);
        assert.equal(content(tree).includes('Override: skip harvest'), false);
        assert.equal(content(tree).includes('Harvest was flagged'), false);
        await button(tree, 'Run with this').props.onClick();
        assert.equal(requests.some(request => request.url.endsWith('/run-full-loop')), false);
        assert.ok(requests.some(request => request.url.endsWith(iterative ? '/iterate' : '/synthesize')));
        assert.equal(requests.find(request => request.url.endsWith('/sessions')).body.scenario.prior_resolution, 'Supplied analysis to audit');
        assert.ok(content(render(props)).includes(audit.raw_response));
        assert.ok(content(render(props)).includes('Resolution ready'));
      }
    }
  } finally { Object.assign(global, saved); }
});

test('both real panel callbacks clear busy after full-run cancellation or socket loss and expose partial strokes', async () => {
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  global.WebSocket = FakeSocket;
  try {
    for (const componentName of ['DispatcherPanel', 'RunnerPanel']) {
      for (const signal of ['session_cancelled', 'close', 'socket-error']) {
        const render = harness(componentName, { '@/data/demoMode': { ...load('data/demoMode.ts'), GANYMEDE_DEMO_MODE: false } });
        let completed = false;
        global.fetch = async (url, init = {}) => {
          if (url.endsWith('/dispatch')) return response({ pathway: 'cleanroom', confidence: 1, scenario: { question: 'Synthetic question' }, needs_external_knowledge: true, rationale: 'Fixture', clarifying_questions: [] });
          if (url.endsWith('/sessions')) return response({ session_id: 'fixture' });
          if (url.endsWith('/run-full-loop')) {
            setImmediate(() => {
              if (signal === 'close') FakeSocket.current.close();
              else if (signal === 'socket-error') FakeSocket.current.onerror?.();
              else FakeSocket.current.emit(event(signal));
            });
            return response({ status: 'running' });
          }
          if (url.endsWith('/strokes')) return response({ strokes: [stroke(1)] });
          if (url.endsWith('/complete')) { completed = true; throw new Error('Must not finalize interrupted run'); }
          return response({ status: signal === 'session_cancelled' ? 'cancelled' : 'running' });
        };
        const props = { backendUrl: 'http://synthetic.invalid' };
        let tree = render(props);
        if (componentName === 'DispatcherPanel') {
          elements(tree).find(node => node.type === 'textarea').props.onChange({ target: { value: 'Synthetic question' } });
          await button(render(props), 'Classify intent').props.onClick();
          await button(render(props), 'Run with this').props.onClick();
        } else {
          elements(tree).find(node => node.props?.label === 'Question').props.onChange('Synthetic question');
          await button(render(props), 'Run Full Loop').props.onClick();
        }
        tree = render(props);
        assert.equal(completed, false, `${componentName}: ${signal}`);
        if (componentName === 'DispatcherPanel') {
          assert.ok(content(tree).includes('Stroke 1'), `${componentName}: partial strokes`);
          assert.ok(content(tree).includes('Completed strokes (partial)'));
          assert.equal(content(tree).includes('Resolution ready'), false);
        } else {
          assert.ok(elements(tree).some(node => node.props?.stroke?.raw_response === 'Stroke 1'), `${componentName}: partial strokes`);
          assert.equal(button(tree, 'Run Full Loop').props.disabled, false);
        }
      }
    }
  } finally { Object.assign(global, saved); }
});

test('actual mind map distinguishes auditor, bridge and revision from live start events', () => {
  const { OrchestratorMindMap } = load('components/OrchestratorMindMap.tsx');
  for (const [kind, number, label] of [['audit', 2, 'Mirror Auditor reviewing'], ['bridge_audit', 3, 'Connection Bridge reviewing'], ['synthesis', 4, 'Re-synthesising']]) {
    const snapshot = { pathway: 'cleanroom', runMode: 'synthesis', scenarioSummary: 'Synthetic question', blueprint: null, oracles: [], strokes: [stroke(1)], finalText: null, running: true, hasError: false, recentEvents: [event('stroke_started', { kind }, number)] };
    const html = renderToStaticMarkup(React.createElement(OrchestratorMindMap, { snapshot }));
    assert.ok(html.includes(label), label);
  }
});

test('actual showcase classify and run callbacks complete all four stages with zero backend requests', async () => {
  const demo = load('data/demoMode.ts');
  const render = harness('DispatcherPanel', { '@/data/demoMode': { ...demo, GANYMEDE_DEMO_MODE: true, waitForDemoBeat: async () => {} } });
  const saved = { fetch: global.fetch, WebSocket: global.WebSocket };
  let requests = 0;
  global.fetch = () => { requests++; throw new Error('Unexpected showcase fetch'); };
  global.WebSocket = class { constructor() { requests++; throw new Error('Unexpected showcase socket'); } };
  try {
    let tree = render({});
    const classify = elements(tree).find(node => node.type === 'button' && /Classify/.test(content(node)));
    assert.ok(classify);
    await classify.props.onClick();
    tree = render({});
    const run = elements(tree).find(node => node.type === 'button' && /Run/.test(content(node)));
    assert.ok(run);
    await run.props.onClick();
    tree = render({});
    assert.equal(requests, 0);
    assert.ok(content(tree).includes(demo.GANYMEDE_DEMO_STROKES.at(-1).raw_response));
  } finally { Object.assign(global, saved); }
});
