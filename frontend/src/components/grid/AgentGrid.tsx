import { useState, useCallback, useEffect } from 'react';
import type { AgentConfig, MCPServerSummary, LLMProfile, EvolutionConfig, RLConfig } from '../../types/api';

interface AgentCardData {
  agent_id: string;
  name: string;
  avatar_url: string | null;
  status: string;
  system_prompt?: string;
  last_message_preview?: string;
}

interface AgentDetail {
  agent_id: string;
  name: string;
  status: string;
  system_prompt: string;
  config: AgentConfig | null;
  tools: { name: string; description: string }[];
  skills: string[];
}

interface AgentGridProps {
  agents: AgentCardData[];
  apiBase: string;
  onSelect?: (agentId: string) => void;
  onAgentsChanged?: () => void;
}

export function AgentGrid({ agents, apiBase, onSelect, onAgentsChanged }: AgentGridProps) {
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPrompt, setNewPrompt] = useState('你是一个有帮助的AI助手。');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Create-time config state
  const [createProfileId, setCreateProfileId] = useState<string>('');
  const [createModel, setCreateModel] = useState<string>('');
  const [createEvoEnabled, setCreateEvoEnabled] = useState(false);
  const [createEvo, setCreateEvo] = useState<EvolutionConfig>({ mode: 'agent', population_size: 50, max_generations: 50, mutation_rate: 0.1, elite_size: 2, genome_dim: 10, seed: 42 });
  const [createRlEnabled, setCreateRlEnabled] = useState(false);
  const [createRl, setCreateRl] = useState<RLConfig>({ algorithm: 'PPO', total_steps: 200, learning_rate: 0.001, seed: 42 });
  const [createSkillIds, setCreateSkillIds] = useState<string[]>([]);
  const [createMcpIds, setCreateMcpIds] = useState<string[]>([]);

  // Detail modal state
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [mcpServers, setMcpServers] = useState<MCPServerSummary[]>([]);
  const [llmProfiles, setLlmProfiles] = useState<LLMProfile[]>([]);

  // Edit state
  const [editing, setEditing] = useState(false);
  const [editPrompt, setEditPrompt] = useState('');
  const [editName, setEditName] = useState('');

  // Config edit state
  const [editProfileId, setEditProfileId] = useState<string>('');
  const [editModel, setEditModel] = useState<string>('');
  const [editEvoEnabled, setEditEvoEnabled] = useState(false);
  const [editEvo, setEditEvo] = useState<EvolutionConfig>({ mode: 'agent', population_size: 50, max_generations: 50, mutation_rate: 0.1, elite_size: 2, genome_dim: 10, seed: 42 });
  const [editRlEnabled, setEditRlEnabled] = useState(false);
  const [editRl, setEditRl] = useState<RLConfig>({ algorithm: 'PPO', total_steps: 200, learning_rate: 0.001, seed: 42 });
  const [allSkills, setAllSkills] = useState<{ name: string; description: string }[]>([]);
  const [editSkillIds, setEditSkillIds] = useState<string[]>([]);
  const [editMcpIds, setEditMcpIds] = useState<string[]>([]);
  const [knowledgeUploading, setKnowledgeUploading] = useState(false);
  const [knowledgeMessage, setKnowledgeMessage] = useState('');

  // Load MCP servers + LLM profiles
  useEffect(() => {
    fetch(`${apiBase}/api/mcp-servers`)
      .then(r => r.json())
      .then(data => setMcpServers(Array.isArray(data) ? data : []))
      .catch(() => {});
    fetch(`${apiBase}/api/llm-profiles`)
      .then(r => r.json())
      .then(data => setLlmProfiles(Array.isArray(data) ? data : []))
      .catch(() => {});
    fetch(`${apiBase}/api/skills`)
      .then(r => r.json())
      .then(data => setAllSkills(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, [apiBase]);

  const openDetail = async (agentId: string) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/agents/${agentId}`);
      const data = await res.json();
      setDetail({
        agent_id: data.agent_id,
        name: data.name,
        status: data.status,
        system_prompt: data.system_prompt || '',
        config: data.config || null,
        tools: data.tools || [],
        skills: data.skills || [],
      });
      setEditName(data.name || '');
      setEditPrompt(data.system_prompt || '');
      setEditing(false);
      // Load config into edit state
      const cfg = data.config || {};
      setEditProfileId(cfg.llm?.provider_profile || '');
      setEditModel(cfg.llm?.model || '');
      setEditEvoEnabled(!!cfg.evolution);
      if (cfg.evolution) setEditEvo(cfg.evolution);
      setEditRlEnabled(!!cfg.rl);
      if (cfg.rl) setEditRl(cfg.rl);
      setEditSkillIds(cfg.skill_ids || []);
      setEditMcpIds(cfg.mcp_server_ids || []);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setDetail(null);
    setEditing(false);
  };

  const saveEdit = async () => {
    if (!detail) return;
    const config: Record<string, unknown> = {};
    if (editProfileId || editModel) {
      config.llm = { provider_profile: editProfileId || null, model: editModel || null };
    }
    if (editEvoEnabled) {
      config.evolution = editEvo;
    }
    if (editRlEnabled) {
      config.rl = editRl;
    }
    config.skill_ids = editSkillIds;
    config.mcp_server_ids = editMcpIds;
    await fetch(`${apiBase}/api/agents/${detail.agent_id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: editName, system_prompt: editPrompt, config }),
    });
    // Reload detail
    const res = await fetch(`${apiBase}/api/agents/${detail.agent_id}`);
    const data = await res.json();
    const cfg = data.config || {};
    setDetail({
      agent_id: data.agent_id, name: data.name, status: data.status,
      system_prompt: data.system_prompt || '', config: cfg,
      tools: data.tools || [], skills: data.skills || [],
    });
    setEditName(data.name || '');
    setEditPrompt(data.system_prompt || '');
    setEditProfileId(cfg.llm?.provider_profile || '');
    setEditModel(cfg.llm?.model || '');
    setEditEvoEnabled(!!cfg.evolution);
    if (cfg.evolution) setEditEvo(cfg.evolution);
    setEditRlEnabled(!!cfg.rl);
    if (cfg.rl) setEditRl(cfg.rl);
    setEditSkillIds(cfg.skill_ids || []);
    setEditMcpIds(cfg.mcp_server_ids || []);
    setEditing(false);
    onAgentsChanged?.();
  };

  const handleKnowledgeJsonUpload = async (file: File) => {
    if (!detail) return;
    setKnowledgeUploading(true);
    setKnowledgeMessage('');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${apiBase}/api/agents/${detail.agent_id}/knowledge/upload-json`, {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      if (data.error) {
        setKnowledgeMessage(`上传失败：${data.error}`);
      } else {
        setKnowledgeMessage(`上传成功：新增 ${data.added} 条，当前共 ${data.total} 条`);
      }
    } catch (e) {
      setKnowledgeMessage('上传失败：网络或文件错误');
    } finally {
      setKnowledgeUploading(false);
    }
  };
  const handleCreate = async () => {
    if (!newName.trim()) return;
    const config: Record<string, unknown> = {};
    if (createProfileId || createModel) {
      config.llm = { provider_profile: createProfileId || null, model: createModel || null };
    }
    if (createEvoEnabled) config.evolution = createEvo;
    if (createRlEnabled) config.rl = createRl;
    config.skill_ids = createSkillIds;
    config.mcp_server_ids = createMcpIds;
    config.tool_ids = [];
    await fetch(`${apiBase}/api/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName, system_prompt: newPrompt, config }),
    });
    setNewName('');
    setNewPrompt('你是一个有帮助的AI助手。');
    setCreateProfileId(''); setCreateModel('');
    setCreateEvoEnabled(false); setCreateRlEnabled(false);
    setCreateSkillIds([]); setCreateMcpIds([]);
    setShowCreate(false);
    onAgentsChanged?.();
  };

  const handleDelete = async (id: string) => {
    await fetch(`${apiBase}/api/agents/${id}`, { method: 'DELETE' });
    setDeleteConfirm(null);
    if (detail?.agent_id === id) closeDetail();
    onAgentsChanged?.();
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 pb-2">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">智能体</h2>
          <p className="text-xs text-gray-500">{agents.length} 个智能体在线</p>
        </div>
        <button
          onClick={() => { setShowCreate(!showCreate); setNewName(''); setNewPrompt('你是一个有帮助的AI助手。'); }}
          className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showCreate ? '取消' : '+ 创建智能体'}
        </button>
      </div>

      {/* Create panel */}
      {showCreate && (
        <div className="mx-4 mb-3 border rounded-xl p-4 bg-blue-50 space-y-3 max-h-[70vh] overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-700">创建智能体</h3>
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="智能体名称，例如：程序员、翻译员、分析师"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-300 focus:outline-none"
          />
          <textarea
            value={newPrompt}
            onChange={(e) => setNewPrompt(e.target.value)}
            placeholder="系统提示词，定义智能体的角色和行为..."
            rows={2}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-300 focus:outline-none"
          />

          {/* LLM Selection */}
          <div className="border-t pt-3">
            <h4 className="text-xs font-semibold text-gray-600 mb-2">LLM 配置</h4>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Provider</label>
                <select value={createProfileId} onChange={e => { setCreateProfileId(e.target.value); setCreateModel(''); }} className="w-full border rounded px-2 py-1.5 text-sm bg-white">
                  <option value="">使用全局配置</option>
                  {llmProfiles.map(p => <option key={p.id} value={p.id}>{p.name} ({p.provider})</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">模型</label>
                {createProfileId ? (
                  <select value={createModel} onChange={e => setCreateModel(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm bg-white">
                    <option value="">选择模型</option>
                    {(llmProfiles.find(p => p.id === createProfileId)?.models || []).map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                ) : (
                  <input value={createModel} onChange={e => setCreateModel(e.target.value)} placeholder="模型 ID（可选）" className="w-full border rounded px-2 py-1.5 text-sm" />
                )}
              </div>
            </div>
          </div>

          {/* Skills */}
          {allSkills.length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-xs font-semibold text-gray-600 mb-2">技能</h4>
              <div className="space-y-1">
                {allSkills.map(skill => (
                  <label key={skill.name} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-blue-100 cursor-pointer">
                    <input type="checkbox" checked={createSkillIds.includes(skill.name)} onChange={e => {
                      if (e.target.checked) setCreateSkillIds([...createSkillIds, skill.name]);
                      else setCreateSkillIds(createSkillIds.filter(id => id !== skill.name));
                    }} className="rounded border-gray-300 text-green-600" />
                    <span className="text-xs text-gray-700">{skill.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* MCP Servers */}
          {mcpServers.length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-xs font-semibold text-gray-600 mb-2">MCP 服务器</h4>
              <div className="space-y-1">
                {mcpServers.map(srv => (
                  <label key={srv.server_id} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-blue-100 cursor-pointer">
                    <input type="checkbox" checked={createMcpIds.includes(srv.server_id)} onChange={e => {
                      if (e.target.checked) setCreateMcpIds([...createMcpIds, srv.server_id]);
                      else setCreateMcpIds(createMcpIds.filter(id => id !== srv.server_id));
                    }} className="rounded border-gray-300 text-orange-600" />
                    <span className="text-xs text-gray-700">{srv.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Evolution toggle */}
          <div className="border-t pt-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-gray-600">进化引擎</h4>
              <button onClick={() => setCreateEvoEnabled(!createEvoEnabled)} className={`relative w-10 h-5 rounded-full transition-colors ${createEvoEnabled ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${createEvoEnabled ? 'translate-x-5' : ''}`} />
              </button>
            </div>
            {createEvoEnabled && (
              <div className="grid grid-cols-3 gap-2 bg-indigo-50 rounded-lg p-2">
                <div><label className="block text-xs text-gray-500 mb-1">模式</label><select value={createEvo.mode} onChange={e => setCreateEvo({ ...createEvo, mode: e.target.value })} className="w-full border rounded px-1 py-1 text-xs"><option value="agent">人格优化</option><option value="sphere">球面基准</option></select></div>
                <div><label className="block text-xs text-gray-500 mb-1">种群</label><input type="number" value={createEvo.population_size} onChange={e => setCreateEvo({ ...createEvo, population_size: +e.target.value || 50 })} className="w-full border rounded px-1 py-1 text-xs" /></div>
                <div><label className="block text-xs text-gray-500 mb-1">代数</label><input type="number" value={createEvo.max_generations} onChange={e => setCreateEvo({ ...createEvo, max_generations: +e.target.value || 50 })} className="w-full border rounded px-1 py-1 text-xs" /></div>
              </div>
            )}
          </div>

          {/* RL toggle */}
          <div className="border-t pt-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-gray-600">RL 训练</h4>
              <button onClick={() => setCreateRlEnabled(!createRlEnabled)} className={`relative w-10 h-5 rounded-full transition-colors ${createRlEnabled ? 'bg-purple-600' : 'bg-gray-300'}`}>
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${createRlEnabled ? 'translate-x-5' : ''}`} />
              </button>
            </div>
            {createRlEnabled && (
              <div className="grid grid-cols-3 gap-2 bg-rose-50 rounded-lg p-2">
                <div><label className="block text-xs text-gray-500 mb-1">算法</label><select value={createRl.algorithm} onChange={e => setCreateRl({ ...createRl, algorithm: e.target.value })} className="w-full border rounded px-1 py-1 text-xs"><option value="PPO">PPO</option><option value="DQN">DQN</option><option value="REINFORCE">REINFORCE</option></select></div>
                <div><label className="block text-xs text-gray-500 mb-1">步数</label><input type="number" value={createRl.total_steps} onChange={e => setCreateRl({ ...createRl, total_steps: +e.target.value || 200 })} className="w-full border rounded px-1 py-1 text-xs" /></div>
                <div><label className="block text-xs text-gray-500 mb-1">学习率</label><input type="number" step="0.0001" value={createRl.learning_rate} onChange={e => setCreateRl({ ...createRl, learning_rate: +e.target.value || 0.001 })} className="w-full border rounded px-1 py-1 text-xs" /></div>
              </div>
            )}
          </div>

          <div className="flex gap-2 pt-1">
            <button onClick={handleCreate} disabled={!newName.trim()} className="text-sm bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed">创建智能体</button>
            <button onClick={() => setShowCreate(false)} className="text-sm bg-gray-200 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-300">取消</button>
          </div>
        </div>
      )}

      {/* Card grid */}
      <div className="flex-1 overflow-y-auto p-4 pt-2">
        {agents.length === 0 && !showCreate && (
          <div className="text-center mt-20">
            <p className="text-gray-400 text-lg">暂无智能体</p>
            <p className="text-gray-400 text-sm mt-2">点击「+ 创建智能体」开始</p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className="bg-white rounded-xl shadow-sm border hover:shadow-md transition-all group relative"
            >
              <div className="absolute top-3 right-3 flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${
                  agent.status === 'ONLINE' ? 'bg-green-500 shadow-sm shadow-green-200' : 'bg-gray-400'
                }`} />
                <span className="text-xs text-gray-500">{agent.status === 'ONLINE' ? '在线' : '离线'}</span>
              </div>

              <div
                className="p-5 cursor-pointer"
                onClick={() => openDetail(agent.agent_id)}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold text-lg shrink-0">
                    {agent.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-800 truncate">{agent.name}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {agent.system_prompt ? agent.system_prompt.slice(0, 40) + (agent.system_prompt.length > 40 ? '...' : '') : 'AI 助手'}
                    </p>
                  </div>
                </div>

                {agent.system_prompt && (
                  <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                    {agent.system_prompt}
                  </p>
                )}

                {agent.last_message_preview && (
                  <p className="text-xs text-gray-400 mt-2 truncate">
                    最近：{agent.last_message_preview}
                  </p>
                )}
              </div>

              <div className="px-5 pb-3 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                {deleteConfirm === agent.agent_id ? (
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(agent.agent_id); }}
                      className="text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                    >
                      确认删除
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteConfirm(null); }}
                      className="text-xs bg-gray-200 text-gray-600 px-3 py-1 rounded hover:bg-gray-300"
                    >
                      取消
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={(e) => { e.stopPropagation(); setDeleteConfirm(agent.agent_id); }}
                    className="text-xs text-red-400 hover:text-red-600 transition-colors"
                  >
                    删除
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Detail Modal ── */}
      {detail && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={closeDetail}>
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between p-5 border-b bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold">
                  {detail.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  {editing ? (
                    <input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="text-lg font-semibold border-b-2 border-blue-400 bg-transparent focus:outline-none"
                    />
                  ) : (
                    <h3 className="text-lg font-semibold text-gray-800">{detail.name}</h3>
                  )}
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${detail.status === 'ONLINE' ? 'bg-green-500' : 'bg-gray-400'}`} />
                    {detail.status === 'ONLINE' ? '在线' : '离线'}
                  </span>
                </div>
              </div>
              <button onClick={closeDetail} className="text-gray-400 hover:text-gray-600 text-xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-200">
                &times;
              </button>
            </div>

            {/* Modal body */}
            <div className="overflow-y-auto p-5 space-y-5" style={{ maxHeight: 'calc(85vh - 140px)' }}>

              {/* System Prompt */}
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-gray-700">系统提示词</h4>
                  {!editing && (
                    <button onClick={() => { setEditing(true); setEditPrompt(detail.system_prompt); setEditName(detail.name); }} className="text-xs text-blue-600 hover:text-blue-800">
                      编辑
                    </button>
                  )}
                </div>
                {editing ? (
                  <>
                    <textarea
                      value={editPrompt}
                      onChange={(e) => setEditPrompt(e.target.value)}
                      rows={4}
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-300 focus:outline-none"
                    />
                    <div className="flex gap-2 mt-2">
                      <button onClick={saveEdit} className="text-xs bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700">保存</button>
                      <button onClick={() => setEditing(false)} className="text-xs bg-gray-200 text-gray-600 px-4 py-1.5 rounded hover:bg-gray-300">取消</button>
                    </div>
                  </>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
                    {detail.system_prompt || '未设置'}
                  </div>
                )}
              </section>

              {/* Knowledge JSON Upload */}
              <section className="border rounded-xl p-3 bg-purple-50">
                <h4 className="text-sm font-semibold text-gray-700 mb-1">专属知识库（Milvus）</h4>
                <p className="text-xs text-gray-500 mb-3">
                  上传预处理后的 JSON 文件。格式：{"{\"documents\":[{\"text\":\"知识内容\",\"metadata\":{\"source\":\"doc\"}}]}"}
                </p>
                <label className="inline-flex items-center gap-2 text-xs bg-purple-600 text-white px-3 py-1.5 rounded hover:bg-purple-700 cursor-pointer disabled:opacity-50">
                  <input
                    type="file"
                    accept="application/json,.json"
                    className="hidden"
                    disabled={knowledgeUploading}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleKnowledgeJsonUpload(file);
                      e.currentTarget.value = '';
                    }}
                  />
                  {knowledgeUploading ? '上传中...' : '上传 JSON 知识文件'}
                </label>
                {knowledgeMessage && (
                  <p className={`text-xs mt-2 ${knowledgeMessage.startsWith('上传成功') ? 'text-green-600' : 'text-red-600'}`}>
                    {knowledgeMessage}
                  </p>
                )}
              </section>

              {/* Config: Tools */}
              <section>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">工具配置</h4>
                <div className="flex flex-wrap gap-2">
                  {detail.tools.length > 0 ? detail.tools.map((t, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      {t.name}
                    </span>
                  )) : (
                    <span className="text-xs text-gray-400">未配置工具</span>
                  )}
                </div>
              </section>

              {/* Config: Skills */}
              <section>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">技能配置</h4>
                {allSkills.length > 0 ? (
                  <div className="space-y-1">
                    {allSkills.map(skill => (
                      <label key={skill.name} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editSkillIds.includes(skill.name)}
                          onChange={e => {
                            if (e.target.checked) setEditSkillIds([...editSkillIds, skill.name]);
                            else setEditSkillIds(editSkillIds.filter(id => id !== skill.name));
                          }}
                          className="rounded border-gray-300 text-green-600"
                        />
                        <span className="text-sm text-gray-700">{skill.name}</span>
                        {skill.description && <span className="text-xs text-gray-400 truncate">— {skill.description.slice(0, 50)}</span>}
                      </label>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-gray-400">前往「设置 → 技能管理」安装技能</span>
                )}
              </section>

              {/* Config: MCP Servers */}
              <section>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">MCP 服务器</h4>
                {mcpServers.length > 0 ? (
                  <div className="space-y-1">
                    {mcpServers.map(srv => (
                      <label key={srv.server_id} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editMcpIds.includes(srv.server_id)}
                          onChange={e => {
                            if (e.target.checked) setEditMcpIds([...editMcpIds, srv.server_id]);
                            else setEditMcpIds(editMcpIds.filter(id => id !== srv.server_id));
                          }}
                          className="rounded border-gray-300 text-orange-600"
                        />
                        <span className="text-sm text-gray-700">{srv.name}</span>
                        <span className="text-xs text-gray-400">{srv.connection_type} · {srv.tool_names?.length || 0} 个工具</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-gray-400">前往「设置 → MCP 服务」添加 MCP 服务器</span>
                )}
              </section>

              {/* Config: LLM Selection */}
              <section>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">LLM 配置</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Provider</label>
                    <select
                      value={editProfileId}
                      onChange={e => { setEditProfileId(e.target.value); setEditModel(''); }}
                      className="w-full border rounded-lg px-2 py-1.5 text-sm"
                    >
                      <option value="">使用全局配置</option>
                      {llmProfiles.map(p => (
                        <option key={p.id} value={p.id}>{p.name} ({p.provider})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">模型</label>
                    {editProfileId ? (
                      <select value={editModel} onChange={e => setEditModel(e.target.value)} className="w-full border rounded-lg px-2 py-1.5 text-sm">
                        <option value="">选择模型</option>
                        {(llmProfiles.find(p => p.id === editProfileId)?.models || []).map(m => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    ) : (
                      <input value={editModel} onChange={e => setEditModel(e.target.value)} placeholder="模型 ID（覆盖全局）" className="w-full border rounded-lg px-2 py-1.5 text-sm" />
                    )}
                  </div>
                </div>
              </section>

              {/* Config: Evolution */}
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-gray-700">进化引擎</h4>
                  <button
                    onClick={() => setEditEvoEnabled(!editEvoEnabled)}
                    className={`relative w-10 h-5 rounded-full transition-colors ${editEvoEnabled ? 'bg-blue-600' : 'bg-gray-300'}`}
                  >
                    <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${editEvoEnabled ? 'translate-x-5' : ''}`} />
                  </button>
                </div>
                {editEvoEnabled && (
                  <div className="grid grid-cols-3 gap-3 bg-indigo-50 rounded-lg p-3">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">模式</label>
                      <select value={editEvo.mode} onChange={e => setEditEvo({ ...editEvo, mode: e.target.value })} className="w-full border rounded px-2 py-1 text-sm">
                        <option value="agent">人格优化</option>
                        <option value="sphere">球面基准</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">种群</label>
                      <input type="number" value={editEvo.population_size} onChange={e => setEditEvo({ ...editEvo, population_size: +e.target.value || 50 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">代数</label>
                      <input type="number" value={editEvo.max_generations} onChange={e => setEditEvo({ ...editEvo, max_generations: +e.target.value || 50 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">变异率</label>
                      <input type="number" step="0.01" value={editEvo.mutation_rate} onChange={e => setEditEvo({ ...editEvo, mutation_rate: +e.target.value || 0.1 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">精英数</label>
                      <input type="number" value={editEvo.elite_size} onChange={e => setEditEvo({ ...editEvo, elite_size: +e.target.value || 2 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">种子</label>
                      <input type="number" value={editEvo.seed} onChange={e => setEditEvo({ ...editEvo, seed: +e.target.value || 42 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                  </div>
                )}
              </section>

              {/* Config: RL Training */}
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-gray-700">RL 训练</h4>
                  <button
                    onClick={() => setEditRlEnabled(!editRlEnabled)}
                    className={`relative w-10 h-5 rounded-full transition-colors ${editRlEnabled ? 'bg-purple-600' : 'bg-gray-300'}`}
                  >
                    <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${editRlEnabled ? 'translate-x-5' : ''}`} />
                  </button>
                </div>
                {editRlEnabled && (
                  <div className="grid grid-cols-3 gap-3 bg-rose-50 rounded-lg p-3">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">算法</label>
                      <select value={editRl.algorithm} onChange={e => setEditRl({ ...editRl, algorithm: e.target.value })} className="w-full border rounded px-2 py-1 text-sm">
                        <option value="PPO">PPO</option>
                        <option value="DQN">DQN</option>
                        <option value="REINFORCE">REINFORCE</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">总步数</label>
                      <input type="number" value={editRl.total_steps} onChange={e => setEditRl({ ...editRl, total_steps: +e.target.value || 200 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">学习率</label>
                      <input type="number" step="0.0001" value={editRl.learning_rate} onChange={e => setEditRl({ ...editRl, learning_rate: +e.target.value || 0.001 })} className="w-full border rounded px-2 py-1 text-sm" />
                    </div>
                  </div>
                )}
              </section>
            </div>

            {/* Modal footer */}
            <div className="flex items-center justify-between p-4 border-t bg-gray-50">
              <div className="flex gap-3">
                <button
                  onClick={() => onSelect?.(detail.agent_id)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  发起对话
                </button>
                <button
                  onClick={saveEdit}
                  className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700"
                >
                  保存配置
                </button>
              </div>
              <button
                onClick={() => { handleDelete(detail.agent_id); }}
                className="text-sm text-red-500 hover:text-red-700"
              >
                删除智能体
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {detailLoading && (
        <div className="fixed inset-0 bg-black/20 z-50 flex items-center justify-center">
          <div className="bg-white rounded-xl p-4 shadow-lg flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-600">加载中...</span>
          </div>
        </div>
      )}
    </div>
  );
}
