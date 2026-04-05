'use client';

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { Message, Session } from '@/types';
import { getSessions, createSession, deleteSession, getSessionMessages, chat } from '@/lib/api';

interface ChatState {
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
}

type ChatAction =
  | { type: 'SET_SESSIONS'; payload: Session[] }
  | { type: 'ADD_SESSION'; payload: Session }
  | { type: 'DELETE_SESSION'; payload: string }
  | { type: 'SELECT_SESSION'; payload: string }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'START_STREAMING' }
  | { type: 'STREAM_UPDATE'; payload: string }
  | { type: 'END_STREAMING' };

const initialState: ChatState = {
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'ADD_SESSION':
      return { ...state, sessions: [action.payload, ...state.sessions] };
    case 'DELETE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter((s) => s.id !== action.payload),
        currentSessionId: state.currentSessionId === action.payload ? null : state.currentSessionId,
      };
    case 'SELECT_SESSION':
      return { ...state, currentSessionId: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'START_STREAMING':
      return { ...state, isStreaming: true, streamingContent: '' };
    case 'STREAM_UPDATE':
      return { ...state, streamingContent: state.streamingContent + action.payload };
    case 'END_STREAMING':
      return {
        ...state,
        isStreaming: false,
        messages: state.messages.concat({
          role: 'assistant',
          content: state.streamingContent,
        }),
        streamingContent: '',
      };
    default:
      return state;
  }
}

interface ChatContextType {
  state: ChatState;
  loadSessions: () => Promise<void>;
  selectSession: (id: string) => Promise<void>;
  createNewSession: () => Promise<void>;
  removeSession: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const loadSessions = useCallback(async () => {
    const data = await getSessions();
    dispatch({ type: 'SET_SESSIONS', payload: data.sessions });
  }, []);

  const selectSession = useCallback(async (id: string) => {
    dispatch({ type: 'SELECT_SESSION', payload: id });
    const data = await getSessionMessages(id);
    dispatch({ type: 'SET_MESSAGES', payload: data.messages });
  }, []);

  const createNewSession = useCallback(async () => {
    const data = await createSession();
    dispatch({ type: 'ADD_SESSION', payload: data.session });
    dispatch({ type: 'SELECT_SESSION', payload: data.session.id });
    dispatch({ type: 'SET_MESSAGES', payload: [] });
  }, []);

  const removeSession = useCallback(async (id: string) => {
    await deleteSession(id);
    dispatch({ type: 'DELETE_SESSION', payload: id });
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    dispatch({ type: 'ADD_MESSAGE', payload: { role: 'user', content } });
    dispatch({ type: 'START_STREAMING' });

    const controller = new AbortController();

    try {
      const response = await chat(content, state.currentSessionId || 'default');
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event: ')) continue;
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            try {
              const parsed = JSON.parse(data);
              if (parsed.delta) {
                dispatch({ type: 'STREAM_UPDATE', payload: parsed.delta });
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      dispatch({ type: 'END_STREAMING' });
    }
  }, [state.currentSessionId]);

  return (
    <ChatContext.Provider
      value={{ state, loadSessions, selectSession, createNewSession, removeSession, sendMessage }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
}
