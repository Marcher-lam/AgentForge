import { useRef, useEffect, type ReactNode } from 'react';
import type { FrontendMessage } from '../../types/api';

interface MessagePanelProps {
  messages: FrontendMessage[];
  onLoadMore?: () => void;
  hasMore?: boolean;
}

function renderContent(msg: FrontendMessage): ReactNode {
  switch (msg.content_type) {
    case 'CODE':
      return (
        <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-sm overflow-x-auto">
          <code>{msg.content}</code>
        </pre>
      );
    case 'MARKDOWN':
      return <div className="prose prose-sm max-w-none">{msg.content}</div>;
    case 'IMAGE':
      return <img src={msg.content} alt="" className="max-w-xs rounded-lg" />;
    case 'SYSTEM':
      return <p className="text-gray-500 text-sm italic text-center">{msg.content}</p>;
    default:
      return <p className="whitespace-pre-wrap">{msg.content}</p>;
  }
}

export function MessagePanel({ messages, onLoadMore, hasMore }: MessagePanelProps) {
  const topRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hasMore) {
      const observer = new IntersectionObserver(
        (entries) => { if (entries[0].isIntersecting) onLoadMore?.(); },
        { threshold: 0.1 }
      );
      if (topRef.current) observer.observe(topRef.current);
      return () => observer.disconnect();
    }
  }, [hasMore, onLoadMore]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 space-y-3">
      {hasMore && <div ref={topRef} className="text-center text-gray-400 text-sm py-2">加载更多...</div>}
      {messages.map((msg) => (
        <div
          key={msg.message_id}
          className={`flex ${msg.sender_type === 'USER' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            msg.sender_type === 'USER'
              ? 'bg-blue-600 text-white'
              : msg.sender_type === 'SYSTEM'
              ? 'bg-transparent'
              : 'bg-gray-100 text-gray-900'
          }`}>
            {msg.sender_type === 'AGENT' && (
              <p className="text-xs font-semibold text-blue-600 mb-1">{msg.sender_name}</p>
            )}
            {renderContent(msg)}
          </div>
        </div>
      ))}
    </div>
  );
}
