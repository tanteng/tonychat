'use client';

import { useEffect, useRef } from 'react';
import { useChat } from '@/context/ChatContext';
import { MessageItem } from './MessageItem';

export function MessageList() {
  const { state } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages, state.streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {state.messages.map((msg, i) => (
        <MessageItem key={i} message={msg} />
      ))}

      {state.isStreaming && state.streamingContent && (
        <MessageItem message={{ role: 'assistant', content: state.streamingContent }} />
      )}

      <div ref={bottomRef} />
    </div>
  );
}