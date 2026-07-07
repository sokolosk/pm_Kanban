"use client";

import { LoginForm } from "@/components/LoginForm";
import { KanbanBoard } from "@/components/KanbanBoard";
import { useState, useEffect } from "react";
import { apiLogin, apiLogout } from "@/lib/api";

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ id: number; username: string } | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem("kanban-token");
    const storedUser = localStorage.getItem("kanban-user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = async (username: string, password: string) => {
    setAuthError(null);
    setAuthLoading(true);
    try {
      const result = await apiLogin(username, password);
      setToken(result.access_token);
      setUser(result.user);
      localStorage.setItem("kanban-token", result.access_token);
      localStorage.setItem("kanban-user", JSON.stringify(result.user));
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Login failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    if (token) {
      try {
        await apiLogout(token);
      } catch (error) {
        console.error("Logout failed", error);
      }
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem("kanban-token");
    localStorage.removeItem("kanban-user");
  };

  if (!token || !user) {
    return <LoginForm onLogin={handleLogin} error={authError} loading={authLoading} />;
  }

  return (
    <div className="relative">
      <header className="fixed top-0 left-0 right-0 bg-white shadow-md z-50 p-4">
        <div className="flex justify-between items-center">
          <div className="text-lg font-semibold text-navy-dark">Kanban Studio</div>
          <button
            onClick={handleLogout}
            className="rounded-full bg-gray-200 text-gray-800 px-3 py-1 text-sm font-medium hover:bg-gray-300"
          >
            Logout
          </button>
        </div>
      </header>
      <main className="relative mt-16">
        <KanbanBoard token={token} user={user} onLogout={handleLogout} />
      </main>
    </div>
  );
}
