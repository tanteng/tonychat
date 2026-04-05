'use client';

import { ChatProvider } from '@/context/ChatContext';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { ChatArea } from '@/components/chat/ChatArea';
import { useEffect } from 'react';
import { useChat } from '@/context/ChatContext';

function HomeContent() {
  const { loadSessions } = useChat();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <ChatArea />
    </div>
  );
}

export default function Home() {
  return (
    <ChatProvider>
      <HomeContent />
    </ChatProvider>
  );
}
