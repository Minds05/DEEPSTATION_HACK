/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart3, 
  MapPin, 
  Briefcase, 
  GraduationCap, 
  Library, 
  Plus, 
  Send, 
  Shield, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  LayoutDashboard,
  Bell,
  Calendar,
  Search,
  ChevronRight,
  Terminal,
  Cpu,
  Building2,
  Car,
  CircleDollarSign,
  Heart,
  X,
  MessageSquare,
  History as HistoryIcon,
  Trash2,
  User,
  FileText,
  Upload,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { analyzeCommunityIssue, libraryQA, processResume } from './services/geminiService';
import { AgentType, ActionLog, AGENT_DESCRIPTIONS, ChatSession, UserProfile } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'assistant' | 'agents' | 'library' | 'admin'>('assistant');
  const [viewMode, setViewMode] = useState<'user' | 'admin'>('user');
  const [inputText, setInputText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState('');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isProcessingResume, setIsProcessingResume] = useState(false);
  
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('civic_sessions');
    if (saved) return JSON.parse(saved);
    const defaultSession: ChatSession = {
      id: 'default',
      title: 'New Conversation',
      logs: [],
      history: [],
      sessionAgent: null,
      createdAt: Date.now()
    };
    return [defaultSession];
  });
  
  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    return localStorage.getItem('civic_active_session_id') || 'default';
  });

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const actionLogs = activeSession.logs;
  const chatHistory = activeSession.history;
  const sessionAgent = activeSession.sessionAgent;

  const [activeAgent, setActiveAgent] = useState<AgentType>('Orchestrator');
  
  const [libraryQuestion, setLibraryQuestion] = useState('');
  const [libraryAnswer, setLibraryAnswer] = useState('“The role of automation in community building is not to replace human interaction, but to remove the logistical friction that prevents it. By automating the allocation of resources—whether it be books, grants, or traffic routes—we free the community to focus on higher-level social cohesion.”');
  const [isLibraryLoading, setIsLibraryLoading] = useState(false);

  const handleLibraryQA = async () => {
    if (!libraryQuestion.trim()) return;
    setIsLibraryLoading(true);
    const context = "CivicNexus Library Archives. Contains information on urban planning, civic contracts, and autonomous community systems.";
    const answer = await libraryQA(context, libraryQuestion);
    setLibraryAnswer(answer || "Search failed.");
    setLibraryQuestion('');
    setIsLibraryLoading(false);
    addLog('AssetAgent', 'Research Inquiry', `Question: ${libraryQuestion}`);
  };

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [actionLogs]);

  useEffect(() => {
    localStorage.setItem('civic_sessions', JSON.stringify(sessions));
    localStorage.setItem('civic_active_session_id', activeSessionId);
  }, [sessions, activeSessionId]);

  const updateActiveSession = (updates: Partial<ChatSession>) => {
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, ...updates } : s));
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Math.random().toString(36).substr(2, 9),
      title: `Conversation ${sessions.length + 1}`,
      logs: [],
      history: [],
      sessionAgent: null,
      createdAt: Date.now()
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const deleteSession = (id: string) => {
    if (sessions.length <= 1) {
      // Don't delete the last session, just clear it
      setSessions([{
        id: 'default',
        title: 'New Conversation',
        logs: [],
        history: [],
        sessionAgent: null,
        createdAt: Date.now()
      }]);
      setActiveSessionId('default');
      return;
    }
    const newSessions = sessions.filter(s => s.id !== id);
    setSessions(newSessions);
    if (activeSessionId === id) {
      setActiveSessionId(newSessions[0].id);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessingResume(true);
    const reader = new FileReader();

    const isTextFile = file.type === 'text/plain' || file.name.endsWith('.txt');

    reader.onload = async (event) => {
      let profile;
      if (isTextFile) {
        const text = event.target?.result as string;
        profile = await processResume(text);
      } else {
        const dataUrl = event.target?.result as string;
        const base64Data = dataUrl.split(',')[1];
        profile = await processResume({ data: base64Data, mimeType: file.type || 'application/pdf' });
      }

      if (profile) {
        updateActiveSession({ userProfile: profile });
        addLog('EduAgent', 'Resume Digestion Complete', `Extracted profile for ${profile.name}. System calibrated for automated applications.`);
      }
      setIsProcessingResume(false);
    };

    if (isTextFile) {
      reader.readAsText(file);
    } else {
      reader.readAsDataURL(file);
    }
  };

  const addLog = (agent: AgentType, action: string, details: string, status: 'pending' | 'completed' | 'failed' = 'completed') => {
    const newLog: ActionLog = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      agent,
      action,
      details,
      status
    };
    
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, logs: [...s.logs, newLog] } : s));
  };

  const handleAction = async () => {
    if (!inputText.trim() || isAnalyzing) return;

    const issue = inputText;
    setInputText('');
    setIsAnalyzing(true);
    setAnalysisStatus('Connecting to Master Orchestrator...');
    
    try {
      if (viewMode === 'admin') {
        addLog('Orchestrator', 'Analyzing Problem Vector', `Classifying issue and identifying target agents...`, 'pending');
      } else {
        addLog('CivicAssistant', 'Analyzing', `Processing your request regarding: "${issue}"...`, 'pending');
      }

      setAnalysisStatus('Accessing City Database...');
      const result = await analyzeCommunityIssue(issue, chatHistory, sessionAgent, activeSession.userProfile || null);
      
      setAnalysisStatus('Synchronizing Agent Sub-routines...');

      if (result && result.steps && result.steps.length > 0) {
        // Maintain agent continuity
        const primaryAgent = result.steps[0].agent as AgentType;
        let newSessionAgent = sessionAgent;
        if (!sessionAgent) {
          newSessionAgent = primaryAgent;
        }
        
        const newHistory = [...chatHistory, { role: 'user' as const, content: issue }];
        
        if (viewMode === 'admin') {
          addLog('Orchestrator', 'Assignment Finalized', `Issue classified. Task assigned to: ${result.steps.map((s: any) => s.agent).join(', ')}`);
        }
        
        // Execute steps with faster perceived response
        result.steps.forEach((step: any, index: number) => {
          setTimeout(() => {
            // Re-fetch current logs within interval
            setSessions(currentSessions => {
              const session = currentSessions.find(s => s.id === activeSessionId);
              if (!session) return currentSessions;
              
              const stepLog: ActionLog = {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toLocaleTimeString(),
                agent: (viewMode === 'admin' ? step.agent : 'CivicAssistant') as AgentType,
                action: step.task,
                details: step.details,
                status: 'completed'
              };

              return currentSessions.map(s => s.id === activeSessionId 
                ? { ...s, logs: [...s.logs, stepLog] } 
                : s
              );
            });
          }, (index + 0.2) * 500);
        });

        setTimeout(() => {
          // Final resolution log and history update
          setSessions(currentSessions => {
            const session = currentSessions.find(s => s.id === activeSessionId);
            if (!session) return currentSessions;

            const finalLog: ActionLog = {
               id: Math.random().toString(36).substr(2, 9),
               timestamp: new Date().toLocaleTimeString(),
               agent: (viewMode === 'admin' ? 'Orchestrator' : 'CivicAssistant') as AgentType,
               action: 'Resolution Complete',
               details: result.estimatedImpact,
               status: 'completed'
            };

            const updatedHistory = [...newHistory, { role: 'assistant' as const, content: result.estimatedImpact }];
            
            // Auto-generate title if it's the first message
            const newTitle = session.logs.length <= 1 ? issue.substring(0, 30) + (issue.length > 30 ? '...' : '') : session.title;

            return currentSessions.map(s => s.id === activeSessionId 
              ? { ...s, logs: [...s.logs, finalLog], history: updatedHistory, sessionAgent: newSessionAgent, title: newTitle } 
              : s
            );
          });
        }, (result.steps.length + 0.5) * 600);

      } else {
        const errorAgent = viewMode === 'admin' ? 'Orchestrator' : 'CivicAssistant';
        addLog(errorAgent, 'Analysis Failed', 'The intelligence nodes returned an empty vector. Re-indexing...', 'failed');
      }
    } catch (error) {
      console.error("Action execution failed:", error);
      const errorAgent = viewMode === 'admin' ? 'Orchestrator' : 'CivicAssistant';
      addLog(errorAgent, 'System Error', 'Network synchronization failed. Please retry.', 'failed');
    } finally {
      setIsAnalyzing(false);
      setAnalysisStatus('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-slate-950/80 backdrop-blur-md border-b border-slate-800 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <span className="text-white font-bold text-xl font-mono">CN</span>
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight text-white uppercase">CivicNexus <span className="text-indigo-400 font-normal lowercase">Master Orchestrator</span></h1>
            <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest leading-none mt-0.5">v4.2.0-STABLE // SYSTEM_READY</p>
          </div>
        </div>

        <div className="flex gap-4">
          <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1">
             <button 
               onClick={() => setViewMode('user')}
               className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'user' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-slate-300'}`}
             >
               User View
             </button>
             <button 
               onClick={() => setViewMode('admin')}
               className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'admin' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-slate-300'}`}
             >
               Admin Hub
             </button>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">Active Nodes: 1,240</span>
          </div>
          <div className="bg-indigo-500/10 border border-indigo-500/30 px-3 py-1.5 rounded-full hidden md:block">
            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 font-mono italic">Autonomous Mode: ON</span>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="pt-16 flex min-h-screen">
        {/* Sidebar */}
        <aside className="w-64 fixed left-0 top-16 bottom-0 bg-slate-950 border-r border-slate-800 p-4 space-y-6">
          <nav className="space-y-1">
            <SidebarItem 
              icon={<LayoutDashboard size={18} />} 
              label="Dashboard" 
              active={activeTab === 'dashboard'} 
              onClick={() => setActiveTab('dashboard')} 
            />
            <SidebarItem 
              icon={<MessageSquare size={18} />} 
              label="Civic Assistant" 
              active={activeTab === 'assistant'} 
              onClick={() => setActiveTab('assistant')} 
            />
            <SidebarItem 
              icon={<Cpu size={18} />} 
              label="Agent Clusters" 
              active={activeTab === 'agents'} 
              onClick={() => setActiveTab('agents')} 
            />
            <SidebarItem 
              icon={<Library size={18} />} 
              label="Library Automation" 
              active={activeTab === 'library'} 
              onClick={() => setActiveTab('library')} 
            />
            <SidebarItem 
              icon={<Shield size={18} />} 
              label="Governance & Policy" 
              active={activeTab === 'admin'} 
              onClick={() => setActiveTab('admin')} 
            />
          </nav>

          <div className="pt-6 border-t border-slate-800">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-3 mb-3 font-mono">Live Nodes</p>
            <div className="space-y-2">
              <AgentStatus 
                name="FinAgent" 
                active={activeAgent === 'FinAgent'} 
                onClick={() => { setActiveTab('agents'); setActiveAgent('FinAgent'); }}
                icon={<CircleDollarSign size={14} className="text-emerald-500" />}
              />
              <AgentStatus 
                name="MobilityAgent" 
                active={activeAgent === 'MobilityAgent'} 
                onClick={() => { setActiveTab('agents'); setActiveAgent('MobilityAgent'); }}
                icon={<Car size={14} className="text-blue-500" />}
              />
              <AgentStatus 
                name="EduAgent" 
                active={activeAgent === 'EduAgent'} 
                onClick={() => { setActiveTab('agents'); setActiveAgent('EduAgent'); }}
                icon={<GraduationCap size={14} className="text-purple-500" />}
              />
              <AgentStatus 
                name="AssetAgent" 
                active={activeAgent === 'AssetAgent'} 
                onClick={() => { setActiveTab('agents'); setActiveAgent('AssetAgent'); }}
                icon={<Library size={14} className="text-amber-500" />}
              />
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="ml-64 flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            <AnimatePresence mode="wait">
              {activeTab === 'dashboard' && viewMode === 'admin' && (
                <motion.div 
                  key="admin-dashboard"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  <section className="bg-slate-900/50 rounded-2xl p-8 border border-slate-800 shadow-xl overflow-hidden relative">
                    <div className="relative z-10">
                      <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">How can CivicNexus assist you today?</h2>
                      <p className="text-slate-400 mb-8 max-w-xl font-medium">State a community problem, and our autonomous orchestrator will deconstruct it into actionable steps for the relevant agent clusters.</p>
                      
                      <div className="flex gap-3 bg-slate-950 p-4 rounded-2xl border border-slate-800 shadow-inner">
                        <div className="w-10 h-10 bg-indigo-500/10 border border-indigo-500/30 rounded-full flex items-center justify-center text-indigo-400 flex-shrink-0">
                          <Terminal size={20} />
                        </div>
                        <input 
                          type="text" 
                          value={inputText}
                          onChange={(e) => setInputText(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleAction()}
                          placeholder="Ex: Traffic is blocked on Main St, we need alternate routes..."
                          className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-slate-600 font-medium"
                        />
                        <button 
                          onClick={handleAction}
                          disabled={isAnalyzing || !inputText.trim()}
                          className="px-6 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:shadow-none flex items-center gap-2 uppercase tracking-widest text-xs"
                        >
                          {isAnalyzing ? (
                            <Clock className="w-4 h-4 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                          Execute
                        </button>
                      </div>

                      <div className="mt-4 flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                        <QuickAction 
                          label="Traffic Outage" 
                          onClick={() => setInputText("Severe congestion at 5th and Broadway, buses are delayed.")}
                        />
                        <QuickAction 
                          label="Small Business Grant" 
                          onClick={() => setInputText("Looking for government grants for a green energy startup.")}
                        />
                        <QuickAction 
                          label="Housing Search" 
                          onClick={() => setInputText("Identify local housing assistance programs for families.")}
                        />
                      </div>
                    </div>
                    {/* Background decoration */}
                    <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-[100px] opacity-40"></div>
                  </section>

                  <div className="grid grid-cols-12 gap-6">
                    {/* Chat Interface */}
                    <section className="col-span-8 bg-slate-900/50 rounded-2xl border border-slate-800 shadow-xl flex flex-col h-[700px] overflow-hidden backdrop-blur-sm">
                      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20">
                            <Cpu className="text-white w-4 h-4" />
                          </div>
                          <div>
                            <h3 className="font-bold text-xs text-white uppercase tracking-widest">Master Orchestrator</h3>
                            <p className="text-[9px] text-emerald-500 font-mono">STATUS: INTERPRETING_VECTORS</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                           <div className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-[9px] font-mono text-slate-500">
                             SESSION_ID: {Math.random().toString(36).substring(7).toUpperCase()}
                           </div>
                        </div>
                      </div>
                      
                      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                        {actionLogs.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center text-slate-700 space-y-4 opacity-50">
                            <div className="w-20 h-20 bg-slate-950 rounded-full flex items-center justify-center border border-slate-800 animate-pulse">
                              <Shield size={40} className="text-indigo-500" />
                            </div>
                            <div className="text-center group">
                              <p className="uppercase tracking-[0.3em] font-bold text-sm text-indigo-400">CivicNexus Intelligence Hub</p>
                              <p className="text-[10px] mt-2 font-mono">System initialized. Awaiting community problem vector...</p>
                            </div>
                          </div>
                        ) : (
                          actionLogs.map((log) => (
                            <motion.div 
                              key={log.id} 
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`flex ${log.agent === 'Orchestrator' ? 'justify-start' : 'justify-start ml-8'}`}
                            >
                              <div className={`max-w-[85%] rounded-2xl p-4 border relative ${
                                log.agent === 'Orchestrator' 
                                  ? 'bg-indigo-600/10 border-indigo-500/30' 
                                  : log.agent === 'FinAgent' ? 'bg-emerald-500/10 border-emerald-500/30'
                                  : log.agent === 'MobilityAgent' ? 'bg-blue-500/10 border-blue-500/30'
                                  : log.agent === 'EduAgent' ? 'bg-purple-500/10 border-purple-500/30'
                                  : 'bg-amber-500/10 border-amber-500/30'
                              }`}>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-widest font-mono ${
                                    log.agent === 'Orchestrator' ? 'bg-indigo-600 text-white' : 
                                    log.agent === 'FinAgent' ? 'bg-emerald-500 text-slate-950' :
                                    log.agent === 'MobilityAgent' ? 'bg-blue-500 text-slate-950' :
                                    log.agent === 'EduAgent' ? 'bg-purple-500 text-white' :
                                    'bg-amber-500 text-slate-950'
                                  }`}>
                                    {log.agent}
                                  </span>
                                  <span className="text-slate-500 text-[9px] font-mono">{log.timestamp}</span>
                                </div>
                                <h4 className="font-bold text-white text-sm mb-1">{log.action}</h4>
                                <p className="text-slate-300 text-sm leading-relaxed">{log.details}</p>
                                
                                {log.status === 'pending' && (
                                  <div className="absolute -right-2 -top-2">
                                    <div className="flex space-x-1">
                                      <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce"></div>
                                      <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                      <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          ))
                        )}
                      </div>

                      {/* Floating Prompt Bar */}
                      <div className="p-6 bg-slate-950/60 border-t border-slate-800">
                        <div className="flex gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-2 shadow-2xl relative">
                          <div className="w-10 h-10 bg-slate-950 rounded-xl flex items-center justify-center text-indigo-400 shrink-0 border border-slate-800">
                            <Terminal size={20} />
                          </div>
                          <input 
                            type="text" 
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAction()}
                            placeholder="Input community issue vector (e.g., Traffic congestion on Route 9)..."
                            className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-slate-600 font-medium text-sm px-2"
                          />
                          <button 
                            onClick={handleAction}
                            disabled={isAnalyzing || !inputText.trim()}
                            className="px-6 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 flex items-center gap-2 uppercase tracking-widest text-[10px]"
                          >
                            {isAnalyzing ? <Clock className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                            Execute
                          </button>
                        </div>
                        <div className="mt-4 flex gap-4 overflow-x-auto pb-2 no-scrollbar">
                          <QuickAction label="Traffic Alert" onClick={() => setInputText("Severe gridlock at central plaza, emergency vehicles delayed.")} />
                          <QuickAction label="Housing Match" onClick={() => setInputText("Find emergency housing for family of 4 displaced by warehouse fire.")} />
                          <QuickAction label="SME Grant" onClick={() => setInputText("Draft eligibility report for sustainable textile startup applying for Q3 grant.")} />
                        </div>
                      </div>
                    </section>

                    {/* Stats/Status */}
                    <div className="col-span-4 space-y-6">
                       <section className="bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
                          <h3 className="font-bold text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-6">Metrics // Node Status</h3>
                          <div className="space-y-6">
                            <StatBar label="Mobility Flow" value={87} color="bg-blue-500" />
                            <StatBar label="Grant Pipeline" value={42} color="bg-indigo-500" />
                            <StatBar label="Housing Reach" value={64} color="bg-emerald-500" />
                            <StatBar label="Asset Allocation" value={91} color="bg-amber-500" />
                          </div>
                       </section>

                       <section className="bg-indigo-600/10 border border-indigo-500/30 rounded-2xl p-6 text-white shadow-xl shadow-indigo-500/5 relative overflow-hidden">
                          <div className="relative z-10">
                            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                               <Heart size={20} className="text-indigo-400" />
                               Impact Matrix
                            </h3>
                            <p className="text-slate-400 text-[10px] uppercase font-bold tracking-widest mb-4">Last 24h operational success.</p>
                            <div className="space-y-3">
                               <div className="flex items-center gap-3 bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                                  <Building2 size={16} className="text-emerald-400" />
                                  <div className="text-xs">
                                     <p className="font-bold">Housing Match: Unity Heights</p>
                                     <p className="text-slate-500 text-[10px]">Low-income family synchronized.</p>
                                  </div>
                               </div>
                               <div className="flex items-center gap-3 bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                                  <Briefcase size={16} className="text-indigo-400" />
                                  <div className="text-xs">
                                     <p className="font-bold">Grant Approved: $25k</p>
                                     <p className="text-slate-500 text-[10px]">GreenSeed project funded.</p>
                                  </div>
                               </div>
                            </div>
                          </div>
                       </section>
                    </div>
                  </div>
                </motion.div>
              )}
              {activeTab === 'dashboard' && viewMode === 'user' && (
                <motion.div 
                  key="user-dashboard"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  <div className="flex flex-col gap-6">
                    <div className="space-y-6">
                        <section className="bg-slate-900/50 rounded-2xl p-8 border border-slate-800 shadow-xl relative overflow-hidden">
                          <div className="relative z-10">
                            <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">Welcome back, neighbor.</h2>
                            <p className="text-slate-400 mb-8 max-w-lg">CivicNexus connects you directly to city services. Our AI Orchestrator manages the complexities of urban life so you don't have to.</p>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                               <div className="flex gap-3 items-start">
                                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
                                     <Activity size={16} className="text-indigo-400" />
                                  </div>
                                  <div>
                                     <p className="text-xs font-bold text-white uppercase tracking-tight">Real-time Coordination</p>
                                     <p className="text-[10px] text-slate-500 mt-0.5">Automated traffic routing and transit synchronization.</p>
                                  </div>
                               </div>
                               <div className="flex gap-3 items-start">
                                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0">
                                     <CircleDollarSign size={16} className="text-emerald-400" />
                                  </div>
                                  <div>
                                     <p className="text-xs font-bold text-white uppercase tracking-tight">Financial Inclusion</p>
                                     <p className="text-[10px] text-slate-500 mt-0.5">Direct matching to grants, tenders, and job opportunities.</p>
                                  </div>
                               </div>
                            </div>
                            
                            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                               <UserServiceCard 
                                 icon={<Car className="text-blue-400" />}
                                 title="Mobility"
                                 desc="Traffic & transit logs."
                                 onClick={() => { setActiveTab('assistant'); setInputText("I want to report a traffic issue or see transit status."); }}
                               />
                               <UserServiceCard 
                                 icon={<CircleDollarSign className="text-emerald-400" />}
                                 title="Economic"
                                 desc="Grants & funding."
                                 onClick={() => { setActiveTab('assistant'); setInputText("Tell me about available small business grants."); }}
                               />
                               <UserServiceCard 
                                 icon={<GraduationCap className="text-purple-400" />}
                                 title="Education"
                                 desc="Jobs & upskilling."
                                 onClick={() => { setActiveTab('assistant'); setInputText("I'm looking for a job."); }}
                               />
                               <UserServiceCard 
                                 icon={<Library className="text-amber-400" />}
                                 title="Resources"
                                 desc="Library assets."
                                 onClick={() => { setActiveTab('assistant'); setInputText("How do I book a library room?"); }}
                               />
                            </div>
                          </div>
                          <div className="absolute top-0 right-0 p-8 opacity-10">
                             <Building2 size={120} />
                          </div>
                        </section>

                        <section className="bg-slate-900/50 rounded-2xl p-6 border border-slate-800">
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h3 className="font-bold text-sm text-white">Community Opportunity Board</h3>
                                <div className="flex gap-2">
                                   {['All', 'Jobs', 'Funding', 'Transit'].map(f => (
                                     <button key={f} className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-[9px] font-bold text-slate-500 hover:text-indigo-400 uppercase tracking-widest transition-colors">{f}</button>
                                   ))}
                                </div>
                            </div>

                            <div className="bg-slate-950/30 p-5 rounded-2xl border border-slate-800/50">
                               <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-4">Advanced Job Filter (EduAgent)</p>
                               <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                  <input 
                                    type="text" 
                                    placeholder="Title (e.g. Engineer)" 
                                    className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl text-xs text-white placeholder:text-slate-600 outline-none focus:border-indigo-500/50"
                                    id="job-title-filter"
                                  />
                                  <input 
                                    type="text" 
                                    placeholder="Industry" 
                                    className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl text-xs text-white placeholder:text-slate-600 outline-none focus:border-indigo-500/50"
                                    id="job-industry-filter"
                                  />
                                  <div className="flex gap-2">
                                    <input 
                                      type="text" 
                                      placeholder="Location" 
                                      className="flex-1 bg-slate-900 border border-slate-800 p-2.5 rounded-xl text-xs text-white placeholder:text-slate-600 outline-none focus:border-indigo-500/50"
                                      id="job-location-filter"
                                    />
                                    <button 
                                      onClick={() => {
                                        const title = (document.getElementById('job-title-filter') as HTMLInputElement)?.value;
                                        const industry = (document.getElementById('job-industry-filter') as HTMLInputElement)?.value;
                                        const location = (document.getElementById('job-location-filter') as HTMLInputElement)?.value;
                                        setActiveTab('assistant');
                                        setInputText(`Search for ${title || 'any'} jobs in ${industry || 'any industry'} at ${location || 'any location'}. Show eligible listings.`);
                                      }}
                                      className="bg-indigo-600 text-white p-2.5 rounded-xl hover:bg-indigo-700 transition-colors"
                                    >
                                      <Search size={16} />
                                    </button>
                                  </div>
                               </div>
                            </div>
                            
                            <div className="space-y-3">
                               <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 flex items-center justify-between group hover:border-slate-700 transition-all">
                                  <div className="flex items-center gap-4">
                                     <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 shrink-0">
                                        <Car size={18} />
                                     </div>
                                     <div>
                                        <p className="text-xs font-bold text-slate-200">Express Corridor Optimization</p>
                                        <p className="text-[10px] text-slate-500">Transit times reduced by 12% in sector 4.</p>
                                     </div>
                                  </div>
                                  <Activity size={14} className="text-slate-700 font-mono" />
                               </div>
                               
                               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div className="bg-emerald-500/5 p-4 rounded-xl border border-emerald-500/20 group hover:border-emerald-500/40 transition-all">
                                     <div className="flex justify-between items-start mb-3">
                                        <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                                           <CircleDollarSign size={16} />
                                        </div>
                                        <div className="px-2 py-0.5 bg-emerald-500/20 rounded text-[8px] font-bold text-emerald-400 uppercase italic">Active Tender</div>
                                     </div>
                                     <h4 className="text-xs font-bold text-white mb-1">Municipal Solar Grid Phase 2</h4>
                                     <div className="space-y-1.5 mt-3">
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Agency</span>
                                          <span className="text-slate-300">Dept. of Energy</span>
                                        </div>
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Award</span>
                                          <span className="text-emerald-400 font-bold">$1.2M - $5.0M</span>
                                        </div>
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Deadline</span>
                                          <span className="text-amber-500">June 15, 2026</span>
                                        </div>
                                     </div>
                                     <button 
                                       onClick={() => { setActiveTab('assistant'); setInputText("How do I apply for the Municipal Solar Grid Phase 2 tender?"); }}
                                       className="w-full mt-4 py-2 bg-emerald-600/20 border border-emerald-500/30 rounded-lg text-[9px] font-bold text-emerald-400 uppercase tracking-widest hover:bg-emerald-600 hover:text-white transition-all"
                                     >
                                        Inquire via FinAgent
                                     </button>
                                  </div>

                                  <div className="bg-indigo-500/5 p-4 rounded-xl border border-indigo-500/20 group hover:border-indigo-500/40 transition-all">
                                     <div className="flex justify-between items-start mb-3">
                                        <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                                           <Briefcase size={16} />
                                        </div>
                                        <div className="px-2 py-0.5 bg-indigo-500/20 rounded text-[8px] font-bold text-indigo-400 uppercase italic">New Opportunity</div>
                                     </div>
                                     <h4 className="text-xs font-bold text-white mb-1">Civic Data Analyst</h4>
                                     <div className="space-y-1.5 mt-3">
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Dept</span>
                                          <span className="text-slate-300">Digital Governance</span>
                                        </div>
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Salary</span>
                                          <span className="text-indigo-400 font-bold">$85k - $110k</span>
                                        </div>
                                        <div className="flex justify-between text-[9px] uppercase tracking-wider">
                                          <span className="text-slate-500">Type</span>
                                          <span className="text-slate-300">Permanent // Remote</span>
                                        </div>
                                     </div>
                                     <button 
                                       onClick={() => { setActiveTab('assistant'); setInputText(`I want to apply for the Civic Data Analyst position using my resume. Please autofill the details for my review.`); }}
                                       className="w-full mt-4 py-2 bg-indigo-600/20 border border-indigo-500/30 rounded-lg text-[9px] font-bold text-indigo-400 uppercase tracking-widest hover:bg-indigo-600 hover:text-white transition-all"
                                     >
                                        Apply via EduAgent
                                     </button>
                                  </div>
                               </div>
                            </div>
                        </div>
                        </section>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'assistant' && (
                <motion.div 
                  key="assistant-tab"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="h-[calc(100vh-120px)] flex gap-4"
                >
                    {/* Session Sidebar */}
                    <div className="w-16 bg-slate-900 border border-slate-800 rounded-3xl p-3 flex flex-col gap-4 overflow-y-auto scrollbar-hide">
                         <button 
                           onClick={createNewSession}
                           className="w-full aspect-square bg-indigo-600 rounded-2xl flex items-center justify-center text-white hover:bg-indigo-700 transition-all shadow-lg active:scale-95"
                           title="Start New Chat"
                         >
                           <Plus size={20} />
                         </button>
                         <div className="w-full h-px bg-slate-800 my-1"></div>
                         <button 
                           onClick={() => setIsProfileOpen(!isProfileOpen)}
                           className={`w-full aspect-square rounded-2xl flex items-center justify-center transition-all ${isProfileOpen ? 'bg-indigo-600 text-white shadow-lg' : 'bg-slate-950 border border-slate-800 text-slate-600 hover:border-slate-700'}`}
                           title="My Profile & Resume"
                         >
                           <User size={20} />
                         </button>
                         <div className="w-full h-px bg-slate-800 my-1"></div>
                         <div className="flex-1 space-y-3">
                            {sessions.map(s => (
                              <div key={s.id} className="relative group">
                                <button 
                                  onClick={() => setActiveSessionId(s.id)}
                                  className={`w-full aspect-square rounded-2xl flex items-center justify-center text-[10px] font-bold border transition-all ${activeSessionId === s.id ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400' : 'bg-slate-950 border-slate-800 text-slate-700 hover:border-slate-700 hover:text-slate-400'}`}
                                  title={s.title}
                                >
                                  {s.title === 'New Conversation' ? <MessageSquare size={16} /> : s.title.substring(0, 2).toUpperCase()}
                                </button>
                                {sessions.length > 1 && (
                                  <button 
                                    onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                                    className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center scale-0 group-hover:scale-100 transition-transform opacity-0 group-hover:opacity-100 shadow-lg z-10"
                                  >
                                    <X size={10} />
                                  </button>
                                )}
                              </div>
                            ))}
                         </div>
                      </div>

                      {/* Profile Panel Overlay */}
                      <AnimatePresence>
                        {isProfileOpen && (
                          <motion.div 
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 300, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            className="flex flex-col bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl"
                          >
                             <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
                               <div className="flex items-center gap-2 text-indigo-400">
                                  <User size={16} />
                                  <h3 className="font-bold text-xs uppercase tracking-widest">My Civic Identity</h3>
                               </div>
                               <button onClick={() => setIsProfileOpen(false)} className="text-slate-500 hover:text-white">
                                  <X size={16} />
                               </button>
                             </div>
                             <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-hide">
                                {/* Resume Upload section */}
                                <div className="space-y-4">
                                   <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-center">
                                      <Upload size={24} className="mx-auto mb-2 text-indigo-500" />
                                      <p className="text-[10px] text-slate-400 mb-3 uppercase tracking-wider font-bold">Digest Resume (PDF/DOCX/TXT)</p>
                                      <label className="block w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-[10px] font-bold uppercase tracking-widest cursor-pointer transition-all active:scale-95">
                                         {isProcessingResume ? 'Analyzing...' : 'Choose File'}
                                         <input 
                                           type="file" 
                                           accept=".txt,.pdf,.doc,.docx"
                                           className="hidden" 
                                           onChange={handleResumeUpload}
                                           disabled={isProcessingResume}
                                         />
                                      </label>
                                   </div>

                                   {activeSession.userProfile ? (
                                     <div className="space-y-4">
                                        <div className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                                           <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                              <CheckCircle2 size={12} />
                                              <span className="text-[8px] font-bold uppercase tracking-widest">Global Calibration Active</span>
                                           </div>
                                           <p className="text-[10px] text-slate-300">Your profile is synchronized. Agents can now perform autonomous actions on your behalf.</p>
                                        </div>

                                        <div className="space-y-3">
                                           <div>
                                              <label className="text-[8px] uppercase tracking-widest text-slate-500 font-bold">Full Name</label>
                                              <p className="text-xs text-white bg-slate-950 border border-slate-800 p-2 rounded-lg mt-1">{activeSession.userProfile.name}</p>
                                           </div>
                                           <div>
                                              <label className="text-[8px] uppercase tracking-widest text-slate-500 font-bold">Email Address</label>
                                              <p className="text-xs text-white bg-slate-950 border border-slate-800 p-2 rounded-lg mt-1">{activeSession.userProfile.email}</p>
                                           </div>
                                           <div>
                                              <label className="text-[8px] uppercase tracking-widest text-slate-500 font-bold">Key Skills</label>
                                              <div className="flex flex-wrap gap-1.5 mt-1.5">
                                                 {activeSession.userProfile.skills.map(skill => (
                                                   <span key={skill} className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[9px] rounded-full">{skill}</span>
                                                 ))}
                                              </div>
                                           </div>
                                           <div>
                                              <label className="text-[8px] uppercase tracking-widest text-slate-500 font-bold">Education</label>
                                              <p className="text-[10px] text-slate-300 leading-relaxed mt-1 italic">"{activeSession.userProfile.education}"</p>
                                           </div>
                                        </div>

                                        <button 
                                          onClick={() => {
                                            setInputText("Suggest job openings that match my resume profile.");
                                            setIsProfileOpen(false);
                                          }}
                                          className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all shadow-lg active:scale-95 flex items-center justify-center gap-2"
                                        >
                                          <Search size={14} />
                                          Find Matching Jobs
                                        </button>
                                     </div>
                                   ) : (
                                     <div className="p-8 text-center border-2 border-dashed border-slate-800 rounded-3xl opacity-40">
                                        <Shield size={32} className="mx-auto mb-3 text-slate-700" />
                                        <p className="text-[10px] font-mono text-slate-500">AWAITING_CALIBRATION_FILE</p>
                                     </div>
                                   )}
                                </div>
                             </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Main Chat Area */}
                      <div className="flex-1 flex flex-col bg-slate-900 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden backdrop-blur-md">
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
                           <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                                 <Shield size={20} />
                              </div>
                              <div>
                                 <h3 className="font-bold text-sm text-white">{activeSession.title}</h3>
                                 <p className="text-[10px] text-emerald-500 font-mono">
                                   {sessionAgent ? `${sessionAgent} ENGAGED` : 'READY_TO_HELP'}
                                 </p>
                              </div>
                           </div>
                           <div className="flex items-center gap-2">
                              <button 
                                onClick={() => {
                                  updateActiveSession({ logs: [], history: [], sessionAgent: null, title: 'New Conversation' });
                                  addLog('CivicAssistant', 'Session Reset', 'Memory cleared for this thread.');
                                }}
                                className="p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-500 hover:text-red-400 transition-colors"
                                title="Reset Current Session"
                              >
                                 <Activity size={14} />
                              </button>
                           </div>
                        </div>

                        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                           {actionLogs.length === 0 ? (
                             <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center px-4 space-y-4">
                                <Shield size={48} className="opacity-10" />
                                <p className="text-sm font-medium italic">"Hello! I am your unified civic assistant. What community problem can I help you resolve today?"</p>
                             </div>
                           ) : (
                             actionLogs.map((log) => (
                               <motion.div 
                                 key={log.id} 
                                 initial={{ opacity: 0, y: 5 }}
                                 animate={{ opacity: 1, y: 0 }}
                                 className={`flex ${log.agent === 'CivicAssistant' ? 'justify-start' : 'justify-end'}`}
                               >
                                  <div className={`max-w-[90%] p-4 rounded-2xl ${
                                     log.agent === 'CivicAssistant' 
                                      ? 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700 shadow-sm' 
                                      : 'bg-indigo-600 text-white rounded-br-none shadow-lg shadow-indigo-500/10'
                                  }`}>
                                     <div className="text-[11px] leading-relaxed prose prose-invert prose-slate max-w-none 
                                       prose-p:mb-2 prose-last:mb-0
                                       prose-headings:text-indigo-400 prose-headings:font-bold prose-headings:text-xs prose-headings:uppercase prose-headings:tracking-widest prose-headings:mt-4 prose-headings:mb-2
                                       prose-table:my-3 prose-table:border-collapse prose-table:w-full
                                       prose-th:border prose-th:border-slate-800 prose-th:bg-slate-900/50 prose-th:px-2 prose-th:py-1 prose-th:text-[10px] prose-th:text-left
                                       prose-td:border prose-td:border-slate-800 prose-td:px-2 prose-td:py-1 prose-td:text-[10px]
                                       prose-hr:my-4 prose-hr:border-slate-800">
                                       <ReactMarkdown remarkPlugins={[remarkGfm]}>{log.details}</ReactMarkdown>
                                     </div>
                                     <p className="text-[8px] mt-2 opacity-40 font-mono uppercase tracking-widest">{log.timestamp}</p>
                                  </div>
                               </motion.div>
                             ))
                           )}
                           {isAnalyzing && (
                               <div className="flex justify-start">
                                  <div className="bg-slate-800 p-4 rounded-2xl rounded-tl-none border border-slate-700 shadow-lg">
                                     <div className="flex items-center gap-3">
                                        <div className="flex space-x-1">
                                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce"></div>
                                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                        </div>
                                        <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-widest">{analysisStatus || 'SYSCALL_PENDING'}</span>
                                     </div>
                                  </div>
                               </div>
                           )}
                        </div>

                        <div className="p-4 bg-slate-950/80 border-t border-slate-800">
                           <div className="flex gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-1.5 focus-within:border-indigo-500/50 transition-all shadow-xl">
                              <input 
                                type="text" 
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAction()}
                                placeholder="Tell me what's on your mind..."
                                className="flex-1 bg-transparent px-3 text-sm text-white placeholder:text-slate-600 outline-none"
                              />
                              <button 
                                onClick={handleAction}
                                disabled={isAnalyzing || !inputText.trim()}
                                className="w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center hover:bg-indigo-700 transition-all disabled:opacity-50 shadow-lg shadow-indigo-500/20 active:scale-95"
                              >
                                 <Send size={18} />
                              </button>
                           </div>
                        </div>
                    </div>
                </motion.div>
              )}

              {activeTab === 'agents' && (
                <motion.div 
                  key="agents"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-3xl font-bold text-white tracking-tight">Agent Cluster Management</h2>
                      <p className="text-slate-500 font-mono text-xs uppercase tracking-widest mt-1">Monitor and configure specialized autonomous nodes.</p>
                    </div>
                    <div className="flex gap-2">
                       <button className="px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-800 transition-all">Re-Sync All</button>
                       <button className="px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/20">New Cluster</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                     {(['FinAgent', 'MobilityAgent', 'EduAgent', 'AssetAgent'] as AgentType[]).map(agent => (
                        <AgentCard 
                          key={agent}
                          type={agent}
                          description={AGENT_DESCRIPTIONS[agent]}
                          active={activeAgent === agent}
                          onClick={() => setActiveAgent(agent)}
                        />
                     ))}
                  </div>
                </motion.div>
              )}

              {activeTab === 'library' && (
                <motion.div 
                   key="library"
                   initial={{ opacity: 0, scale: 0.95 }}
                   animate={{ opacity: 1, scale: 1 }}
                   exit={{ opacity: 0, scale: 1.05 }}
                   className="space-y-6"
                >
                   <div className="flex items-center gap-4 mb-4">
                      <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center text-amber-500 shadow-lg shadow-amber-500/5">
                        <Library size={32} />
                      </div>
                      <div>
                        <h2 className="text-3xl font-bold text-white tracking-tight">Library Automation</h2>
                        <p className="text-slate-500 font-mono text-[10px] uppercase tracking-[0.2em] mt-1">ID: 412-AST // AssetAgent Managed</p>
                      </div>
                   </div>

                   <div className="grid grid-cols-4 gap-6">
                      <div className="col-span-1 space-y-6">
                         <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
                           <h4 className="font-bold text-[10px] uppercase tracking-widest text-slate-500 mb-4 font-mono">Reserved Assets</h4>
                           <div className="space-y-4">
                              <BookThumb title="Urban Planning 101" dueDate="In 2 days" overdue={false} />
                              <BookThumb title="Smart Cities" dueDate="Overdue by 1d" overdue={true} />
                              <BookThumb title="The Civic Contract" dueDate="In 5 days" overdue={false} />
                           </div>
                         </div>
                         <button className="w-full py-4 bg-amber-600 text-white rounded-2xl font-bold shadow-lg shadow-amber-500/20 hover:bg-amber-700 transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-xs">
                           <Calendar size={18} />
                           Schedule Return
                         </button>
                      </div>

                      <div className="col-span-3 bg-slate-900/50 rounded-2xl border border-slate-800 p-8 flex flex-col gap-6">
                         <div className="flex justify-between items-start mb-4">
                            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-tighter font-mono">Resource RAG Q&A</span>
                            <button className="text-[10px] font-mono font-bold text-indigo-400 flex items-center gap-1 uppercase tracking-widest">
                              Select Sources <ChevronRight size={10} />
                            </button>
                         </div>
                         <div className="bg-slate-950 rounded-2xl p-6 min-h-[300px] border border-slate-800 font-serif leading-relaxed text-slate-300 italic relative">
                            {isLibraryLoading && (
                              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center rounded-2xl z-10 text-amber-500">
                                <Clock size={32} className="animate-spin" />
                              </div>
                            )}
                            <p className="text-xl leading-relaxed text-slate-200">
                               <span className="text-amber-500 font-bold block mb-4 not-italic font-mono text-xs uppercase tracking-widest">Answer Stream:</span>
                               {libraryAnswer}
                            </p>
                            <p className="mt-8 text-[10px] font-sans not-italic font-bold text-slate-600 uppercase tracking-[0.2em]">— Source: CivicNexus Knowledge base (AssetAgent)</p>
                         </div>
                         <div className="flex gap-3">
                            <input 
                              type="text" 
                              value={libraryQuestion}
                              onChange={(e) => setLibraryQuestion(e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && handleLibraryQA()}
                              placeholder="Ask a question about the library archives..."
                              className="flex-1 px-6 py-4 bg-slate-950 rounded-2xl border border-slate-800 outline-none text-white font-medium focus:ring-1 focus:ring-amber-500/30 transition-all"
                            />
                            <button 
                              onClick={handleLibraryQA}
                              disabled={isLibraryLoading || !libraryQuestion.trim()}
                              className="px-8 bg-slate-800 text-amber-500 rounded-2xl border border-slate-700 hover:bg-slate-700 transition-all disabled:opacity-50"
                            >
                               <Search size={22} />
                            </button>
                         </div>
                      </div>
                   </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>

      <footer className="fixed bottom-0 left-64 right-0 h-10 border-t border-slate-800 bg-slate-950/50 backdrop-blur-sm px-6 flex items-center justify-between text-[10px] text-slate-600 font-mono font-bold uppercase tracking-widest z-40">
        <span>CivicNexus v4.2.0-STABLE [0x8823FB]</span>
        <div className="flex gap-6">
           <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Sytem: SYNCHRONIZED</span>
           <span className="flex items-center gap-1 font-normal opacity-50">Encryption: AES-256-GCM</span>
        </div>
      </footer>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active: boolean, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-bold transition-all uppercase tracking-widest ${
        active ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:bg-slate-900 hover:text-slate-200'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function AgentStatus({ name, active, onClick, icon }: { name: string, active: boolean, onClick: () => void, icon: React.ReactNode }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all ${
        active ? 'bg-slate-900 border border-slate-800' : 'hover:bg-slate-900/50'
      }`}
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{name}</span>
      </div>
      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
    </button>
  );
}

function QuickAction({ label, onClick }: { label: string, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="flex-shrink-0 px-4 py-2 bg-slate-950 border border-slate-800 rounded-full text-[10px] font-bold text-slate-400 hover:bg-slate-900 hover:text-indigo-400 hover:border-indigo-500/30 transition-all flex items-center gap-2 group uppercase tracking-widest"
    >
      <Plus size={14} className="text-slate-600 group-hover:text-indigo-500" />
      {label}
    </button>
  );
}

function UserServiceCard({ icon, title, desc, onClick }: { icon: React.ReactNode, title: string, desc: string, onClick?: () => void }) {
  return (
    <div 
      onClick={onClick}
      className="bg-slate-950/50 p-5 rounded-2xl border border-slate-800 hover:border-indigo-500/30 hover:bg-slate-900 transition-all group cursor-pointer"
    >
       <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          {icon}
       </div>
       <h4 className="font-bold text-sm text-white mb-1">{title}</h4>
       <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
    </div>
  );
}

function StatBar({ label, value, color }: { label: string, value: number, color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] font-mono">
        <span>{label}</span>
        <span className="text-slate-300 italic">{value}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full ${color} shadow-[0_0_10px_rgba(0,0,0,0.5)]`}
        />
      </div>
    </div>
  );
}

interface AgentCardProps {
  type: AgentType;
  description: string;
  active: boolean;
  onClick: () => void;
}

function AgentCard({ type, description, active, onClick }: AgentCardProps) {
  const Icon = type === 'FinAgent' ? CircleDollarSign : type === 'MobilityAgent' ? Car : type === 'EduAgent' ? GraduationCap : Library;
  const color = type === 'FinAgent' ? 'emerald' : type === 'MobilityAgent' ? 'blue' : type === 'EduAgent' ? 'purple' : 'amber';
  
  return (
    <div 
      onClick={onClick}
      className={`p-6 rounded-2xl border transition-all cursor-pointer group ${
        active ? `border-${color}-500 bg-${color}-500/5 shadow-lg shadow-${color}-500/5` : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
         <div className={`w-12 h-12 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center text-${color}-500 group-hover:scale-110 transition-transform`}>
            <Icon size={24} />
         </div>
         <div className={`px-2 py-1 bg-${color}-500/10 text-${color}-400 text-[10px] font-bold rounded uppercase tracking-widest font-mono`}>STABLE</div>
      </div>
      <h3 className="font-bold text-lg mb-2 text-white">{type}</h3>
      <p className="text-xs text-slate-400 leading-relaxed mb-6 font-medium">{description}</p>
      <div className="flex gap-2">
         <button className={`flex-1 py-2 rounded-xl text-[10px] font-bold border border-slate-800 text-slate-400 bg-slate-950 hover:bg-slate-900 transition-colors uppercase tracking-widest`}>Logs</button>
         <button className={`flex-1 py-2 rounded-xl text-[10px] font-bold bg-${color}-600 text-white hover:opacity-90 transition-opacity uppercase tracking-widest shadow-lg shadow-${color}-500/10`}>Override</button>
      </div>
    </div>
  );
}

function BookThumb({ title, dueDate, overdue }: { title: string, dueDate: string, overdue: boolean }) {
  return (
    <div className="flex items-center gap-3 group cursor-pointer">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${overdue ? 'bg-red-500/10 border-red-500/30 text-red-500' : 'bg-slate-950 border-slate-800 text-slate-500'} group-hover:scale-105 transition-transform`}>
        <Library size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold truncate text-slate-200 uppercase tracking-tight">{title}</p>
        <p className={`text-[10px] uppercase font-bold tracking-widest ${overdue ? 'text-red-500' : 'text-slate-500'}`}>{dueDate}</p>
      </div>
    </div>
  );
}
