/**
 * ChatPanel Component
 * Conversational AI interface for housing queries.
 * Displays messages and handles input.
 */
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Home, TrendingUp, AlertCircle, Sparkles } from 'lucide-react';
import { useHousing } from '../store/housingStore';

const QUICK_QUERIES = [
  '🏠 PG near Whitefield under ₹8000',
  '🏢 1BHK in Koramangala under ₹20000',
  '🛏️ Furnished flat in HSR Layout',
  '🌙 Budget PG with food near Electronic City',
];

export default function ChatPanel() {
  const { messages, isLoading, sendMessage } = useHousing();
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (query) => {
    const q = (query || input).trim();
    if (!q || isLoading) return;
    setInput('');
    await sendMessage(q);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/40 backdrop-blur-sm rounded-2xl border border-slate-700/50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-700/50 bg-slate-800/40">
        <div className="w-8 h-8 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
          <Bot className="w-4 h-4 text-violet-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Housing AI</p>
          <p className="text-[10px] text-slate-400">Powered by Gemini 2.5 Flash</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] text-slate-400">Live</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-6 text-center py-8">
            <div className="w-16 h-16 rounded-2xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-violet-400" />
            </div>
            <div>
              <p className="text-white font-semibold text-lg mb-1">Find Your Perfect Home</p>
              <p className="text-slate-400 text-sm max-w-xs">Describe what you're looking for and our AI will find the best matches.</p>
            </div>
            <div className="grid grid-cols-1 gap-2 w-full">
              {QUICK_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-left text-xs text-slate-300 bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/50 hover:border-violet-500/30 px-3 py-2.5 rounded-xl transition-all duration-200 hover:text-white"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-800/30">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Describe your housing needs..."
            disabled={isLoading}
            className="flex-1 bg-slate-800/80 border border-slate-600/50 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl focus:outline-none focus:border-violet-500/70 focus:ring-1 focus:ring-violet-500/20 transition-all duration-200 disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:opacity-50 text-white rounded-xl flex items-center justify-center transition-all duration-200 hover:shadow-lg hover:shadow-violet-500/25 active:scale-95"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] flex items-start gap-2">
          <div className="bg-violet-600/80 text-white text-sm px-4 py-2.5 rounded-2xl rounded-tr-sm shadow-lg">
            {message.content}
          </div>
          <div className="w-7 h-7 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0 mt-0.5">
            <User className="w-3.5 h-3.5 text-slate-300" />
          </div>
        </div>
      </div>
    );
  }

  // Error message
  if (message.error) {
    return (
      <div className="flex items-start gap-2">
        <div className="w-7 h-7 rounded-full bg-red-900/40 border border-red-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 text-red-400" />
        </div>
        <div className="bg-red-900/20 border border-red-500/20 text-red-300 text-xs px-3 py-2 rounded-2xl rounded-tl-sm">
          {message.error}
        </div>
      </div>
    );
  }

  // AI response
  const meta = message.meta || {};
  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-violet-900/40 border border-violet-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-violet-400" />
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 text-sm px-4 py-3 rounded-2xl rounded-tl-sm space-y-1.5 max-w-[85%]">
        {meta.total !== undefined && (
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
            <Home className="w-3 h-3" />
            Found {meta.total} listing{meta.total !== 1 ? 's' : ''}
            {meta.recommendations > 0 && (
              <span className="text-violet-400 flex items-center gap-1">
                · <TrendingUp className="w-3 h-3" /> {meta.recommendations} ranked
              </span>
            )}
          </div>
        )}
        <p className="text-slate-300 text-xs">
          {meta.total > 0
            ? 'Results updated. Check the panels on the right for details.'
            : message.task === 'schedule'
            ? 'Visit scheduling processed. Check your schedules.'
            : 'No listings found matching your criteria. Try adjusting your filters.'}
        </p>
        {meta.agent_trace?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {meta.agent_trace.map((t, i) => (
              <span key={i} className="text-[9px] text-slate-500 bg-slate-700/30 px-1.5 py-0.5 rounded">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-violet-900/40 border border-violet-500/30 flex items-center justify-center flex-shrink-0">
        <Bot className="w-3.5 h-3.5 text-violet-400" />
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 px-4 py-3 rounded-2xl rounded-tl-sm">
        <div className="flex gap-1.5 items-center">
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
