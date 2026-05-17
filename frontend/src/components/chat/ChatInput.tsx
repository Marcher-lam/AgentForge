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

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (content.trim()) {
        onSend(content.trim());
        setContent('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className="border-t p-3 flex gap-2">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => { setContent(e.target.value); adjustHeight(); }}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="输入消息...（Enter 发送，Shift+Enter 换行）"
        className="flex-1 resize-none border rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 max-h-40"
        rows={1}
      />
      <button
        onClick={() => { if (content.trim()) { onSend(content.trim()); setContent(''); } }}
        disabled={disabled || !content.trim()}
        className="bg-blue-600 text-white px-4 py-2 rounded-xl disabled:opacity-50 hover:bg-blue-700 transition-colors"
      >
        Send
      </button>
    </div>
  );
}
