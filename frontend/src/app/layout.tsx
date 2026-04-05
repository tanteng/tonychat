import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'TonyChat - 文档问答助手',
  description: '基于 RAG 的智能文档问答助手',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
