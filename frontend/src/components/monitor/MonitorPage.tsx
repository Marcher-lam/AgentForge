import { useState, useEffect, useRef, useMemo } from 'react';
import type { MonitorMessage, TopologyNode, TopologyEdge } from '../../types/api';

interface MonitorPageProps {
  messages: MonitorMessage[];
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  isPaused: boolean;
  onTogglePause: () => void;
  onFilter?: (filter: MonitorFilter) => void;
}

export interface MonitorFilter {
  agentId?: string;
  topic?: string;
  type?: string;
  keyword?: string;
  timeRange?: { start: Date; end: Date };
}

type MessageTypeFilter = 'ALL' | 'TEXT' | 'TOOL_CALL' | 'SYSTEM';

export function MonitorPage({ messages, isPaused, onTogglePause }: MonitorPageProps) {
  const [selectedMsg, setSelectedMsg] = useState<MonitorMessage | null>(null);
  const [filterKeyword, setFilterKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<MessageTypeFilter>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const prevMsgCountRef = useRef(0);

  // Statistics computation
  const stats = useMemo(() => {
    const total = messages.length;
    const perAgent: Record<string, number> = {};
    for (const m of messages) {
      const agent = m.sender_id.slice(0, 8);
      perAgent[agent] = (perAgent[agent] || 0) + 1;
    }
    // Compute messages/sec over last 10 seconds
    const now = Date.now();
    const recentWindow = 10_000; // 10s
    const recent = messages.filter(m => now - new Date(m.timestamp).getTime() < recentWindow);
    const msgsPerSec = recent.length / (recentWindow / 1000);
    return { total, perAgent, msgsPerSec };
  }, [messages]);

  // Time range
  const timeRange = useMemo(() => {
    if (messages.length === 0) return null;
    const timestamps = messages.map(m => new Date(m.timestamp).getTime());
    const earliest = new Date(Math.min(...timestamps));
    const latest = new Date(Math.max(...timestamps));
    return { earliest, latest };
  }, [messages]);

  // Filter logic
  const filtered = useMemo(() => {
    let result = messages;
    if (typeFilter !== 'ALL') {
      result = result.filter(m => m.message_type === typeFilter);
    }
    if (filterKeyword) {
      result = result.filter(
        m => JSON.stringify(m.payload).includes(filterKeyword) || m.topic.includes(filterKeyword)
      );
    }
    return result;
  }, [messages, typeFilter, filterKeyword]);

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && listRef.current && filtered.length > prevMsgCountRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
    prevMsgCountRef.current = filtered.length;
  }, [filtered.length, autoScroll]);

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        {/* Statistics bar */}
        <div className="flex items-center gap-4 p-2 border-b bg-gray-50 text-xs">
          <div className="flex items-center gap-1">
            <span className="text-gray-500">Total:</span>
            <span className="font-semibold text-gray-700">{stats.total}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-500">Rate:</span>
            <span className="font-semibold text-blue-600">{stats.msgsPerSec.toFixed(1)}/s</span>
          </div>
          {timeRange && (
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Range:</span>
              <span className="font-mono text-gray-600">
                {timeRange.earliest.toLocaleTimeString()} - {timeRange.latest.toLocaleTimeString()}
              </span>
            </div>
          )}
          {Object.entries(stats.perAgent).slice(0, 5).map(([agent, count]) => (
            <div key={agent} className="flex items-center gap-1">
              <span className="text-blue-600 font-mono">{agent}</span>
              <span className="text-gray-500">:</span>
              <span className="font-semibold text-gray-700">{count}</span>
            </div>
          ))}
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-2 p-3 border-b bg-gray-50">
          <input
            value={filterKeyword}
            onChange={(e) => setFilterKeyword(e.target.value)}
            placeholder="按关键词或主题筛选..."
            className="flex-1 border rounded-lg px-3 py-1.5 text-sm"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as MessageTypeFilter)}
            className="border rounded-lg px-3 py-1.5 text-sm bg-white"
          >
            <option value="ALL">ALL</option>
            <option value="TEXT">TEXT</option>
            <option value="TOOL_CALL">TOOL_CALL</option>
            <option value="SYSTEM">SYSTEM</option>
          </select>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              autoScroll ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            {autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          </button>
          <button
            onClick={onTogglePause}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              isPaused ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>

        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1">
          {filtered.map((msg) => (
            <div
              key={msg.message_id}
              onClick={() => setSelectedMsg(msg)}
              className="flex items-center gap-2 p-2 rounded hover:bg-gray-100 cursor-pointer text-sm"
            >
              <span className="text-blue-600 font-mono">{msg.sender_id.slice(0, 8)}</span>
              <span className="text-gray-400">→</span>
              <span className="text-purple-600 font-mono">{msg.receiver_id?.slice(0, 8) || '*'}</span>
              <span className="text-gray-500 flex-1 truncate">{msg.topic}</span>
              <span className="text-xs text-gray-400">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </div>
      {selectedMsg && (
        <div className="w-80 border-l p-4 bg-white overflow-y-auto">
          <h3 className="font-semibold mb-2">消息详情</h3>
          <dl className="space-y-2 text-sm">
            <div><dt className="text-gray-500">发送者</dt><dd className="font-mono">{selectedMsg.sender_id}</dd></div>
            <div><dt className="text-gray-500">接收者</dt><dd className="font-mono">{selectedMsg.receiver_id || 'broadcast'}</dd></div>
            <div><dt className="text-gray-500">主题</dt><dd>{selectedMsg.topic}</dd></div>
            <div><dt className="text-gray-500">类型</dt><dd>{selectedMsg.message_type}</dd></div>
            <div><dt className="text-gray-500">时间戳</dt><dd>{new Date(selectedMsg.timestamp).toISOString()}</dd></div>
            <div><dt className="text-gray-500">载荷</dt><dd><pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">{JSON.stringify(selectedMsg.payload, null, 2)}</pre></dd></div>
          </dl>
          <button onClick={() => setSelectedMsg(null)} className="mt-3 text-sm text-gray-500 hover:text-gray-700">关闭</button>
        </div>
      )}
    </div>
  );
}
