import assert from 'node:assert/strict';
import test from 'node:test';
import { layers, scenarios } from '../src/data.js';

test('every demonstration explains every reasoning layer', () => {
  const expectedLayers = Object.keys(layers).sort();
  for (const scenario of Object.values(scenarios)) {
    assert.deepEqual(Object.keys(scenario.layers).sort(), expectedLayers);
  }
});

test('confidence stays calibrated as a percentage', () => {
  for (const scenario of Object.values(scenarios)) {
    assert.ok(scenario.confidence > 0 && scenario.confidence <= 100);
  }
});

