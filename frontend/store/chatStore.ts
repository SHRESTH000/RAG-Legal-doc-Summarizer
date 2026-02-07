import { create } from 'zustand';
import type { ChatSession, ChatMessage } from '@/types/chat';
import { STORAGE_KEYS } from '@/utils/constants';

function loadSessions(): Record<string, ChatSession> {
  if (typeof window === 'undefined') return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.SESSIONS);
    return raw ? (JSON.parse(raw) as Record<string, ChatSession>) : {};
  } catch {
    return {};
  }
}

function saveSessions(sessions: Record<string, ChatSession>) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
}

function loadActiveId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION_ID);
}

function saveActiveId(id: string | null) {
  if (typeof window === 'undefined') return;
  if (id) localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION_ID, id);
  else localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION_ID);
}

function generateId(): string {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

interface ChatStore {
  sessions: Record<string, ChatSession>;
  activeSessionId: string | null;
  hydrate: () => void;
  createSession: () => string;
  setActiveSession: (id: string | null) => void;
  getActiveSession: () => ChatSession | null;
  addMessage: (sessionId: string, message: ChatMessage) => void;
  updateMessage: (sessionId: string, messageId: string, content: string) => void;
  setSessionTitle: (sessionId: string, title: string) => void;
  deleteSession: (sessionId: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  sessions: {},
  activeSessionId: null,

  hydrate: () => {
    set({
      sessions: loadSessions(),
      activeSessionId: loadActiveId(),
    });
  },

  createSession: () => {
    const id = generateId();
    const session: ChatSession = {
      session_id: id,
      title: 'New chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((state) => {
      const next = { ...state.sessions, [id]: session };
      saveSessions(next);
      saveActiveId(id);
      return { sessions: next, activeSessionId: id };
    });
    return id;
  },

  setActiveSession: (id) => {
    saveActiveId(id);
    set({ activeSessionId: id });
  },

  getActiveSession: () => {
    const { sessions, activeSessionId } = get();
    return activeSessionId ? sessions[activeSessionId] ?? null : null;
  },

  updateMessage: (sessionId: string, messageId: string, content: string) => {
    set((state) => {
      const session = state.sessions[sessionId];
      if (!session) return state;
      const messages = session.messages.map((m) =>
        m.id === messageId ? { ...m, content } : m
      );
      const updated = { ...session, messages, updatedAt: Date.now() };
      const next = { ...state.sessions, [sessionId]: updated };
      saveSessions(next);
      return { sessions: next };
    });
  },

  addMessage: (sessionId, message) => {
    set((state) => {
      const session = state.sessions[sessionId];
      if (!session) return state;
      const updated: ChatSession = {
        ...session,
        messages: [...session.messages, message],
        updatedAt: Date.now(),
        title:
          session.messages.length === 0 && message.role === 'user'
            ? message.content.slice(0, 50) + (message.content.length > 50 ? '…' : '')
            : session.title,
      };
      const next = { ...state.sessions, [sessionId]: updated };
      saveSessions(next);
      return { sessions: next };
    });
  },

  setSessionTitle: (sessionId, title) => {
    set((state) => {
      const session = state.sessions[sessionId];
      if (!session) return state;
      const updated = { ...session, title, updatedAt: Date.now() };
      const next = { ...state.sessions, [sessionId]: updated };
      saveSessions(next);
      return { sessions: next };
    });
  },

  deleteSession: (sessionId) => {
    set((state) => {
      const { [sessionId]: _, ...rest } = state.sessions;
      saveSessions(rest);
      const nextActive =
        state.activeSessionId === sessionId ? null : state.activeSessionId;
      saveActiveId(nextActive);
      return { sessions: rest, activeSessionId: nextActive };
    });
  },
}));
