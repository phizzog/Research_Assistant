'use client';

import { useState, useRef, useEffect } from 'react';
import { FiSend } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';
import FileUpload from '@/components/FileUpload';
import { ChatHistory, ChatMessage } from '@/lib/gemini';

interface ChatProps {
  onSendMessage: (message: string, file?: File) => Promise<void>;
  messages: ChatHistory;
  isLoading: boolean;
}

// Define types for markdown components
type ComponentProps = {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  [key: string]: any;
};

export default function Chat({ onSendMessage, messages, isLoading }: ChatProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await onSendMessage(message);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-indigo-50 to-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              {message.role === 'user' ? (
                <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{message.content}</p>
              ) : (
                <div className="markdown-content text-[15px] leading-relaxed text-black">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw, rehypeHighlight]}
                    components={{
                      // Style headings
                      h1: ({ node, ...props }: ComponentProps) => (
                        <h1 className="text-indigo-900 text-xl font-bold mt-4 mb-2" {...props} />
                      ),
                      h2: ({ node, ...props }: ComponentProps) => (
                        <h2 className="text-indigo-800 text-lg font-bold mt-3 mb-2" {...props} />
                      ),
                      h3: ({ node, ...props }: ComponentProps) => (
                        <h3 className="text-indigo-700 text-base font-bold mt-2 mb-1" {...props} />
                      ),
                      p: ({ node, ...props }: ComponentProps) => (
                        <p className="text-gray-800 mb-2" {...props} />
                      ),
                      // Style lists
                      ul: ({ node, ...props }: ComponentProps) => (
                        <ul className="text-gray-800 list-disc pl-5 mb-2" {...props} />
                      ),
                      ol: ({ node, ...props }: ComponentProps) => (
                        <ol className="text-gray-800 list-decimal pl-5 mb-2" {...props} />
                      ),
                      li: ({ node, ...props }: ComponentProps) => (
                        <li className="text-gray-800 mb-1" {...props} />
                      ),
                      // Style emphasis
                      strong: ({ node, ...props }: ComponentProps) => (
                        <strong className="text-gray-900 font-bold" {...props} />
                      ),
                      em: ({ node, ...props }: ComponentProps) => (
                        <em className="text-gray-800 italic" {...props} />
                      ),
                      // Style code blocks
                      code({ node, inline, className, children, ...props }: ComponentProps) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <div className="my-2 overflow-x-auto">
                            <pre className="p-2 rounded bg-gray-100 text-gray-800 overflow-x-auto">
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                          </div>
                        ) : (
                          <code className="bg-gray-100 text-gray-800 px-1 rounded" {...props}>
                            {children}
                          </code>
                        );
                      },
                      // Style links
                      a: ({ node, ...props }: ComponentProps) => (
                        <a 
                          className="text-indigo-600 font-medium hover:underline" 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          {...props}
                        />
                      ),
                      // Style tables
                      table: ({ node, ...props }: ComponentProps) => (
                        <div className="overflow-x-auto my-4">
                          <table className="min-w-full border border-gray-300 text-gray-800" {...props} />
                        </div>
                      ),
                      thead: ({ node, ...props }: ComponentProps) => (
                        <thead className="bg-gray-100" {...props} />
                      ),
                      th: ({ node, ...props }: ComponentProps) => (
                        <th className="border border-gray-300 px-4 py-2 text-left" {...props} />
                      ),
                      td: ({ node, ...props }: ComponentProps) => (
                        <td className="border border-gray-300 px-4 py-2" {...props} />
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-gray-200">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800 font-medium placeholder:text-gray-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <FiSend className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
