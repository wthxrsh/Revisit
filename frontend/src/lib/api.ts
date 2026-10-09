import type {
  ChatResponse,
  Conversation,
  ConversationDetail,
  DeleteResponse,
  Document,
  Note,
  TokenResponse,
  User,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "revisit.token";
const EMAIL_KEY = "revisit.email";
export const UNAUTHORIZED_EVENT = "revisit:unauthorized";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(EMAIL_KEY);
}

export function setSession(token: string, email: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(EMAIL_KEY, email);
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EMAIL_KEY);
}

function extractMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const candidate = record.message ?? record.detail ?? record.error;
    if (typeof candidate === "string" && candidate.length > 0) return candidate;
    if (Array.isArray(candidate) && candidate.length > 0) {
      const first = candidate[0] as Record<string, unknown> | undefined;
      if (first && typeof first.msg === "string") return first.msg;
    }
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the Revisit API. Is the backend running?",
    );
  }

  if (response.status === 401) {
    clearSession();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      extractMessage(payload, response.statusText || "Request failed"),
      payload,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  register(email: string, password: string) {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string) {
    const data = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    return data.access_token;
  },

  listNotes(params: { search?: string; limit?: number; offset?: number } = {}) {
    const query = new URLSearchParams();
    if (params.search) query.set("search", params.search);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<Note[]>(`/notes${suffix}`);
  },

  createNote(title: string, content: string) {
    return request<Note>("/notes", {
      method: "POST",
      body: JSON.stringify({ title, content }),
    });
  },

  updateNote(id: number, title: string, content: string) {
    return request<Note>(`/notes/${id}`, {
      method: "PUT",
      body: JSON.stringify({ title, content }),
    });
  },

  deleteNote(id: number) {
    return request<DeleteResponse>(`/notes/${id}`, { method: "DELETE" });
  },

  listDocuments() {
    return request<Document[]>("/documents");
  },

  uploadDocument(file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<Document>("/documents", { method: "POST", body });
  },

  reprocessDocument(id: number) {
    return request<Document>(`/documents/${id}/process`, { method: "POST" });
  },

  deleteDocument(id: number) {
    return request<DeleteResponse>(`/documents/${id}`, { method: "DELETE" });
  },

  chat(input: {
    question: string;
    conversation_id?: number | null;
    top_k?: number | null;
    document_ids?: number[] | null;
  }) {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  listConversations() {
    return request<Conversation[]>("/conversations");
  },

  getConversation(id: number) {
    return request<ConversationDetail>(`/conversations/${id}`);
  },

  deleteConversation(id: number) {
    return request<DeleteResponse>(`/conversations/${id}`, {
      method: "DELETE",
    });
  },
};
