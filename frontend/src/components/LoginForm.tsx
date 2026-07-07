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
    <div className="login-container">
      <h2>Login to Kanban Studio</h2>
      {(error || localError) && (
        <div className="error-message">{error ?? localError}</div>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="form-input"
            placeholder="Enter username"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="form-input"
            placeholder="Enter password"
          />
        </div>
        <button 
          type="submit" 
          disabled={loading}
          className="btn-primary"
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
};