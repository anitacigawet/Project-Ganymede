/** Shared HTTP/WebSocket lifecycle for the two local run panels. */
export interface RunEvent {
  type: string;
  stroke_number: number | null;
  payload: Record<string, unknown>;
  emitted_at: string;
}

type SessionState = { status: string; error_message?: string | null };
type Terminal = { type: 'complete' | 'cancelled' | 'error' | 'disconnected'; message?: string };

export function iterationStrokeLimit(iterative: boolean, includeBridge: boolean): number {
  return iterative ? (includeBridge ? 4 : 3) : 1;
}

export async function runSession<Stroke extends { stroke_number: number }, Event extends RunEvent>(options: {
  backendUrl: string;
  sessionId: string;
  endpoint: 'run-full-loop' | 'iterate' | 'synthesize';
  body: object;
  onSocket: (socket: WebSocket) => void;
  onEvent: (event: Event) => void;
  onStrokes: (strokes: Stroke[]) => void;
}): Promise<{ final_text: string; strokes: Stroke[] }> {
  const { backendUrl, sessionId, endpoint, onEvent, onStrokes } = options;
  const url = `${backendUrl}/api/v2/sessions/${sessionId}`;
  const requestController = new AbortController();
  const socket = new WebSocket(`${url.replace(/^http/, 'ws')}/events/stream`);
  options.onSocket(socket);
  let active = true;
  let terminalValue: Terminal | undefined;
  let resolveTerminal!: (value: Terminal) => void;
  const terminal = new Promise<Terminal>((resolve) => { resolveTerminal = resolve; });
  const finish = (value: Terminal) => {
    if (terminalValue) return;
    terminalValue = value;
    resolveTerminal(value);
  };

  // Small state requests are bounded independently of long provider work.
  async function readJson<T>(requestUrl: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(requestUrl, { cache: 'no-store', ...init, signal: controller.signal });
      if (!response.ok) throw new Error(`Session request failed: HTTP ${response.status} ${await response.text()}`);
      return await response.json() as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // Serialize refreshes so an older response cannot erase newer strokes.
  let refreshQueue: Promise<void> = Promise.resolve();
  const refreshStrokes = () => {
    refreshQueue = refreshQueue.catch(() => {}).then(async () => {
      if (!active) return;
      const data = await readJson<{ strokes: Stroke[] }>(`${url}/strokes`);
      if (active && Array.isArray(data.strokes)) onStrokes(data.strokes);
    });
    return refreshQueue;
  };

  let rejectOpen!: (reason: Error) => void;
  let openTimer: ReturnType<typeof setTimeout>;
  const opened = new Promise<void>((resolve, reject) => {
    rejectOpen = reject;
    openTimer = setTimeout(() => reject(new Error('Session stream open timeout.')), 5000);
    socket.onopen = () => { clearTimeout(openTimer); resolve(); };
  });
  const disconnected = () => {
    const message = 'Session stream disconnected. The backend may still be running.';
    clearTimeout(openTimer);
    finish({ type: 'disconnected', message });
    rejectOpen(new Error(message));
  };
  socket.onerror = disconnected;
  socket.onclose = disconnected;
  // Install all handlers before open: history replay may arrive immediately.
  socket.onmessage = (message) => {
    let event: Event;
    try {
      event = JSON.parse(message.data) as Event;
      if (!event || typeof event.type !== 'string' || !event.payload || typeof event.payload !== 'object') return;
    } catch { return; }
    if (event.type === 'session_complete') finish({ type: 'complete' });
    if (event.type === 'session_cancelled') finish({ type: 'cancelled', message: 'Session cancelled. Completed strokes are retained.' });
    if (event.type === 'error') finish({ type: 'error', message: typeof event.payload.message === 'string' ? event.payload.message : 'Session failed.' });
    onEvent(event);
    if (event.type === 'stroke_completed' || event.type === 'synthesis_complete') {
      void refreshStrokes().catch(() => {}); // Terminal reconciliation retries transient failures.
    }
  };

  let reconciled = false;
  try {
    await opened;
    const drive = terminalValue ? terminal : fetch(`${url}/${endpoint}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options.body), signal: requestController.signal,
    }).then(async (response) => {
      if (!response.ok) throw new Error(`Run failed: HTTP ${response.status} ${await response.text()}`);
      return { type: 'response' as const, data: await response.json() as { strokes?: Stroke[]; stroke?: Stroke } };
    });
    const result = await Promise.race([drive, terminal]);
    if (result.type === 'response') {
      if (endpoint === 'run-full-loop') await terminal;
      else if (result.data.strokes) onStrokes(result.data.strokes);
      else if (result.data.stroke) onStrokes([result.data.stroke]);
    }
    // State is authoritative after cancellation, a dropped stream, or an HTTP
    // response. Read partial strokes even when the state request fails.
    const [stateResult] = await Promise.allSettled([
      readJson<SessionState>(url), refreshStrokes(),
    ]);
    reconciled = true;
    if (stateResult.status === 'rejected') throw stateResult.reason;
    const state = stateResult.value;
    if (state.status === 'cancelled' || terminalValue?.type === 'cancelled') {
      throw new Error('Session cancelled. Completed strokes are retained.');
    }
    if (state.status === 'error' || terminalValue?.type === 'error') {
      throw new Error(state.error_message || terminalValue?.message || 'Session failed.');
    }
    const completed = state.status === 'complete';
    if (!completed && terminalValue?.type === 'disconnected') throw new Error(terminalValue.message);
    if (!completed && (endpoint === 'run-full-loop' || result.type !== 'response' || state.status !== 'running')) {
      throw new Error('Session has not completed. Completed strokes are retained.');
    }
    const final = await readJson<{ final_resolution: { final_text: string; strokes: Stroke[] } }>(`${url}/complete`, { method: 'POST' });
    if (!final.final_resolution || typeof final.final_resolution.final_text !== 'string' || !Array.isArray(final.final_resolution.strokes)) {
      throw new Error('Session returned an invalid final result.');
    }
    onStrokes(final.final_resolution.strokes);
    return final.final_resolution;
  } catch (error) {
    if (!reconciled) await refreshStrokes().catch(() => {});
    throw error;
  } finally {
    active = false;
    clearTimeout(openTimer!);
    requestController.abort();
    socket.onopen = socket.onmessage = socket.onclose = socket.onerror = null;
    socket.close();
  }
}
