import { Message } from '@/types';

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-900'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.created_at && (
          <p className={`text-xs mt-1 ${isUser ? 'text-gray-400' : 'text-gray-500'}`}>
            {new Date(message.created_at).toLocaleString('zh-CN', {
              timeZone: 'Asia/Shanghai',
            })}
          </p>
        )}
      </div>
    </div>
  );
}