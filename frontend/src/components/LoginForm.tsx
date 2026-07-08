"use client";

import { useState } from "react";

type LoginFormProps = {
  onLogin: (username: string, password: string) => Promise<void> | void;
  error?: string | null;
  loading?: boolean;
};

export const LoginForm = ({ onLogin, error, loading }: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setLocalError("Please enter both username and password");
      return;
    }
    setLocalError(null);
    await onLogin(username, password);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-6">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <div className="relative w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/80 p-10 shadow-[var(--shadow)] backdrop-blur">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
          <h2 className="mt-4 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Kanban Studio
          </h2>
          <p className="mt-2 text-sm text-[var(--gray-text)]">
            Sign in to view your board
          </p>
        </div>

        {(error || localError) && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            {error ?? localError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          <div>
            <label
              htmlFor="username"
              className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
              placeholder="Enter username"
              autoComplete="username"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
              placeholder="Enter password"
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
};