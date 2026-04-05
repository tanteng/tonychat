'use client';

import { useChat } from '@/context/ChatContext';
import { Button } from '@/components/ui/Button';

export function SessionList() {
  const { state, selectSession, createNewSession, removeSession } = useChat();

  return (
    <div className="space-y-2">
      <Button onClick={createNewSession} className="w-full">
        + 新建会话
      </Button>

      <div className="space-y-1">
        {state.sessions.map((session) => (
          <div
            key={session.id}
            className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer ${
              state.currentSessionId === session.id
                ? 'bg-gray-100'
                : 'hover:bg-gray-50'
            }`}
            onClick={() => selectSession(session.id)}
          >
            <span className="truncate flex-1">{session.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeSession(session.id);
              }}
              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500"
            >
              &times;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
