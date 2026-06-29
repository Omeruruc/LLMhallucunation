export interface Message {
  id: string;
  type: 'user' | 'agent';
  agentNumber?: number;
  content: string;
  color?: string;
  isThinking?: boolean;
  hasCorrected?: boolean;
}

export interface AgentConfig {
  number: number;
  temperature: number;
  color: string;
}

export interface GlobalSettings {
  maxTokens: number;
  topP: number;
}
