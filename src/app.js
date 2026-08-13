import { layers, scenarios } from './data.js';

const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));
const scenarioButtons = [...document.querySelectorAll('.scenario-option')];
const layerButtons = [...document.querySelectorAll('.layer-node')];
const trailItems = [...document.querySelectorAll('.trail-item')];
const workspace = document.querySelector('.workspace');
const runButton = document.querySelector('#run-button');
const resetButton = document.querySelector('#reset-button');
const phasePill = document.querySelector('#phase-pill');
const layerNote = document.querySelector('#layer-note');

let activeScenario = 'water';
let running = false;

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function renderScenario(key) {
  activeScenario = key;
  const scenario = scenarios[key];
  const index = Object.keys(scenarios).indexOf(key) + 1;

  scenarioButtons.forEach((button) => button.classList.toggle('active', button.dataset.scenario === key));
  setText('#scenario-title', scenario.title);
  setText('#scenario-question', scenario.question);
  setText('#step-count', `0${index} / 03`);
  setText('#core-label', scenario.core);
  setText('#core-subtitle', scenario.subtitle);
  setText('#trail-frame', scenario.frame);
  setText('#trail-hypothesis', scenario.hypothesis);
  setText('#trail-audit', scenario.audit);
  setText('#trail-revision', scenario.revision);
  resetRun();
}

function resetRun() {
  running = false;
  workspace.classList.remove('running');
  runButton.disabled = false;
  runButton.querySelector('span').textContent = 'Run the reasoning loop';
  setText('#run-status', 'Ready');
  document.querySelector('#run-status').insertAdjacentHTML('afterbegin', '<i></i>');
  setText('#run-detail', 'A recorded analysis is ready to explore.');
  phasePill.textContent = 'Waiting';
  phasePill.classList.remove('running');
  trailItems.forEach((item, index) => {
    item.classList.toggle('active', index === 0);
    item.classList.remove('complete');
  });
  layerButtons.forEach((button) => button.classList.remove('active', 'seen'));
  document.querySelectorAll('.connectors line').forEach((line) => line.classList.remove('lit'));
  document.querySelector('#confidence-bar').style.width = '0';
  setText('#confidence-value', '—');
  setText('#confidence-note', 'The demonstration separates confidence from certainty.');
  layerNote.classList.remove('visible');
}

function showLayer(name) {
  const scenario = scenarios[activeScenario];
  const metadata = layers[name];
  layerButtons.forEach((button) => button.classList.toggle('active', button.dataset.layer === name));
  setText('#layer-note-number', metadata.number);
  setText('#layer-note-title', metadata.title);
  setText('#layer-note-copy', scenario.layers[name]);
  layerNote.classList.add('visible');
}

function activateTrail(index) {
  trailItems.forEach((item, itemIndex) => {
    item.classList.toggle('active', itemIndex === index);
    if (itemIndex < index) item.classList.add('complete');
  });
}

async function runReasoningLoop() {
  if (running) return;
  running = true;
  workspace.classList.add('running');
  runButton.disabled = true;
  runButton.querySelector('span').textContent = 'Following the analysis…';
  phasePill.classList.add('running');
  setText('#run-status', 'In progress');
  document.querySelector('#run-status').insertAdjacentHTML('afterbegin', '<i></i>');

  const stageNames = ['Framing', 'Gathering', 'Synthesizing', 'Auditing', 'Revising'];
  const layerOrder = Object.keys(layers);

  for (let stage = 0; stage < stageNames.length; stage += 1) {
    activateTrail(stage);
    phasePill.textContent = stageNames[stage];
    setText('#run-detail', stage === 3 ? 'A separate pass is testing the first answer.' : 'The recorded reasoning trail is unfolding.');

    if (stage === 1) {
      for (let index = 0; index < layerOrder.length; index += 1) {
        const name = layerOrder[index];
        const button = document.querySelector(`[data-layer="${name}"]`);
        const line = document.querySelector(`[data-line="${name}"]`);
        button.classList.add('seen');
        line?.classList.add('lit');
        showLayer(name);
        await wait(175);
      }
      layerButtons.forEach((button) => button.classList.remove('active'));
      layerNote.classList.remove('visible');
    } else {
      await wait(750);
    }
  }

  trailItems.forEach((item) => item.classList.add('complete'));
  trailItems.forEach((item) => item.classList.remove('active'));
  workspace.classList.remove('running');
  phasePill.textContent = 'Complete';
  phasePill.classList.remove('running');
  runButton.disabled = false;
  runButton.querySelector('span').textContent = 'Replay the reasoning loop';
  setText('#run-status', 'Complete');
  document.querySelector('#run-status').insertAdjacentHTML('afterbegin', '<i></i>');
  setText('#run-detail', 'The revised conclusion and its uncertainty are visible.');
  const scenario = scenarios[activeScenario];
  setText('#confidence-value', `${scenario.confidence}%`);
  setText('#confidence-note', scenario.confidenceNote);
  document.querySelector('#confidence-bar').style.width = `${scenario.confidence}%`;
  running = false;
}

function drawConnectors() {
  const svg = document.querySelector('#connectors');
  const map = document.querySelector('#reasoning-map').getBoundingClientRect();
  svg.replaceChildren();
  layerButtons.forEach((button) => {
    const rect = button.getBoundingClientRect();
    const x = ((rect.left + rect.width / 2 - map.left) / map.width) * 760;
    const y = ((rect.top + rect.height / 2 - map.top) / map.height) * 600;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', '380');
    line.setAttribute('y1', '300');
    line.setAttribute('x2', x.toFixed(2));
    line.setAttribute('y2', y.toFixed(2));
    line.dataset.line = button.dataset.layer;
    svg.append(line);
  });
}

scenarioButtons.forEach((button) => button.addEventListener('click', () => renderScenario(button.dataset.scenario)));
layerButtons.forEach((button) => button.addEventListener('click', () => showLayer(button.dataset.layer)));
runButton.addEventListener('click', runReasoningLoop);
resetButton.addEventListener('click', resetRun);
window.addEventListener('resize', drawConnectors);

renderScenario(activeScenario);
window.requestAnimationFrame(drawConnectors);

