export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
}

export interface ChatSession {
  session_id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  file_ids?: string[];
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
}
