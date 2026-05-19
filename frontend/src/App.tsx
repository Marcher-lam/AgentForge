import { useState, useEffect, useCallback, useRef } from 'react';
import 'highlight.js/styles/github-dark.css';
import 'katex/dist/katex.min.css';
import { Provider } from 'jotai';
import { MessagePanel } from './components/chat/MessagePanel';
import { ChatInput } from './components/chat/ChatInput';
import { AgentGrid } from './components/grid/AgentGrid';
import { MonitorPage } from './components/monitor/MonitorPage';
import { DashboardPage } from './components/dashboard/DashboardPage';
import { SettingsPage } from './components/settings/SettingsPage';
import {
  sessionsAtom,
  activeSessionAtom,
  messagesAtom,
  agentsAtom,
  monitorMessagesAtom,
  monitorPausedAtom,
} from './atoms';
import { useAtom } from 'jotai';
import type { FrontendMessage, SessionResponse, AgentSummary } from './types/api';

const API_BASE = 'http://localhost:8000';

type Tab = 'chat' | 'grid' | 'monitor' | 'dashboard' | 'settings';

function AppContent() {
  const [tab, setTab] = useState<Tab>('chat');
  const [wsConnected, setWsConnected] = useState(false);
  const [showNewSession, setShowNewSession] = useState(false);
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([]);
  const [newSessionName, setNewSessionName] = useState('');
  const [sessionType, setSessionType] = useState<'single' | 'group'>('single');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [showMembers, setShowMembers] = useState(false);
  const [typingAgents, setTypingAgents] = useState<Map<string, string>>(new Map());
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const [sessions, setSessions] = useAtom(sessionsAtom);
  const [activeSession, setActiveSession] = useAtom(activeSessionAtom);
  const [messageMap, setMessageMap] = useAtom(messagesAtom);
  const [agents, setAgents] = useAtom(agentsAtom);
  const [monitorMessages] = useAtom(monitorMessagesAtom);
  const [monitorPaused, setMonitorPaused] = useAtom(monitorPausedAtom);
  const messages = activeSession ? messageMap.get(activeSession) || [] : [];

  // Agents in the active session (for @mention filtering)
  const activeSessionData = sessions.find((s) => s.session_id === activeSession);
  const sessionAgents = activeSessionData
    ? agents.filter((a) => activeSessionData.agent_ids.includes(a.agent_id))
    : [];

  // WebSocket connection
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'typing') {
          const { session_id, sender_name } = data.data;
          setTypingAgents((prev) => {
            const next = new Map(prev);
            next.set(sender_name, session_id);
            return next;
          });
        } else if (data.type === 'tool_call') {
          // Tool execution notification — show as system message
          const { session_id, sender_name, tool_name, result } = data.data;
          setTypingAgents((prev) => {
            const next = new Map(prev);
            next.set(`${sender_name}`, session_id);
            return next;
          });
        } else if (data.type === 'chunk') {
          // Streaming chunk: append to existing message or create placeholder
          const { message_id, session_id, sender_name, sender_id, chunk } = data.data;
          setMessageMap((prev) => {
            const next = new Map(prev);
            const existing = next.get(session_id) || [];
            const idx = existing.findIndex((m) => m.message_id === message_id);
            if (idx === -1) {
              // First chunk: create placeholder
              next.set(session_id, [...existing, {
                message_id,
                session_id,
                sender_type: 'AGENT',
                sender_id,
                sender_name,
                content: chunk,
                content_type: 'TEXT',
                created_at: new Date().toISOString(),
              }]);
            } else {
              // Append chunk
              const updated = [...existing];
              updated[idx] = { ...updated[idx], content: updated[idx].content + chunk };
              next.set(session_id, updated);
            }
            return next;
          });
        } else if (data.type === 'message') {
          const msg: FrontendMessage = data.data;
          // Clear typing indicator for this agent
          if (msg.sender_type === 'AGENT' && msg.sender_name) {
            setTypingAgents((prev) => {
              const next = new Map(prev);
              next.delete(msg.sender_name);
              return next;
            });
          }
          setMessageMap((prev) => {
            const next = new Map(prev);
            const existing = next.get(msg.session_id) || [];
            // Replace streaming placeholder if exists, otherwise append
            const streamIdx = existing.findIndex((m) => m.message_id === msg.message_id);
            if (streamIdx !== -1) {
              const updated = [...existing];
              updated[streamIdx] = msg;
              next.set(msg.session_id, updated);
            } else if (!existing.find((m) => m.message_id === msg.message_id)) {
              next.set(msg.session_id, [...existing, msg]);
            }
            return next;
          });
          setSessions((prev) =>
            prev.map((s) =>
              s.session_id === msg.session_id ? { ...s, last_message: msg, updated_at: msg.created_at } : s
            )
          );
        }
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { wsRef.current?.close(); };
  }, []);

  // Poll sessions + agents
  const refreshData = useCallback(async () => {
    try {
      const [sessRes, agentRes] = await Promise.all([
        fetch(`${API_BASE}/api/sessions`),
        fetch(`${API_BASE}/api/agents`),
      ]);
      const sessData: SessionResponse[] = await sessRes.json();
      const agentData: AgentSummary[] = await agentRes.json();
      setSessions(sessData);
      setAgents(agentData);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 5000);
    return () => clearInterval(interval);
  }, [refreshData]);

  // Auto-scroll to bottom on new messages or typing
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingAgents]);

  // Poll messages for active session
  useEffect(() => {
    if (!activeSession) return;
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${activeSession}/messages`);
        const data: FrontendMessage[] = await res.json();
        setMessageMap((prev) => {
          const next = new Map(prev);
          next.set(activeSession, data);
          return next;
        });
      } catch { /* ignore */ }
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [activeSession]);

  const handleSend = useCallback((content: string) => {
    if (!activeSession || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({ type: 'chat', session_id: activeSession, content }));
  }, [activeSession]);

  const handleNewSession = async (agentIds?: string[], name?: string) => {
    try {
      const body: Record<string, unknown> = {};
      if (agentIds && agentIds.length > 0) body.agent_ids = agentIds;
      if (name) body.name = name;
      if (agentIds && agentIds.length > 1) body.type = 'GROUP_BROADCAST';
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const session: SessionResponse = await res.json();
      setSessions((prev) => [...prev, session]);
      setActiveSession(session.session_id);
    } catch { /* ignore */ }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' });
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      setMessageMap((prev) => {
        const next = new Map(prev);
        next.delete(sessionId);
        return next;
      });
      if (activeSession === sessionId) setActiveSession(null);
    } catch { /* ignore */ }
    setDeleteConfirm(null);
  };

  const handleExportSession = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/export`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const sessionName = sessions.find((s) => s.session_id === sessionId)?.name || sessionId.slice(0, 8);
      a.download = `chat-${sessionName}-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  const handleAddMember = async (sessionId: string, agentId: string) => {
    try {
      await fetch(`${API_BASE}/api/sessions/${sessionId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      setSessions((prev) =>
        prev.map((s) =>
          s.session_id === sessionId
            ? { ...s, agent_ids: [...s.agent_ids, agentId], updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch { /* ignore */ }
  };

  const handleRemoveMember = async (sessionId: string, agentId: string) => {
    try {
      await fetch(`${API_BASE}/api/sessions/${sessionId}/members/${agentId}`, {
        method: 'DELETE',
      });
      setSessions((prev) =>
        prev.map((s) =>
          s.session_id === sessionId
            ? { ...s, agent_ids: s.agent_ids.filter((id) => id !== agentId), updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch { /* ignore */ }
  };

  const toggleAgent = (id: string) => {
    setSelectedAgentIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'chat', label: '对话' },
    { key: 'grid', label: '智能体' },
    { key: 'monitor', label: '监控' },
    { key: 'dashboard', label: '仪表盘' },
    { key: 'settings', label: '设置' },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <header className="flex items-center justify-between border-b bg-white px-4 py-2 shadow-sm">
        <h1 className="text-lg font-bold text-gray-800">AgentForge 多智能体平台</h1>
        <nav className="flex gap-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === t.key ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">{wsConnected ? '已连接' : '离线'}</span>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        {tab === 'chat' && (
          <div className="flex h-full">
            <aside className="w-64 border-r bg-white overflow-y-auto flex flex-col">
              <div className="p-3 border-b flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">会话列表</h2>
                <button
                  onClick={() => { setSelectedAgentIds([]); setNewSessionName(''); setSessionType('single'); setShowNewSession(true); }}
                  className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                >
                  + 新建
                </button>
              </div>

              {showNewSession && (
                <div className="p-3 border-b bg-blue-50 space-y-2">
                  <input
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    placeholder="会话名称（可选）"
                    className="w-full border rounded px-2 py-1 text-xs"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setSessionType('single'); setSelectedAgentIds([]); }}
                      className={`flex-1 text-xs py-1 rounded ${sessionType === 'single' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                    >
                      单聊
                    </button>
                    <button
                      onClick={() => { setSessionType('group'); setSelectedAgentIds([]); }}
                      className={`flex-1 text-xs py-1 rounded ${sessionType === 'group' ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                    >
                      群聊
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 font-medium">
                    {sessionType === 'group' ? '选择参与的智能体（多个）:' : '选择一个智能体:'}
                  </p>
                  {agents.map((ag) => (
                    <label key={ag.agent_id} className="flex items-center gap-2 text-xs cursor-pointer hover:bg-blue-100 px-1 py-0.5 rounded">
                      <input
                        type="checkbox"
                        checked={selectedAgentIds.includes(ag.agent_id)}
                        onChange={() => toggleAgent(ag.agent_id)}
                      />
                      <span className={`w-2 h-2 rounded-full ${ag.status === 'ONLINE' ? 'bg-green-500' : 'bg-gray-400'}`} />
                      {ag.name}
                    </label>
                  ))}
                  {agents.length === 0 && (
                    <p className="text-xs text-gray-400">暂无智能体，请先在「智能体」页面创建</p>
                  )}
                  {sessionType === 'group' && selectedAgentIds.length >= 2 && (
                    <p className="text-xs text-purple-600 font-medium">群聊模式：{selectedAgentIds.length} 个智能体将多轮讨论</p>
                  )}
                  {sessionType === 'single' && selectedAgentIds.length > 1 && (
                    <p className="text-xs text-amber-600">单聊模式只取第一个智能体</p>
                  )}
                  <div className="flex gap-1 pt-1">
                    <button
                      onClick={() => {
                        const ids = sessionType === 'single'
                          ? (selectedAgentIds.length > 0 ? [selectedAgentIds[0]] : undefined)
                          : (selectedAgentIds.length > 0 ? selectedAgentIds : undefined);
                        handleNewSession(ids, newSessionName || undefined);
                        setShowNewSession(false);
                      }}
                      disabled={agents.length === 0}
                      className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      创建{sessionType === 'group' ? '群聊' : '会话'}
                    </button>
                    <button
                      onClick={() => setShowNewSession(false)}
                      className="text-xs bg-gray-300 text-gray-700 px-3 py-1 rounded hover:bg-gray-400"
                    >
                      取消
                    </button>
                  </div>
                </div>
              )}

              {sessions.map((s) => (
                <div
                  key={s.session_id}
                  className={`w-full text-left px-4 py-3 text-sm border-b hover:bg-gray-50 relative group ${
                    activeSession === s.session_id ? 'bg-blue-50 border-l-2 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setActiveSession(s.session_id)}
                      className="flex-1 text-left"
                    >
                      <div className="flex items-center gap-1.5">
                        <p className="font-medium truncate">{s.name || s.session_id.slice(0, 8)}</p>
                        {s.agent_ids.length > 1 && (
                          <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded shrink-0">群聊</span>
                        )}
                      </div>
                      {s.last_message && (
                        <p className="text-xs text-gray-500 truncate mt-0.5">{s.last_message.content}</p>
                      )}
                    </button>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleExportSession(s.session_id); }}
                        title="导出聊天记录"
                        className="text-xs text-gray-400 hover:text-blue-600 p-1"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3" /></svg>
                      </button>
                      {deleteConfirm === s.session_id ? (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.session_id); }}
                            className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded"
                          >确认</button>
                          <button
                            onClick={(e) => { e.stopPropagation(); setDeleteConfirm(null); }}
                            className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded"
                          >取消</button>
                        </div>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); setDeleteConfirm(s.session_id); }}
                          title="删除会话"
                          className="text-xs text-gray-400 hover:text-red-600 p-1"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {sessions.length === 0 && (
                <p className="text-xs text-gray-400 p-4">暂无会话——点击「+ 新建」创建</p>
              )}
            </aside>
            <div className="flex-1 flex flex-col relative">
              {activeSession && (
                <div className="flex items-center justify-between px-4 py-2 border-b bg-white">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">
                      {activeSessionData?.name || '对话'}
                    </span>
                    {activeSessionData && activeSessionData.agent_ids.length > 1 && (
                      <button
                        onClick={() => setShowMembers(!showMembers)}
                        className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded hover:bg-purple-200 transition-colors cursor-pointer flex items-center gap-1"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        群聊 · {activeSessionData.agent_ids.length} 人
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleExportSession(activeSession)}
                      className="text-xs text-gray-500 hover:text-blue-600 flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-50"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3" /></svg>
                      导出记录
                    </button>
                  </div>
                </div>
              )}

              {/* Group Members Panel */}
              {showMembers && activeSessionData && activeSessionData.agent_ids.length > 1 && (
                <div className="absolute top-10 right-4 w-72 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">群成员 ({activeSessionData.agent_ids.length})</h3>
                    <button onClick={() => setShowMembers(false)} className="text-gray-400 hover:text-gray-600">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </div>

                  {/* Current members */}
                  <div className="max-h-48 overflow-y-auto">
                    {activeSessionData.agent_ids.map((aid) => {
                      const ag = agents.find((a) => a.agent_id === aid);
                      return (
                        <div key={aid} className="flex items-center justify-between px-4 py-2 hover:bg-gray-50">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-xs font-bold">
                              {(ag?.name || '?').slice(0, 1)}
                            </div>
                            <span className="text-sm text-gray-700">{ag?.name || aid.slice(0, 8)}</span>
                          </div>
                          <button
                            onClick={() => handleRemoveMember(activeSession, aid)}
                            className="text-xs text-gray-400 hover:text-red-500 p-1"
                            title="移出群聊"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>

                  {/* Add members */}
                  {agents.filter((a) => !activeSessionData.agent_ids.includes(a.agent_id)).length > 0 && (
                    <div className="border-t">
                      <div className="px-4 py-2">
                        <p className="text-xs text-gray-500 font-medium mb-1">添加成员</p>
                        {agents
                          .filter((a) => !activeSessionData.agent_ids.includes(a.agent_id))
                          .map((ag) => (
                            <div key={ag.agent_id} className="flex items-center justify-between py-1">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-white text-[10px] font-bold">
                                  {ag.name.slice(0, 1)}
                                </div>
                                <span className="text-xs text-gray-600">{ag.name}</span>
                              </div>
                              <button
                                onClick={() => handleAddMember(activeSession, ag.agent_id)}
                                className="text-xs text-blue-500 hover:text-blue-700 font-medium"
                              >
                                + 邀请
                              </button>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <MessagePanel messages={messages} />
              {/* Typing indicator */}
              {typingAgents.size > 0 && (
                <div className="px-4 py-2 text-sm text-gray-400 flex items-center gap-2">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                  <span>{Array.from(typingAgents.keys()).join(', ')} 正在输入...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
              <ChatInput onSend={handleSend} disabled={!activeSession} agents={sessionAgents.map((a) => ({ agent_id: a.agent_id, name: a.name }))} />
            </div>
          </div>
        )}

        {tab === 'grid' && (
          <div className="h-full">
            <AgentGrid
              agents={agents.map((ag) => ({
                agent_id: ag.agent_id,
                name: ag.name,
                avatar_url: ag.avatar_url,
                status: ag.status,
                system_prompt: ag.system_prompt,
                last_message_preview: ag.last_message_preview,
              }))}
              apiBase={API_BASE}
              onSelect={(id) => {
                const session = sessions.find((s) => s.agent_ids.includes(id));
                if (session) setActiveSession(session.session_id);
                setTab('chat');
              }}
              onAgentsChanged={refreshData}
            />
          </div>
        )}

        {tab === 'monitor' && (
          <MonitorPage />
        )}

        {tab === 'dashboard' && (
          <DashboardPage agents={agents} apiBase={API_BASE} />
        )}

        {tab === 'settings' && (
          <SettingsPage apiBase={API_BASE} onAgentsChanged={refreshData} />
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Provider>
      <AppContent />
    </Provider>
  );
}
