import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react';

interface Agent {
  agent_id: string;
  name: string;
}

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  agents?: Agent[];
}

export function ChatInput({ onSend, disabled, agents = [] }: ChatInputProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showMention, setShowMention] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [mentionIndex, setMentionIndex] = useState(0);
  const mentionRef = useRef<HTMLDivElement>(null);

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
      setShowMention(false);
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  // Detect @ trigger
  const handleChange = (val: string) => {
    setContent(val);
    adjustHeight();

    const cursorPos = textareaRef.current?.selectionStart ?? val.length;
    const textBefore = val.slice(0, cursorPos);
    const atMatch = textBefore.match(/@([^\s@]*)$/);
    if (atMatch) {
      setShowMention(true);
      setMentionFilter(atMatch[1].toLowerCase());
      setMentionIndex(0);
    } else {
      setShowMention(false);
    }
  };

  const filteredAgents = agents.filter((a) =>
    a.name.toLowerCase().includes(mentionFilter)
  );

  const insertMention = (name: string) => {
    const cursorPos = textareaRef.current?.selectionStart ?? content.length;
    const textBefore = content.slice(0, cursorPos);
    const textAfter = content.slice(cursorPos);
    const replaced = textBefore.replace(/@[^\s@]*$/, `@${name} `);
    setContent(replaced + textAfter);
    setShowMention(false);
    // focus back
    setTimeout(() => {
      const newPos = replaced.length + 1;
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(newPos, newPos);
      adjustHeight();
    }, 0);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showMention && filteredAgents.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMentionIndex((i) => (i + 1) % filteredAgents.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMentionIndex((i) => (i - 1 + filteredAgents.length) % filteredAgents.length);
        return;
      }
      if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        insertMention(filteredAgents[mentionIndex].name);
        return;
      }
      if (e.key === 'Escape') {
        setShowMention(false);
        return;
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // Close mention on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (mentionRef.current && !mentionRef.current.contains(e.target as Node)) {
        setShowMention(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="border-t border-gray-100 px-4 py-3 relative" ref={mentionRef}>
      {/* Mention dropdown */}
      {showMention && filteredAgents.length > 0 && (
        <div className="absolute bottom-full left-4 right-4 mb-1 bg-white rounded-xl shadow-lg border border-gray-200 py-1 max-h-48 overflow-y-auto z-50">
          {filteredAgents.map((agent, i) => (
            <button
              key={agent.agent_id}
              className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors ${
                i === mentionIndex ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'
              }`}
              onMouseDown={(e) => { e.preventDefault(); insertMention(agent.name); }}
              onMouseEnter={() => setMentionIndex(i)}
            >
              <span className="text-blue-500 font-medium">@</span>
              <span className="font-medium">{agent.name}</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 bg-gray-50 rounded-2xl px-4 py-2 border border-gray-200 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="输入消息...（@ 提及 Agent）"
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
      <p className="text-[10px] text-gray-300 mt-1 text-center">Enter 发送 · @ 提及 · Shift+Enter 换行</p>
    </div>
  );
}
