import { useState, useEffect, useMemo, type ReactNode } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area,
} from 'recharts';
import { lttb } from '../../utils/lttb';
import type { DataPoint, AgentSummary } from '../../types/api';

/* ── Types ── */

interface EvoRunSummary {
  run_id: string;
  status: string;
  current_generation: number;
  max_generations: number;
  mode: string;
  best_fitness: number | null;
}
interface RLRunSummary {
  run_id: string;
  status: string;
  algorithm: string;
  current_step: number;
  total_steps: number;
  last_reward: number | null;
  last_loss: number | null;
}

interface EvoGenLog {
  generation: number;
  best_fitness: number;
  mean_fitness: number;
  std_fitness: number;
  diversity: number;
}
interface RLStepLog {
  step: number;
  reward: number;
  loss: number | null;
}

interface EvoRunDetail {
  evolution_id: string;
  current_generation: number;
  status: string;
  mode: string;
  population_size: number;
  max_generations: number;
  mutation_rate: number;
  elite_size: number;
  fitness_curves: { best: DataPoint[]; mean: DataPoint[]; std: DataPoint[] };
  gene_tree: { nodes: { id: string; generation: number; fitness: number }[]; edges: { source: string; target: string }[] } | null;
  logs: EvoGenLog[];
}
interface RLRunDetail {
  task_id: string;
  algorithm: string;
  current_step: number;
  status: string;
  total_steps: number;
  learning_rate: number;
  metrics: Record<string, DataPoint[]>;
  logs: RLStepLog[];
}

const LTTB_MAX = 2000;
function ds(data: DataPoint[]) {
  return data.length <= LTTB_MAX ? { data, downsampled: false } : { data: lttb(data, LTTB_MAX), downsampled: true };
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    running: 'bg-yellow-100 text-yellow-700',
    cancelled: 'bg-gray-100 text-gray-600',
    idle: 'bg-blue-100 text-blue-700',
  };
  const label: Record<string, string> = { completed: '已完成', running: '运行中', cancelled: '已取消', idle: '待运行' };
  const cls = map[status] || 'bg-red-100 text-red-700';
  const txt = label[status] || status;
  return <span className={`text-xs px-2 py-0.5 rounded font-medium ${cls}`}>{txt}</span>;
}

/* ── Shared UI ── */

