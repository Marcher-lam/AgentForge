import { useRef, useEffect, useMemo, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import type { FrontendMessage } from '../../types/api';

interface MessagePanelProps {
  messages: FrontendMessage[];
  onLoadMore?: () => void;
  hasMore?: boolean;
}

/* ---------- color utils ---------- */

function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

const GRADIENT_PAIRS: [string, string][] = [
  ['#6366f1', '#8b5cf6'], // indigo-violet
  ['#ec4899', '#f43f5e'], // pink-rose
  ['#f59e0b', '#f97316'], // amber-orange
  ['#10b981', '#06b6d4'], // emerald-cyan
  ['#3b82f6', '#6366f1'], // blue-indigo
  ['#8b5cf6', '#ec4899'], // violet-pink
  ['#14b8a6', '#22c55e'], // teal-green
  ['#ef4444', '#f97316'], // red-orange
  ['#06b6d4', '#3b82f6'], // cyan-blue
  ['#a855f7', '#6366f1'], // purple-indigo
  ['#f43f5e', '#a855f7'], // rose-purple
  ['#22c55e', '#84cc16'], // green-lime
];

function getGradient(name: string): [string, string] {
  return GRADIENT_PAIRS[hashStr(name) % GRADIENT_PAIRS.length];
}

function getBubbleBg(name: string): string {
  const [c1] = getGradient(name);
  return c1 + '12'; // 7% opacity hex
}

function getBubbleBorder(name: string): string {
  const [c1] = getGradient(name);
  return c1 + '30'; // 19% opacity
}

/* ---------- avatar ---------- */

function Avatar({ name }: { name: string }) {
  const [c1, c2] = useMemo(() => getGradient(name), [name]);
  const initial = name.slice(0, 1);
  return (
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0 shadow-sm select-none"
      style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}
    >
      {initial}
    </div>
  );
}

/* ---------- content renderer ---------- */

function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeHighlight, rehypeKatex]}
      components={{
        pre: ({ children }) => (
          <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-sm overflow-x-auto my-1.5">
            {children}
          </pre>
        ),
        code: ({ children, className, ...props }) => {
          const isInline = !className;
          return isInline ? (
            <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
              {children}
            </code>
          ) : (
            <code className={className} {...props}>{children}</code>
          );
        },
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer"
            className="text-blue-500 underline hover:text-blue-700">{children}</a>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2">
            <table className="min-w-full text-sm border-collapse">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-gray-200 px-3 py-1.5 bg-gray-50 text-left font-semibold">{children}</th>
        ),
        td: ({ children }) => (
          <td className="border border-gray-200 px-3 py-1.5">{children}</td>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-blue-300 pl-3 my-2 text-gray-600 italic">{children}</blockquote>
        ),
        ul: ({ children }) => <ul className="list-disc pl-5 my-1 space-y-0.5">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 my-1 space-y-0.5">{children}</ol>,
        h1: ({ children }) => <h1 className="text-lg font-bold mt-3 mb-1">{children}</h1>,
        h2: ({ children }) => <h2 className="text-base font-bold mt-2.5 mb-1">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-bold mt-2 mb-0.5">{children}</h3>,
        p: ({ children }) => <p className="leading-relaxed my-0.5">{children}</p>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function renderContent(msg: FrontendMessage): ReactNode {
  switch (msg.content_type) {
    case 'CODE':
      return (
        <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-sm overflow-x-auto my-1">
          <code>{msg.content}</code>
        </pre>
      );
    case 'IMAGE':
      return <img src={msg.content} alt="" className="max-w-xs rounded-lg my-1" />;
    case 'SYSTEM':
      return <p className="text-gray-400 text-xs italic text-center py-1">{msg.content}</p>;
    default:
      return <MarkdownContent content={msg.content} />;
  }
}

/* ---------- main panel ---------- */

export function MessagePanel({ messages, onLoadMore, hasMore }: MessagePanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const topRef = useRef<HTMLDivElement>(null);

  // auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // infinite scroll upward
  useEffect(() => {
    if (!hasMore) return;
    const observer = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) onLoadMore?.(); },
      { threshold: 0.1 },
    );
    if (topRef.current) observer.observe(topRef.current);
    return () => observer.disconnect();
  }, [hasMore, onLoadMore]);

  return (
    <div className="flex flex-col h-full overflow-y-auto px-4 py-3 space-y-4">
      {hasMore && (
        <div ref={topRef} className="text-center text-gray-400 text-xs py-2">
          加载更多...
        </div>
      )}

      {messages.map((msg) => {
        // system messages: centered, no bubble
        if (msg.sender_type === 'SYSTEM') {
          return (
            <div key={msg.message_id} className="flex justify-center">
              <span className="text-gray-400 text-xs bg-gray-50 px-3 py-1 rounded-full">
                {msg.content}
              </span>
            </div>
          );
        }

        // user messages: right-aligned, blue gradient
        if (msg.sender_type === 'USER') {
          return (
            <div key={msg.message_id} className="flex justify-end items-end gap-2">
              <div className="max-w-[70%] rounded-2xl rounded-br-md px-4 py-2.5 bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm">
                {renderContent(msg)}
              </div>
            </div>
          );
        }

        // agent messages: left-aligned with avatar
        const bubbleBg = getBubbleBg(msg.sender_name);
        const bubbleBorder = getBubbleBorder(msg.sender_name);
        const [c1] = getGradient(msg.sender_name);

        return (
          <div key={msg.message_id} className="flex items-start gap-2.5">
            <Avatar name={msg.sender_name} />
            <div className="max-w-[75%] min-w-0">
              <p className="text-xs font-semibold mb-1" style={{ color: c1 }}>
                {msg.sender_name}
              </p>
              <div
                className="rounded-2xl rounded-tl-md px-4 py-2.5 shadow-sm"
                style={{ backgroundColor: bubbleBg, border: `1px solid ${bubbleBorder}` }}
              >
                {renderContent(msg)}
              </div>
            </div>
          </div>
        );
      })}

      <div ref={bottomRef} />
    </div>
  );
}
