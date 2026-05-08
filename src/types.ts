export type ViewMode = 'user' | 'admin';
export type AgentType = 'FinAgent' | 'MobilityAgent' | 'EduAgent' | 'AssetAgent' | 'Orchestrator' | 'CivicAssistant';

export interface UserProfile {
  name: string;
  email: string;
  phone: string;
  resumeText: string;
  skills: string[];
  education: string;
  experience: string;
}

export interface ChatSession {
  id: string;
  title: string;
  logs: ActionLog[];
  history: { role: 'user' | 'assistant', content: string }[];
  sessionAgent: AgentType | null;
  userProfile?: UserProfile;
  createdAt: number;
}

export interface ActionLog {
  id: string;
  timestamp: string;
  agent: AgentType;
  action: string;
  details: string;
  status: 'pending' | 'completed' | 'failed';
}

export interface CommunityIssue {
  id: string;
  title: string;
  description: string;
  category: 'Traffic' | 'Housing' | 'Funding' | 'Jobs' | 'Library';
  status: 'New' | 'Analyzing' | 'Acting' | 'Resolved';
}

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  FinAgent: 'Economic & Opportunity Agent. Specializes in SMB/Startup funding, government grants, and housing assistance.',
  MobilityAgent: 'Traffic & Logistics Agent. Monitors congestion, identifies alternate routes, and manages donation schedules.',
  EduAgent: 'Jobs & Learning Agent. Scrapes job boards, generates resumes, and finds accessible training programs.',
  AssetAgent: 'Library & Resource Agent. Manages RAG Q&A for books, notifications, and scheduling reservations.',
  Orchestrator: 'Master System Orchestrator. Deconstructs complex community problems and delegates tasks to specialized agents.',
  CivicAssistant: 'Unified Citizen Interface. Provides multi-agent synthesized responses and guided civic interactions.'
};