function ChartCard({ title, children, onZoom, extra }: { title: string; children: ReactNode; onZoom?: () => void; extra?: ReactNode }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-700">{title}</h4>
        <div className="flex items-center gap-2">
          {extra}
          {onZoom && (
            <button onClick={onZoom} className="text-xs text-blue-500 hover:text-blue-700 px-2 py-0.5 rounded hover:bg-blue-50">⤢ 放大</button>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

function ZoomOverlay({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/50 z-[70] flex items-center justify-center p-6" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 w-full max-w-5xl max-h-[90vh] overflow-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100">×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ── Gene Tree ── */

function GeneTreeView({ tree }: { tree: { nodes: { id: string; generation: number; fitness: number }[]; edges: { source: string; target: string }[] } }) {
  const { nodes, edges } = tree;
  if (!nodes?.length) return <p className="text-sm text-gray-400">暂无树数据</p>;

  const genMap = new Map<number, typeof nodes>();
  for (const n of nodes) { const a = genMap.get(n.generation) || []; a.push(n); genMap.set(n.generation, a); }
  const gens = [...genMap.keys()].sort((a, b) => a - b);

  const fits = nodes.map(n => n.fitness);
  const minF = Math.min(...fits), range = Math.max(...fits) - minF || 1;
  const color = (f: number) => { const t = (f - minF) / range; return `rgb(${Math.round(255 * (1 - t))},${Math.round(255 * t)},80)`; };

  const W = 900, R = 8, GH = 60, svgH = Math.max(200, gens.length * GH + 40);
  const pos = new Map<string, { x: number; y: number }>();
  gens.forEach((g, gi) => { const ns = genMap.get(g) || []; const sp = W / (ns.length + 1); ns.forEach((n, ni) => pos.set(n.id, { x: sp * (ni + 1), y: 30 + gi * GH })); });

  return (
    <div className="overflow-x-auto">
      <svg width={W} height={svgH} className="block">
        {edges.map((e, i) => { const s = pos.get(e.source), t = pos.get(e.target); return s && t ? <line key={`e${i}`} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#d1d5db" strokeWidth={1} opacity={0.6} /> : null; })}
        {nodes.map(n => { const p = pos.get(n.id); return p ? <circle key={n.id} cx={p.x} cy={p.y} r={R} fill={color(n.fitness)} stroke="#fff" strokeWidth={1.5} opacity={0.85}><title>Gen {n.generation} | Fitness: {n.fitness.toFixed(4)}</title></circle> : null; })}
        {gens.map(g => { const f = genMap.get(g)?.[0]; const p = f ? pos.get(f.id) : null; return p ? <text key={`g${g}`} x={12} y={p.y + 4} fill="#9ca3af" fontSize={10}>Gen {g}</text> : null; })}
      </svg>
      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
        <span>适应度：</span>
        <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-full" style={{ background: 'rgb(255,0,80)' }} />低</span>
        <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-full" style={{ background: 'rgb(0,255,80)' }} />高</span>
        <span className="ml-4">{nodes.length} 个体, {gens.length} 代</span>
      </div>
    </div>
  );
}

/* ── Evo Run Detail: left logs + right charts ── */

function EvoRunDetail({ runId, apiBase }: { runId: string; apiBase: string }) {
  const [detail, setDetail] = useState<EvoRunDetail | null>(null);
  const [zoomed, setZoomed] = useState<'fitness' | 'area' | 'tree' | null>(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/api/evolution/${runId}`);
        const d = await res.json();
        if (d.error || !alive) return;
        setDetail(d);
        if (d.status === 'running') setTimeout(load, 1500);
      } catch { /* */ }
    };
    load();
    return () => { alive = false; };
  }, [runId, apiBase]);

  const curves = detail?.fitness_curves;
  const tree = detail?.gene_tree;

  const chartData = useMemo(() => {
    if (!curves) return null;
    const b = ds(curves.best), m = ds(curves.mean), s = ds(curves.std);
    return {
      merged: b.data.map((p, i) => ({ gen: p.x, best: +p.y.toFixed(4), mean: m.data[i] ? +m.data[i].y.toFixed(4) : 0, std: s.data[i] ? +s.data[i].y.toFixed(4) : 0 })),
      downsampled: b.downsampled || m.downsampled || s.downsampled,
    };
  }, [curves]);

  const renderLine = (h: number) => chartData && (
    <ResponsiveContainer width="100%" height={h}>
      <LineChart data={chartData.merged}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="gen" label={{ value: '代数', position: 'insideBottom', offset: -5 }} />
        <YAxis label={{ value: '适应度', angle: -90, position: 'insideLeft' }} />
        <Tooltip /><Legend />
        <Line type="monotone" dataKey="best" stroke="#3b82f6" strokeWidth={2} dot={false} name="最优" />
        <Line type="monotone" dataKey="mean" stroke="#22c55e" strokeWidth={2} dot={false} name="均值" />
        <Line type="monotone" dataKey="std" stroke="#f97316" strokeWidth={1.5} dot={false} name="标准差" strokeDasharray="5 5" />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderArea = (h: number) => chartData && (
    <ResponsiveContainer width="100%" height={h}>
      <AreaChart data={chartData.merged}>
        <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="gen" /><YAxis /><Tooltip />
        <Area type="monotone" dataKey="best" stroke="#3b82f6" fill="#3b82f620" name="最优" />
        <Area type="monotone" dataKey="mean" stroke="#22c55e" fill="#22c55e20" name="均值" />
      </AreaChart>
    </ResponsiveContainer>
  );

  if (!detail) return <p className="text-sm text-gray-400 py-4">加载中...</p>;

  const logs = detail.logs || [];

  return (
    <div className="space-y-3">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="bg-blue-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">模式</p><p className="text-sm font-bold text-blue-600">{detail.mode === 'agent' ? '智能体优化' : '基准测试'}</p></div>
        <div className="bg-green-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">种群 × 代数</p><p className="text-sm font-bold text-green-600">{detail.population_size} × {detail.max_generations}</p></div>
        <div className="bg-purple-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">变异率</p><p className="text-sm font-bold text-purple-600">{detail.mutation_rate}</p></div>
        <div className="bg-orange-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">精英数</p><p className="text-sm font-bold text-orange-600">{detail.elite_size}</p></div>
      </div>

      {/* Left-right split: logs | charts */}
      <div className="flex gap-4 min-h-[420px]">
        {/* Left: Logs */}
        <div className="w-[45%] flex flex-col border rounded-xl overflow-hidden">
          <div className="bg-gray-50 px-3 py-2 border-b">
            <h4 className="text-xs font-semibold text-gray-600">训练日志 ({logs.length} 条)</h4>
          </div>
          <div className="flex-1 overflow-y-auto text-xs font-mono">
            {logs.length === 0 ? (
              <p className="p-3 text-gray-400">暂无日志数据</p>
            ) : (
              <table className="w-full">
                <thead className="sticky top-0 bg-gray-50">
                  <tr className="text-left text-gray-500">
                    <th className="px-2 py-1.5 font-medium">代数</th>
                    <th className="px-2 py-1.5 font-medium">最优</th>
                    <th className="px-2 py-1.5 font-medium">均值</th>
                    <th className="px-2 py-1.5 font-medium">标准差</th>
                    <th className="px-2 py-1.5 font-medium">多样性</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                      <td className="px-2 py-1 text-gray-600">{log.generation}</td>
                      <td className="px-2 py-1 text-blue-600 font-medium">{log.best_fitness.toFixed(4)}</td>
                      <td className="px-2 py-1 text-green-600">{log.mean_fitness.toFixed(4)}</td>
                      <td className="px-2 py-1 text-orange-600">{log.std_fitness.toFixed(4)}</td>
                      <td className="px-2 py-1 text-gray-500">{log.diversity.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right: Charts */}
        <div className="flex-1 min-w-0 space-y-3 overflow-y-auto">
          {chartData && (
            <>
              <ChartCard title="适应度曲线" onZoom={() => setZoomed('fitness')} extra={chartData.downsampled ? <span className="text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded">已降采样</span> : undefined}>
                {renderLine(240)}
              </ChartCard>
              <ChartCard title="适应度分布（面积图）" onZoom={() => setZoomed('area')}>
                {renderArea(180)}
              </ChartCard>
            </>
          )}
          {tree && tree.nodes.length > 0 && (
            <ChartCard title="进化树" onZoom={() => setZoomed('tree')}><GeneTreeView tree={tree} /></ChartCard>
          )}
          {!chartData && (!tree || tree.nodes.length === 0) && (
            <p className="text-sm text-gray-400 py-8 text-center">暂无图表数据</p>
          )}
        </div>
      </div>

      {zoomed && (
        <ZoomOverlay title={zoomed === 'fitness' ? '适应度曲线' : zoomed === 'area' ? '适应度分布' : '进化树'} onClose={() => setZoomed(null)}>
          {zoomed === 'fitness' && renderLine(500)}
          {zoomed === 'area' && renderArea(400)}
          {zoomed === 'tree' && tree && <GeneTreeView tree={tree} />}
        </ZoomOverlay>
      )}
    </div>
  );
}

/* ── RL Run Detail: left logs + right charts ── */

function RLRunDetail({ runId, apiBase }: { runId: string; apiBase: string }) {
  const [detail, setDetail] = useState<RLRunDetail | null>(null);
  const [zoomed, setZoomed] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/api/rl/${runId}`);
        const d = await res.json();
        if (d.error || !alive) return;
        setDetail(d);
        if (d.status === 'running') setTimeout(load, 1500);
      } catch { /* */ }
    };
    load();
    return () => { alive = false; };
  }, [runId, apiBase]);

  const metrics = detail?.metrics || {};
  const metricEntries = useMemo(() => Object.entries(metrics).map(([name, points]) => {
    const d = points && points.length > LTTB_MAX ? { data: lttb(points, LTTB_MAX), downsampled: true } : { data: points || [], downsampled: false };
    return { name, data: d.data.map(p => ({ step: p.x, value: +p.y.toFixed(4) })), color: name === 'reward' ? '#8b5cf6' : '#ef4444', label: name === 'reward' ? '累计奖励' : name === 'loss' ? '损失函数' : name, downsampled: d.downsampled };
  }), [metrics]);

  const rewardArr = metrics.reward || [];
  const lossArr = metrics.loss || [];

  const renderMetric = (name: string, h: number) => {
    const m = metricEntries.find(e => e.name === name);
    if (!m) return null;
    return (
      <ResponsiveContainer width="100%" height={h}>
        <LineChart data={m.data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="step" label={{ value: '步数', position: 'insideBottom', offset: -5 }} /><YAxis /><Tooltip />
          <Line type="monotone" dataKey="value" stroke={m.color} strokeWidth={2} dot={false} name={m.label} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderCombined = (h: number) => {
    const r = rewardArr.length > LTTB_MAX ? lttb(rewardArr, LTTB_MAX) : rewardArr;
    const l = lossArr.length > LTTB_MAX ? lttb(lossArr, LTTB_MAX) : lossArr;
    return (
      <ResponsiveContainer width="100%" height={h}>
        <LineChart data={r.map((p, i) => ({ step: p.x, reward: +p.y.toFixed(4), loss: l[i] ? +l[i].y.toFixed(4) : 0 }))}>
          <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="step" /><YAxis yAxisId="left" /><YAxis yAxisId="right" orientation="right" /><Tooltip /><Legend />
          <Line yAxisId="left" type="monotone" dataKey="reward" stroke="#8b5cf6" strokeWidth={2} dot={false} name="奖励" />
          <Line yAxisId="right" type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={false} name="损失" />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  if (!detail) return <p className="text-sm text-gray-400 py-4">加载中...</p>;

  const logs = detail.logs || [];

  return (
    <div className="space-y-3">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="bg-purple-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">算法</p><p className="text-sm font-bold text-purple-600">{detail.algorithm}</p></div>
        <div className="bg-blue-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">步数</p><p className="text-sm font-bold text-blue-600">{detail.current_step} / {detail.total_steps}</p></div>
        <div className="bg-green-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">学习率</p><p className="text-sm font-bold text-green-600">{detail.learning_rate}</p></div>
        <div className="bg-red-50 rounded-lg p-2"><p className="text-[10px] text-gray-500">状态</p><p className="text-sm font-bold text-red-600">{detail.status === 'completed' ? '已完成' : detail.status === 'running' ? '运行中' : detail.status}</p></div>
      </div>

      {/* Left-right split: logs | charts */}
      <div className="flex gap-4 min-h-[420px]">
        {/* Left: Logs */}
        <div className="w-[45%] flex flex-col border rounded-xl overflow-hidden">
          <div className="bg-gray-50 px-3 py-2 border-b">
            <h4 className="text-xs font-semibold text-gray-600">训练日志 ({logs.length} 条)</h4>
          </div>
          <div className="flex-1 overflow-y-auto text-xs font-mono">
            {logs.length === 0 ? (
              <p className="p-3 text-gray-400">暂无日志数据</p>
            ) : (
              <table className="w-full">
                <thead className="sticky top-0 bg-gray-50">
                  <tr className="text-left text-gray-500">
                    <th className="px-2 py-1.5 font-medium">步数</th>
                    <th className="px-2 py-1.5 font-medium">奖励</th>
                    <th className="px-2 py-1.5 font-medium">损失</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                      <td className="px-2 py-1 text-gray-600">{log.step}</td>
                      <td className="px-2 py-1 text-purple-600 font-medium">{log.reward.toFixed(4)}</td>
                      <td className="px-2 py-1 text-red-600">{log.loss !== null ? log.loss.toFixed(4) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right: Charts */}
        <div className="flex-1 min-w-0 space-y-3 overflow-y-auto">
          {metricEntries.map(m => (
            <ChartCard key={m.name} title={m.label} onZoom={() => setZoomed(m.name)} extra={m.downsampled ? <span className="text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded">已降采样</span> : undefined}>
              {renderMetric(m.name, 180)}
            </ChartCard>
          ))}
          {metricEntries.length >= 2 && (
            <ChartCard title="奖励 vs 损失（对比）" onZoom={() => setZoomed('combined')}>{renderCombined(180)}</ChartCard>
          )}
          {metricEntries.length === 0 && (
            <p className="text-sm text-gray-400 py-8 text-center">暂无图表数据</p>
          )}
        </div>
      </div>

      {zoomed && (
        <ZoomOverlay title={zoomed === 'combined' ? '奖励 vs 损失' : metricEntries.find(m => m.name === zoomed)?.label || zoomed} onClose={() => setZoomed(null)}>
          {zoomed === 'combined' ? renderCombined(500) : renderMetric(zoomed, 500)}
        </ZoomOverlay>
      )}
    </div>
  );
}

/* ── Evolution Tab (training records) ── */

function EvolutionTab({ agentId, apiBase }: { agentId: string; apiBase: string }) {
  const [runs, setRuns] = useState<EvoRunSummary[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadRuns = async () => {
    try {
      const res = await fetch(`${apiBase}/api/agents/${agentId}/evolution/runs`);
      const data = await res.json();
      if (Array.isArray(data)) setRuns(data);
    } catch { /* */ }
  };

  useEffect(() => {
    loadRuns();
    const iv = setInterval(loadRuns, 5000);
    return () => clearInterval(iv);
  }, [agentId, apiBase]);

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">进化引擎训练记录</p>

      {runs.length === 0 && (
        <div className="text-center py-10">
          <p className="text-gray-400">暂无训练记录</p>
          <p className="text-gray-400 text-xs mt-1">在智能体配置中启用进化引擎后，训练记录将显示在此处</p>
        </div>
      )}

      {runs.map(run => (
        <div key={run.run_id} className="border rounded-xl overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
            onClick={() => setExpandedId(expandedId === run.run_id ? null : run.run_id)}
          >
            <div className="flex items-center gap-3">
              {statusBadge(run.status)}
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {run.mode === 'agent' ? '智能体人格优化' : '经典基准'}
                </p>
                <p className="text-xs text-gray-400">
                  第 {run.current_generation} / {run.max_generations} 代
                  {run.best_fitness !== null && ` · 最优适应度 ${run.best_fitness.toFixed(4)}`}
                </p>
              </div>
            </div>
            <span className="text-gray-400 text-sm">{expandedId === run.run_id ? '▾' : '▸'}</span>
          </button>

          {expandedId === run.run_id && (
            <div className="border-t p-4 bg-gray-50/50">
              <EvoRunDetail runId={run.run_id} apiBase={apiBase} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── RL Tab (training records) ── */

function RLTab({ agentId, apiBase }: { agentId: string; apiBase: string }) {
  const [runs, setRuns] = useState<RLRunSummary[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadRuns = async () => {
    try {
      const res = await fetch(`${apiBase}/api/agents/${agentId}/rl/runs`);
      const data = await res.json();
      if (Array.isArray(data)) setRuns(data);
    } catch { /* */ }
  };

  useEffect(() => {
    loadRuns();
    const iv = setInterval(loadRuns, 5000);
    return () => clearInterval(iv);
  }, [agentId, apiBase]);

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">强化学习训练记录</p>

      {runs.length === 0 && (
        <div className="text-center py-10">
          <p className="text-gray-400">暂无训练记录</p>
          <p className="text-gray-400 text-xs mt-1">在智能体配置中启用强化学习后，训练记录将显示在此处</p>
        </div>
      )}

      {runs.map(run => (
        <div key={run.run_id} className="border rounded-xl overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
            onClick={() => setExpandedId(expandedId === run.run_id ? null : run.run_id)}
          >
            <div className="flex items-center gap-3">
              {statusBadge(run.status)}
              <div>
                <p className="text-sm font-medium text-gray-800">{run.algorithm} 训练</p>
                <p className="text-xs text-gray-400">
                  {run.current_step} / {run.total_steps} 步
                  {run.last_reward !== null && ` · 奖励 ${run.last_reward.toFixed(2)}`}
                  {run.last_loss !== null && ` · 损失 ${run.last_loss.toFixed(4)}`}
                </p>
              </div>
            </div>
            <span className="text-gray-400 text-sm">{expandedId === run.run_id ? '▾' : '▸'}</span>
          </button>

          {expandedId === run.run_id && (
            <div className="border-t p-4 bg-gray-50/50">
              <RLRunDetail runId={run.run_id} apiBase={apiBase} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Agent Dashboard Modal ── */

function AgentDashboardModal({ agent, apiBase, onClose }: { agent: AgentSummary; apiBase: string; onClose: () => void }) {
  const [tab, setTab] = useState<'evolution' | 'rl'>('evolution');
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-5 border-b bg-gray-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold">{agent.name.charAt(0).toUpperCase()}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{agent.name}</h3>
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${agent.status === 'ONLINE' ? 'bg-green-500' : 'bg-gray-400'}`} />
              {agent.status === 'ONLINE' ? '在线' : '离线'}
            </span>
          </div>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-200">×</button>
      </div>
      <div className="flex border-b">
        {(['evolution', 'rl'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} className={`flex-1 px-4 py-3 text-sm font-medium text-center border-b-2 transition-colors ${tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t === 'evolution' ? '进化引擎' : '强化学习'}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-5">
        {tab === 'evolution' && <EvolutionTab agentId={agent.agent_id} apiBase={apiBase} />}
        {tab === 'rl' && <RLTab agentId={agent.agent_id} apiBase={apiBase} />}
      </div>
    </div>
  );
}

/* ── Main Dashboard ── */

export function DashboardPage({ agents, apiBase }: { agents: AgentSummary[]; apiBase: string }) {
  const [selectedAgent, setSelectedAgent] = useState<AgentSummary | null>(null);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 pb-2">
        <h2 className="text-lg font-semibold text-gray-800">仪表盘</h2>
        <p className="text-xs text-gray-500">点击智能体卡片查看训练记录</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {agents.length === 0 ? (
          <div className="text-center mt-20">
            <p className="text-gray-400 text-lg">暂无智能体</p>
            <p className="text-gray-400 text-sm mt-2">请先在「智能体」页面创建</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {agents.map(agent => (
              <div key={agent.agent_id} className="bg-white rounded-xl shadow-sm border p-5 cursor-pointer hover:shadow-md transition-all" onClick={() => setSelectedAgent(agent)}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-11 h-11 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold text-lg shrink-0">
                    {agent.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-800 truncate">{agent.name}</p>
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${agent.status === 'ONLINE' ? 'bg-green-500' : 'bg-gray-400'}`} />
                      {agent.status === 'ONLINE' ? '在线' : '离线'}
                    </p>
                  </div>
                </div>
                {agent.system_prompt && <p className="text-xs text-gray-500 line-clamp-2">{agent.system_prompt}</p>}
                <div className="mt-3 flex gap-2">
                  <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">进化引擎</span>
                  <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded">强化学习</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedAgent && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setSelectedAgent(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <AgentDashboardModal agent={selectedAgent} apiBase={apiBase} onClose={() => setSelectedAgent(null)} />
          </div>
        </div>
      )}
    </div>
  );
}
