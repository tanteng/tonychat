'use client';

import { useState } from 'react';
import { useChat } from '@/context/ChatContext';
import { Button } from '@/components/ui/Button';

export function InputArea() {
  const [input, setInput] = useState('');
  const { sendMessage, state } = useChat();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || state.isStreaming) return;

    const content = input.trim();
    setInput('');
    await sendMessage(content);
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的问题..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
          disabled={state.isStreaming}
        />
        <Button type="submit" disabled={state.isStreaming || !input.trim()}>
          {state.isStreaming ? '发送中...' : '发送'}
        </Button>
      </div>
    </form>
  );
}