export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Note {
  id: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface Citation {
  document_id: number;
  filename: string;
  page_number: number | null;
  chunk_id: number | null;
  chunk_index: number;
  snippet: string;
}

export interface ChatResponse {
  conversation_id: number;
  message_id: number;
  answer: string;
  grounded: boolean;
  citations: Citation[];
}

export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  grounded?: boolean;
  pending?: boolean;
}

export interface DeleteResponse {
  message: string;
}
