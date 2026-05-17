import { atom } from 'jotai';
import type { SessionResponse, AgentSummary, FrontendMessage, MonitorMessage } from '../types/api';

export const sessionsAtom = atom<SessionResponse[]>([]);
export const activeSessionAtom = atom<string | null>(null);
export const messagesAtom = atom<Map<string, FrontendMessage[]>>(new Map());
export const agentsAtom = atom<AgentSummary[]>([]);
export const connectionStatusAtom = atom<'connected' | 'disconnected' | 'reconnecting'>('disconnected');

// Monitor atoms
export const monitorMessagesAtom = atom<MonitorMessage[]>([]);
export const monitorPausedAtom = atom(false);

// Dashboard atoms
export const dashboardTabAtom = atom<'evolution' | 'rl'>('evolution');
export const evolutionDataAtom = atom<EvolutionDashboardData | null>(null);
export const rlDataAtom = atom<TrainingDashboardData | null>(null);

// Import for dashboard type references
import type { EvolutionDashboardData, TrainingDashboardData } from '../types/api';
