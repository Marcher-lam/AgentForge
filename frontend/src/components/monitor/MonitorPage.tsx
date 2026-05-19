import { useState, useEffect, useRef, useMemo, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

interface MonitorEvent {
  id: string;
  timestamp: string;
  type: string;
  severity: string;
  session_id: string | null;
  agent_id: string | null;
  run_id: string | null;
  payload: Record<string, unknown>;
}

interface MonitorStats {
  total_events: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  top_agents: [string, number][];
  top_sessions: [string, number][];
  recent_errors: MonitorEvent[];
  active_websockets: number;
  sessions: number;
  messages: number;
  agents: number;
  running_training: { rl: number; evolution: number; coevolution: number };
}

const TYPE_OPTIONS = [
  'ALL', 'system', 'message', 'typing', 'chunk', 'tool_call', 'llm', 'rag', 'memory', 'rl', 'evolution', 'coevolution', 'persistence', 'error',
] as const;

const SEVERITY_COLORS: Record<string, string> = {
  info: 'text-gray-600',
  warning: 'text-yellow-600',
  error: 'text-red-600',
};

const TYPE_COLORS: Record<string, string> = {
  system: 'bg-gray-100 text-gray-700',
  message: 'bg-blue-100 text-blue-700',
  typing: 'bg-purple-100 text-purple-700',
  chunk: 'bg-indigo-100 text-indigo-700',
  tool_call: 'bg-orange-100 text-orange-700',
  llm: 'bg-cyan-100 text-cyan-700',
  rag: 'bg-green-100 text-green-700',
  memory: 'bg-teal-100 text-teal-700',
  rl: 'bg-pink-100 text-pink-700',
  evolution: 'bg-amber-100 text-amber-700',
  coevolution: 'bg-red-100 text-red-700',
  persistence: 'bg-lime-100 text-lime-700',
  error: 'bg-red-200 text-red-800',
};

export function MonitorPage() {
  const [events, setEvents] = useState<MonitorEvent[]>([]);
  const [stats, setStats] = useState<MonitorStats | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [keyword, setKeyword] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<MonitorEvent | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const prevCountRef = useRef(0);

  const fetchEvents = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '200' });
      if (typeFilter !== 'ALL') params.set('type', typeFilter);
      const res = await fetch(`${API_BASE}/api/monitor/events?${params}`);
      const data = await res.json();
      setEvents(data.events || []);
    } catch { /* ignore */ }
  }, [typeFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/monitor/stats`);
      const data = await res.json();
      setStats(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchEvents();
    fetchStats();
    const interval = setInterval(() => { fetchEvents(); fetchStats(); }, 3000);
    return () => clearInterval(interval);
  }, [fetchEvents, fetchStats]);

  const filtered = useMemo(() => {
    if (!keyword) return events;
    return events.filter(e => JSON.stringify(e).toLowerCase().includes(keyword.toLowerCase()));
  }, [events, keyword]);

  useEffect(() => {
    if (autoScroll && listRef.current && filtered.length > prevCountRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
    prevCountRef.current = filtered.length;
  }, [filtered.length, autoScroll]);

  const formatTime = (ts: string) => new Date(ts).toLocaleTimeString();

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        {/* System overview cards */}
        <div className="grid grid-cols-4 gap-2 p-3 border-b bg-gray-50">
          <div className="bg-white rounded-lg p-2 border">
            <div className="text-xs text-gray-500">Events</div>
            <div className="text-lg font-bold text-gray-800">{stats?.total_events ?? 0}</div>
          </div>
          <div className="bg-white rounded-lg p-2 border">
            <div className="text-xs text-gray-500">WebSocket</div>
            <div className="text-lg font-bold text-green-600">{stats?.active_websockets ?? 0} online</div>
          </div>
          <div className="bg-white rounded-lg p-2 border">
            <div className="text-xs text-gray-500">Training</div>
            <div className="text-sm font-bold text-purple-600">
              RL:{stats?.running_training.rl ?? 0} Evo:{stats?.running_training.evolution ?? 0} CoEvo:{stats?.running_training.coevolution ?? 0}
            </div>
          </div>
          <div className="bg-white rounded-lg p-2 border">
            <div className="text-xs text-gray-500">Agents / Sessions / Msgs</div>
            <div className="text-sm font-bold text-blue-600">
              {stats?.agents ?? 0} / {stats?.sessions ?? 0} / {stats?.messages ?? 0}
            </div>
          </div>
        </div>

        {/* Event type breakdown */}
        {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
          <div className="flex flex-wrap gap-1 px-3 py-1.5 border-b bg-gray-50 text-xs">
            {Object.entries(stats.by_type).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
              <span key={type} className={`px-1.5 py-0.5 rounded ${TYPE_COLORS[type] || 'bg-gray-100 text-gray-600'}`}>
                {type}: {count}
              </span>
            ))}
          </div>
        )}

        {/* Recent errors */}
        {stats?.recent_errors && stats.recent_errors.length > 0 && (
          <div className="px-3 py-1.5 border-b bg-red-50 text-xs text-red-700">
            Errors: {stats.recent_errors.map(e => e.payload?.event || e.type).join(' | ')}
          </div>
        )}

        {/* Filter bar */}
        <div className="flex items-center gap-2 p-2 border-b bg-gray-50">
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索事件..."
            className="flex-1 border rounded px-2 py-1 text-sm"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="border rounded px-2 py-1 text-sm bg-white"
          >
            {TYPE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-2 py-1 rounded text-sm ${autoScroll ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}
          >
            {autoScroll ? 'Auto ON' : 'Auto OFF'}
          </button>
        </div>

        {/* Event list */}
        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {filtered.map((event) => (
            <div
              key={event.id}
              onClick={() => setSelectedEvent(event)}
              className={`flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 cursor-pointer text-xs ${
                event.severity === 'error' ? 'bg-red-50' : ''
              }`}
            >
              <span className="text-gray-400 w-16 flex-shrink-0">{formatTime(event.timestamp)}</span>
              <span className={`px-1.5 py-0.5 rounded font-mono ${TYPE_COLORS[event.type] || 'bg-gray-100 text-gray-600'}`}>
                {event.type}
              </span>
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                event.severity === 'error' ? 'bg-red-500' : event.severity === 'warning' ? 'bg-yellow-500' : 'bg-gray-300'
              }`} />
              <span className="text-gray-600 flex-1 truncate">
                {event.payload?.sender_name && `[${event.payload.sender_name}] `}
                {event.payload?.event || event.payload?.tool_name || event.payload?.action || JSON.stringify(event.payload).slice(0, 80)}
              </span>
              {event.session_id && (
                <span className="text-gray-400 font-mono">{event.session_id.slice(0, 8)}</span>
              )}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center text-gray-400 py-8">暂无监控事件</div>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selectedEvent && (
        <div className="w-80 border-l p-3 bg-white overflow-y-auto">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold text-sm">事件详情</h3>
            <button onClick={() => setSelectedEvent(null)} className="text-gray-400 hover:text-gray-600 text-sm">X</button>
          </div>
          <dl className="space-y-1.5 text-xs">
            <div><dt className="text-gray-500">Type</dt><dd><span className={`px-1.5 py-0.5 rounded ${TYPE_COLORS[selectedEvent.type] || ''}`}>{selectedEvent.type}</span></dd></div>
            <div><dt className="text-gray-500">Severity</dt><dd className={SEVERITY_COLORS[selectedEvent.severity]}>{selectedEvent.severity}</dd></div>
            <div><dt className="text-gray-500">Time</dt><dd className="font-mono">{selectedEvent.timestamp}</dd></div>
            {selectedEvent.agent_id && <div><dt className="text-gray-500">Agent</dt><dd className="font-mono">{selectedEvent.agent_id.slice(0, 12)}</dd></div>}
            {selectedEvent.session_id && <div><dt className="text-gray-500">Session</dt><dd className="font-mono">{selectedEvent.session_id.slice(0, 12)}</dd></div>}
            {selectedEvent.run_id && <div><dt className="text-gray-500">Run</dt><dd className="font-mono">{selectedEvent.run_id.slice(0, 12)}</dd></div>}
            <div>
              <dt className="text-gray-500 mb-1">Payload</dt>
              <dd><pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto max-h-64">{JSON.stringify(selectedEvent.payload, null, 2)}</pre></dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
