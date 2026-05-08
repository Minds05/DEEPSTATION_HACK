import React, { useState } from 'react';
import { X, Send, Sparkles, BookOpen } from 'lucide-react';
import axios from 'axios';

const AgentFAB = ({ userId, books = [] }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([
    { role: 'agent', content: "Hello! Paste your syllabus or JD and I'll find the best books." }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setQuery("");
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8001/agent/query', {
        user_query: userMsg,
        user_id: userId
      });
      
      const { message, book_ids } = response.data;
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: message, 
        books: book_ids 
      }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'agent', content: "Error connecting to Agent backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-8 right-8 bg-emerald-500 hover:bg-emerald-400 text-slate-900 p-4 rounded-full shadow-lg shadow-emerald-500/30 transition-all duration-300 hover:scale-110 z-40 cursor-pointer ${isOpen ? 'scale-0' : 'scale-100'}`}
      >
        <Sparkles size={28} className="animate-pulse" />
      </button>

      <div className={`fixed bottom-8 right-8 w-[400px] h-[600px] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col z-50 transition-all duration-500 origin-bottom-right ${isOpen ? 'scale-100 opacity-100' : 'scale-0 opacity-0 pointer-events-none'}`}>
        
        <div className="bg-slate-800 p-4 rounded-t-2xl border-b border-slate-700 flex justify-between items-center">
          <div className="flex items-center gap-2 text-emerald-400">
            <Sparkles size={20} />
            <h3 className="font-bold text-white">Syllabus-to-Shelf Agent</h3>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white transition-colors cursor-pointer">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-3 ${msg.role === 'user' ? 'bg-emerald-500 text-slate-900 rounded-br-sm font-medium' : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-sm'}`}>
                {msg.content}
                {msg.books && (
                  <div className="mt-3 flex flex-col gap-2">
                    {msg.books.map(id => {
                      const book = books.find(b => b.isbn === id || b.id === id);
                      const title = book ? book.title : `ISBN: ${id}`;
                      return (
                        <button 
                          key={id} 
                          onClick={() => {
                            const el = document.getElementById(`book-${id}`);
                            if (el) {
                              // Close chat overlay on mobile or keep open if preferred
                              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                              el.classList.add('ring-2', 'ring-emerald-500', 'scale-105');
                              setTimeout(() => el.classList.remove('ring-2', 'ring-emerald-500', 'scale-105'), 2000);
                            }
                          }}
                          className="text-left flex items-center gap-2 bg-slate-900/50 hover:bg-slate-900 text-emerald-400 text-sm px-3 py-2 rounded-lg border border-emerald-500/30 hover:border-emerald-500 transition-all cursor-pointer shadow-sm"
                        >
                          <BookOpen size={14} className="flex-shrink-0" />
                          <span className="font-semibold truncate">{title}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 border border-slate-700 rounded-2xl p-4 rounded-bl-sm flex gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="p-4 bg-slate-800 rounded-b-2xl border-t border-slate-700">
          <div className="relative">
            <textarea 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Paste syllabus or JD here..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 pr-12 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 resize-none h-24"
              onKeyDown={(e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <button 
              type="submit" 
              disabled={isLoading || !query.trim()}
              className="absolute bottom-3 right-3 text-emerald-400 hover:text-emerald-300 disabled:text-slate-600 transition-colors cursor-pointer"
            >
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default AgentFAB;
