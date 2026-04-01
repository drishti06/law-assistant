"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { chatApi, authApi, type HistorySession } from "@/lib/api";

type Props = {
  isOpen: boolean;
  onClose: () => void;
};

export default function Sidebar({ isOpen, onClose }: Props) {
  const router = useRouter();
  const [history, setHistory] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(false);
  const [userName, setUserName] = useState("");

  useEffect(() => {
    const user = localStorage.getItem("user");
    if (user) {
      try {
        setUserName(JSON.parse(user).name);
      } catch {}
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  async function loadHistory() {
    setLoading(true);
    try {
      const data = await chatApi.history();
      setHistory(data);
    } catch {
      // Silently fail - history is not critical
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch {}
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    router.push("/login");
  }

  async function handleDeleteSession(id: string) {
    try {
      await chatApi.deleteSession(id);
      setHistory((prev) => prev.filter((s) => s.session_id !== id));
    } catch {}
  }

  function getSessionPreview(session: HistorySession): string {
    const firstUserMsg = session.messages.find((m) => m.role === "user");
    if (firstUserMsg) {
      return firstUserMsg.content.length > 50
        ? firstUserMsg.content.slice(0, 50) + "..."
        : firstUserMsg.content;
    }
    return "Chat session";
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 dark:bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-72 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 z-50 transform transition-transform duration-200 flex flex-col ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚖</span>
            <span className="font-semibold text-gray-800 dark:text-gray-100 text-sm">Legal Chatbot</span>
          </div>
          <button onClick={onClose} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat button */}
        <div className="px-3 py-3">
          <button
            onClick={() => {
              window.location.reload();
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-primary-700 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 hover:bg-primary-100 dark:hover:bg-primary-900/50 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* History */}
        <div className="flex-1 overflow-y-auto px-3">
          <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider px-2 mb-2">
            History
          </p>
          {loading ? (
            <div className="text-center py-4 text-gray-400 dark:text-gray-500 text-sm">Loading...</div>
          ) : history.length === 0 ? (
            <div className="text-center py-4 text-gray-400 dark:text-gray-500 text-sm">No chat history</div>
          ) : (
            <div className="space-y-1">
              {history.map((session) => (
                <div
                  key={session.session_id}
                  className="group flex items-center gap-1 px-2 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                >
                  <span className="flex-1 text-sm text-gray-600 dark:text-gray-300 truncate">
                    {getSessionPreview(session)}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.session_id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 dark:hover:text-red-400 p-0.5 transition-opacity"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User / Logout */}
        <div className="border-t border-gray-100 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-400 flex items-center justify-center text-sm font-bold">
                {userName.charAt(0).toUpperCase() || "U"}
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate max-w-[140px]">
                {userName || "User"}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 p-1.5 transition-colors"
              title="Logout"
            >
              <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
