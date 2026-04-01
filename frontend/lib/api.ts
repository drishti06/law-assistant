type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

async function http<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {}, signal } = options;

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };

  // Attach JWT token from localStorage
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      authHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const config: RequestInit = {
    method,
    headers: authHeaders,
    signal,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  // All API calls go through Next.js rewrite proxy at /api
  const res = await fetch(`/api${endpoint}`, config);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => http<T>(endpoint),
  post: <T>(endpoint: string, body: unknown) => http<T>(endpoint, { method: "POST", body }),
  delete: <T>(endpoint: string) => http<T>(endpoint, { method: "DELETE" }),
};

// Auth
export type LoginPayload = { email: string; password: string };
export type RegisterPayload = { name: string; email: string; password: string };
export type LoginResponse = { message: string; token: string; user: { name: string; email: string } };
export type UserResponse = { name: string; email: string; created_at: string };

export const authApi = {
  login: (data: LoginPayload) => api.post<LoginResponse>("/auth/login", data),
  register: (data: RegisterPayload) => api.post<UserResponse>("/auth/register", data),
  logout: () => api.post<{ message: string }>("/auth/logout", {}),
};

// Chat
export type ChatRequest = { query: string; language?: string };
export type ChatResponse = {
  answer: string;
  short_answer: string;
  explanation: string;
  relevant_law: string;
  next_steps: string;
  disclaimer: string;
  sources: string[];
};
export type ChatMessage = { role: string; content: string; timestamp: string };
export type HistorySession = {
  session_id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
};

export const chatApi = {
  send: (data: ChatRequest, signal?: AbortSignal) =>
    http<ChatResponse>("/chat", { method: "POST", body: data, signal }),
  history: () => api.get<HistorySession[]>("/history"),
  deleteSession: (id: string) => api.delete<{ message: string }>(`/history/${id}`),
};
