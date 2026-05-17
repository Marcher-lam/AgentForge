import { useState, useEffect } from 'react';
import type { LLMProfile, MCPServerSummary } from '../../types/api';

interface SettingsPageProps {
  apiBase: string;
  onAgentsChanged: () => void;
}

type SettingsTab = 'llm' | 'mcp' | 'skill';

export function SettingsPage({ apiBase, onAgentsChanged }: SettingsPageProps) {
  const [subTab, setSubTab] = useState<SettingsTab>('llm');

  const tabs: { key: SettingsTab; label: string }[] = [
    { key: 'llm', label: '模型配置' },
    { key: 'mcp', label: 'MCP 服务' },
    { key: 'skill', label: '技能管理' },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex gap-1 p-4 pb-0">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setSubTab(t.key)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium ${
              subTab === t.key ? 'bg-white text-blue-600 border border-b-white -mb-px' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto bg-white border-t p-6">
        {subTab === 'llm' && <LLMConfig apiBase={apiBase} />}
        {subTab === 'mcp' && <MCPManager apiBase={apiBase} />}
        {subTab === 'skill' && <SkillManager apiBase={apiBase} />}
      </div>
    </div>
  );
}

function LLMConfig({ apiBase }: { apiBase: string }) {
  const [profiles, setProfiles] = useState<LLMProfile[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [newModel, setNewModel] = useState('');
  const [showAdd, setShowAdd] = useState(false);

  // New profile form
  const [newName, setNewName] = useState('');
  const [newProvider, setNewProvider] = useState('openai');
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newApiKey, setNewApiKey] = useState('');

  const load = () => {
    fetch(`${apiBase}/api/llm-profiles`)
      .then(r => r.json())
      .then(data => setProfiles(Array.isArray(data) ? data : []))
      .catch(() => {});
  };

  useEffect(load, [apiBase]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await fetch(`${apiBase}/api/llm-profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newName,
        provider: newProvider,
        base_url: newBaseUrl,
        api_key: newApiKey,
        models: [],
      }),
    });
    setNewName(''); setNewBaseUrl(''); setNewApiKey(''); setShowAdd(false);
    load();
  };

  const handleDelete = async (id: string) => {
    await fetch(`${apiBase}/api/llm-profiles/${id}`, { method: 'DELETE' });
    setExpanded(null);
    load();
  };

  const handleUpdate = async (profile: LLMProfile, updates: Partial<LLMProfile>) => {
    await fetch(`${apiBase}/api/llm-profiles/${profile.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    load();
  };

  const addModel = async (profile: LLMProfile) => {
    if (!newModel.trim()) return;
    const models = [...(profile.models || []), newModel.trim()];
    await handleUpdate(profile, { models });
    setNewModel('');
  };

  const removeModel = async (profile: LLMProfile, idx: number) => {
    const models = (profile.models || []).filter((_, i) => i !== idx);
    await handleUpdate(profile, { models });
  };

  const providerLabel = (p: string) => {
    const map: Record<string, string> = { openai: 'OpenAI 兼容', anthropic: 'Anthropic', ollama: 'Ollama' };
    return map[p] || p;
  };

  const providerColor = (p: string) => {
    const map: Record<string, string> = { openai: 'from-green-400 to-emerald-500', anthropic: 'from-orange-400 to-red-500', ollama: 'from-blue-400 to-indigo-500' };
    return map[p] || 'from-gray-400 to-gray-500';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">模型服务</h3>
          <p className="text-sm text-gray-500">管理 LLM Provider，每个厂商可配置多个模型</p>
        </div>
        <button onClick={() => { setShowAdd(!showAdd); setNewName(''); setNewBaseUrl(''); setNewApiKey(''); }}
          className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          {showAdd ? '取消' : '+ 添加 Provider'}
        </button>
      </div>

      {/* Add new provider form */}
      {showAdd && (
        <div className="border rounded-xl p-4 bg-blue-50 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="名称，如：本地Qwen" className="border rounded-lg px-3 py-2 text-sm" />
            <select value={newProvider} onChange={e => setNewProvider(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
              <option value="openai">OpenAI 兼容</option>
              <option value="anthropic">Anthropic</option>
              <option value="ollama">Ollama</option>
            </select>
            <input value={newBaseUrl} onChange={e => setNewBaseUrl(e.target.value)} placeholder="接口地址 http://..." className="border rounded-lg px-3 py-2 text-sm" />
            <input type="password" value={newApiKey} onChange={e => setNewApiKey(e.target.value)} placeholder="API Key" className="border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button onClick={handleCreate} disabled={!newName.trim()} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">创建</button>
        </div>
      )}

      {/* Profile cards */}
      {profiles.length === 0 && !showAdd && (
        <div className="text-center mt-10">
          <p className="text-gray-400">暂无 Provider，点击「+ 添加 Provider」开始</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {profiles.map(profile => (
          <div key={profile.id} className="bg-white rounded-xl shadow-sm border overflow-hidden">
            {/* Card header — click to expand */}
            <div className="p-4 cursor-pointer hover:bg-gray-50" onClick={() => setExpanded(expanded === profile.id ? null : profile.id)}>
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${providerColor(profile.provider)} flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                  {profile.provider.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-800 truncate">{profile.name}</p>
                  <p className="text-xs text-gray-500">{providerLabel(profile.provider)} · {profile.models?.length || 0} 个模型</p>
                </div>
                <span className="text-gray-400 text-xs">{expanded === profile.id ? '▲' : '▼'}</span>
              </div>
            </div>

            {/* Expanded detail */}
            {expanded === profile.id && (
              <div className="px-4 pb-4 space-y-3 border-t bg-gray-50">
                <div className="grid grid-cols-2 gap-3 pt-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">名称</label>
                    <input defaultValue={profile.name} onBlur={e => handleUpdate(profile, { name: e.target.value })} className="w-full border rounded px-2 py-1.5 text-sm" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">厂商</label>
                    <select value={profile.provider} onChange={e => handleUpdate(profile, { provider: e.target.value })} className="w-full border rounded px-2 py-1.5 text-sm">
                      <option value="openai">OpenAI 兼容</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="ollama">Ollama</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">接口地址</label>
                    <input defaultValue={profile.base_url} onBlur={e => handleUpdate(profile, { base_url: e.target.value })} className="w-full border rounded px-2 py-1.5 text-sm" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">API Key</label>
                    <input type="password" defaultValue={profile.api_key} onBlur={e => handleUpdate(profile, { api_key: e.target.value })} className="w-full border rounded px-2 py-1.5 text-sm" />
                  </div>
                </div>

                {/* Model list */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">模型列表</label>
                  <div className="space-y-1">
                    {(profile.models || []).map((m, i) => (
                      <div key={i} className="flex items-center gap-2 bg-white border rounded px-2 py-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                        <span className="flex-1 text-sm text-gray-700 truncate">{m}</span>
                        <button onClick={() => removeModel(profile, i)} className="text-xs text-red-400 hover:text-red-600">删除</button>
                      </div>
                    ))}
                    <div className="flex gap-2">
                      <input value={newModel} onChange={e => setNewModel(e.target.value)} placeholder="添加模型 ID，如 gpt-4o-mini" className="flex-1 border rounded px-2 py-1.5 text-sm" onKeyDown={e => { if (e.key === 'Enter') addModel(profile); }} />
                      <button onClick={() => addModel(profile)} className="text-xs bg-blue-100 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-200">添加</button>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button onClick={() => handleDelete(profile.id)} className="text-xs text-red-500 hover:text-red-700">删除此 Provider</button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
function MCPManager({ apiBase }: { apiBase: string }) {
  const [servers, setServers] = useState<MCPServerSummary[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [addMode, setAddMode] = useState<'manual' | 'online'>('manual');
  const [form, setForm] = useState({ server_id: '', name: '', description: '', connection_type: 'stdio', command: '', url: '' });
  const [onlinePkg, setOnlinePkg] = useState('');
  const [onlineArgs, setOnlineArgs] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState('');

  const load = () => {
    fetch(`${apiBase}/api/mcp-servers`)
      .then(r => r.json())
      .then(data => setServers(Array.isArray(data) ? data : []))
      .catch(() => {});
  };

  useEffect(load, [apiBase]);

  const handleAdd = async () => {
    if (!form.server_id.trim() || !form.name.trim()) return;
    await fetch(`${apiBase}/api/mcp-servers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    setForm({ server_id: '', name: '', description: '', connection_type: 'stdio', command: '', url: '' });
    setShowAdd(false);
    load();
  };

  const handleOnlineInstall = async () => {
    if (!onlinePkg.trim()) return;
    setInstalling(true);
    setInstallMsg('');
    try {
      const res = await fetch(`${apiBase}/api/mcp-servers/install-online`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: onlinePkg, args: onlineArgs }),
      });
      const data = await res.json();
      if (data.error) {
        setInstallMsg(`错误: ${data.error}`);
      } else {
        const tools = data.tool_names?.length || 0;
        setInstallMsg(`已安装: ${data.server_id}${tools > 0 ? ` (${tools} 个工具)` : ''}`);
        setOnlinePkg('');
        setOnlineArgs('');
        setShowAdd(false);
        load();
      }
    } finally {
      setInstalling(false);
    }
  };

  const handleDelete = async (serverId: string) => {
    await fetch(`${apiBase}/api/mcp-servers/${serverId}`, { method: 'DELETE' });
    load();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">MCP 服务器</h3>
          <p className="text-sm text-gray-500">管理 Model Context Protocol 服务器连接，供智能体调用外部工具</p>
        </div>
        <button onClick={() => { setShowAdd(!showAdd); setInstallMsg(''); }} className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          {showAdd ? '取消' : '+ 添加服务器'}
        </button>
      </div>

      {showAdd && (
        <div className="border rounded-xl p-4 bg-blue-50 space-y-3">
          <div className="flex gap-2 mb-2">
            <button onClick={() => setAddMode('manual')} className={`text-sm px-3 py-1 rounded ${addMode === 'manual' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border'}`}>
              手动配置
            </button>
            <button onClick={() => setAddMode('online')} className={`text-sm px-3 py-1 rounded ${addMode === 'online' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border'}`}>
              从 npm 在线安装
            </button>
          </div>

          {addMode === 'manual' ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <input value={form.server_id} onChange={e => setForm({ ...form, server_id: e.target.value })} placeholder="服务器 ID（唯一标识）" className="border rounded-lg px-3 py-2 text-sm" />
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="显示名称" className="border rounded-lg px-3 py-2 text-sm" />
                <select value={form.connection_type} onChange={e => setForm({ ...form, connection_type: e.target.value })} className="border rounded-lg px-3 py-2 text-sm">
                  <option value="stdio">Stdio（本地命令）</option>
                  <option value="sse">SSE（HTTP 服务）</option>
                </select>
                {form.connection_type === 'stdio' ? (
                  <input value={form.command} onChange={e => setForm({ ...form, command: e.target.value })} placeholder="启动命令，如：npx my-mcp-server" className="border rounded-lg px-3 py-2 text-sm" />
                ) : (
                  <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} placeholder="服务器 URL，如：http://localhost:3000/sse" className="border rounded-lg px-3 py-2 text-sm" />
                )}
              </div>
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="描述（可选）" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <button onClick={handleAdd} disabled={!form.server_id.trim() || !form.name.trim()} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">添加</button>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <input value={onlinePkg} onChange={e => setOnlinePkg(e.target.value)} placeholder="npm 包名，如 @modelcontextprotocol/server-filesystem" className="w-full border rounded-lg px-3 py-2 text-sm" />
                <input value={onlineArgs} onChange={e => setOnlineArgs(e.target.value)} placeholder="启动参数（可选），如 /path/to/dir" className="w-full border rounded-lg px-3 py-2 text-sm" />
                <p className="text-xs text-gray-500">安装后将自动配置为 stdio 模式，使用 npx 运行</p>
              </div>
              <button onClick={handleOnlineInstall} disabled={!onlinePkg.trim() || installing} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">
                {installing ? '安装中...' : '在线安装'}
              </button>
            </>
          )}
          {installMsg && <p className="text-sm text-blue-600">{installMsg}</p>}
        </div>
      )}

      {servers.length === 0 && !showAdd && (
        <div className="text-center mt-10">
          <p className="text-gray-400">暂无 MCP 服务器，点击「+ 添加服务器」开始</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {servers.map(srv => (
          <div key={srv.server_id} className="bg-white rounded-xl shadow-sm border p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-amber-500 flex items-center justify-center text-white font-bold text-xs">
                  {srv.connection_type === 'stdio' ? 'CL' : 'HTTP'}
                </div>
                <div>
                  <p className="font-semibold text-gray-800">{srv.name}</p>
                  <p className="text-xs text-gray-500">{srv.server_id} · {srv.connection_type}</p>
                </div>
              </div>
              <button onClick={() => handleDelete(srv.server_id)} className="text-xs text-red-400 hover:text-red-600">删除</button>
            </div>
            {srv.description && <p className="text-xs text-gray-500">{srv.description}</p>}
            {srv.connection_type === 'stdio' && srv.command && (
              <p className="text-xs text-gray-400 font-mono bg-gray-50 px-2 py-1 rounded">$ {srv.command}</p>
            )}
            {srv.connection_type !== 'stdio' && srv.url && (
              <p className="text-xs text-blue-500 font-mono bg-blue-50 px-2 py-1 rounded">{srv.url}</p>
            )}
            {srv.tool_names && srv.tool_names.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {srv.tool_names.map((t, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full text-xs bg-orange-100 text-orange-700">{t}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

interface SkillItem {
  name: string;
  description: string;
  instructions_length: number;
  source_path: string | null;
}

function SkillManager({ apiBase }: { apiBase: string }) {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [addMode, setAddMode] = useState<'path' | 'text' | 'url'>('url');
  const [skillText, setSkillText] = useState('');
  const [skillPath, setSkillPath] = useState('');
  const [skillUrl, setSkillUrl] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState('');

  const load = () => {
    fetch(`${apiBase}/api/skills`)
      .then(r => r.json())
      .then(data => setSkills(Array.isArray(data) ? data : []))
      .catch(() => {});
  };

  useEffect(load, [apiBase]);

  const handleInstallText = async () => {
    if (!skillText.trim()) return;
    setInstalling(true);
    try {
      const res = await fetch(`${apiBase}/api/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: skillText }),
      });
      const data = await res.json();
      if (data.error) {
        setInstallMsg(`错误: ${data.error}`);
      } else {
        setInstallMsg(`已安装: ${data.name}`);
        setSkillText('');
        setShowAdd(false);
        load();
      }
    } finally { setInstalling(false); }
  };

  const handleInstallPath = async () => {
    if (!skillPath.trim()) return;
    setInstalling(true);
    try {
      const res = await fetch(`${apiBase}/api/skills/install-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: skillPath }),
      });
      const data = await res.json();
      if (data.error) {
        setInstallMsg(`错误: ${data.error}`);
      } else {
        setInstallMsg(`已安装: ${data.name}`);
        setSkillPath('');
        setShowAdd(false);
        load();
      }
    } finally { setInstalling(false); }
  };

  const handleInstallUrl = async () => {
    if (!skillUrl.trim()) return;
    setInstalling(true);
    try {
      const res = await fetch(`${apiBase}/api/skills/install-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: skillUrl }),
      });
      const data = await res.json();
      if (data.error) {
        setInstallMsg(`错误: ${data.error}`);
      } else {
        setInstallMsg(`已安装: ${data.name}`);
        setSkillUrl('');
        setShowAdd(false);
        load();
      }
    } finally { setInstalling(false); }
  };

  const handleDelete = async (name: string) => {
    await fetch(`${apiBase}/api/skills/${name}`, { method: 'DELETE' });
    load();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">技能管理</h3>
          <p className="text-sm text-gray-500">管理 SKILL.md 格式的技能，可从本地路径、文本或在线 URL 安装</p>
        </div>
        <button onClick={() => { setShowAdd(!showAdd); setInstallMsg(''); }} className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          {showAdd ? '取消' : '+ 安装技能'}
        </button>
      </div>

      {showAdd && (
        <div className="border rounded-xl p-4 bg-blue-50 space-y-3">
          <div className="flex gap-2 mb-2">
            <button onClick={() => setAddMode('url')} className={`text-sm px-3 py-1 rounded ${addMode === 'url' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border'}`}>
              从在线安装
            </button>
            <button onClick={() => setAddMode('path')} className={`text-sm px-3 py-1 rounded ${addMode === 'path' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border'}`}>
              从路径安装
            </button>
            <button onClick={() => setAddMode('text')} className={`text-sm px-3 py-1 rounded ${addMode === 'text' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border'}`}>
              从文本安装
            </button>
          </div>
          {addMode === 'url' ? (
            <>
              <input value={skillUrl} onChange={e => setSkillUrl(e.target.value)} placeholder="GitHub 仓库 URL 或 SKILL.md 直链，如 https://github.com/user/skill-repo" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <p className="text-xs text-gray-500">支持 GitHub 仓库地址或 SKILL.md 文件的直接链接</p>
              <button onClick={handleInstallUrl} disabled={!skillUrl.trim() || installing} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">
                {installing ? '下载安装中...' : '在线安装'}
              </button>
            </>
          ) : addMode === 'path' ? (
            <>
              <input value={skillPath} onChange={e => setSkillPath(e.target.value)} placeholder="SKILL.md 文件路径或包含 SKILL.md 的目录路径" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <button onClick={handleInstallPath} disabled={!skillPath.trim() || installing} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">安装</button>
            </>
          ) : (
            <>
              <textarea value={skillText} onChange={e => setSkillText(e.target.value)} placeholder="粘贴 SKILL.md 内容（YAML frontmatter + body）" rows={6} className="w-full border rounded-lg px-3 py-2 text-sm font-mono" />
              <button onClick={handleInstallText} disabled={!skillText.trim() || installing} className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40">安装</button>
            </>
          )}
          {installMsg && <p className="text-sm text-blue-600">{installMsg}</p>}
        </div>
      )}

      {skills.length === 0 && !showAdd && (
        <div className="text-center mt-10">
          <p className="text-gray-400">暂无技能，点击「+ 安装技能」开始</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {skills.map(skill => (
          <div key={skill.name} className="bg-white rounded-xl shadow-sm border p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-white font-bold text-xs">S</div>
                <p className="font-semibold text-gray-800">{skill.name}</p>
              </div>
              <button onClick={() => handleDelete(skill.name)} className="text-xs text-red-400 hover:text-red-600">删除</button>
            </div>
            {skill.description && <p className="text-xs text-gray-500">{skill.description}</p>}
            <div className="flex gap-3 text-xs text-gray-400">
              <span>{skill.instructions_length} 字符</span>
              {skill.source_path && <span className="truncate font-mono">{skill.source_path}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
