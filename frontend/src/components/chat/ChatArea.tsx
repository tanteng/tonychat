'use client';

import { useChat } from '@/context/ChatContext';
import { MessageList } from './MessageList';
import { InputArea } from './InputArea';

export function ChatArea() {
  const { state } = useChat();

  if (!state.currentSessionId) {
    return (
      <main className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-4xl mb-4">💬</p>
          <p className="text-gray-500">上传文档后开始提问</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col bg-white">
      <MessageList />
      <InputArea />
    </main>
  );
}