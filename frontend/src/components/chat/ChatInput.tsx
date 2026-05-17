import { useState, useRef, useCallback, type KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 160) + 'px';
    }
  }, []);

  const send = () => {
    if (content.trim()) {
      onSend(content.trim());
      setContent('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="border-t border-gray-100 px-4 py-3">
      <div className="flex items-end gap-2 bg-gray-50 rounded-2xl px-4 py-2 border border-gray-200 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => { setContent(e.target.value); adjustHeight(); }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="输入消息..."
          className="flex-1 resize-none bg-transparent text-sm placeholder-gray-400 focus:outline-none max-h-40 leading-relaxed"
          rows={1}
        />
        <button
          onClick={send}
          disabled={disabled || !content.trim()}
          className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white w-9 h-9 rounded-xl flex items-center justify-center disabled:opacity-40 hover:shadow-md active:scale-95 transition-all shrink-0"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      <p className="text-[10px] text-gray-300 mt-1 text-center">Enter 发送 · Shift+Enter 换行</p>
    </div>
  );
}
