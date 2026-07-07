"use client";

import { useMemo, useRef, useState } from "react";
import clsx from "clsx";
import type { BoardData } from "@/lib/kanban";
import { aiChat, type AIChatMessage } from "@/lib/api";

export type AIChatEntry = AIChatMessage & { id: string };

const bubbleColors: Record<AIChatMessage["role"], string> = {
  user: "bg-[var(--primary-blue)] text-white",
  assistant: "bg-white text-[var(--navy-dark)] border border-[var(--stroke)]",
};

const formatTimestamp = () =>
  new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());

type AIChatSidebarProps = {
  token: string;
  board: BoardData;
  onBoardUpdate: (nextBoard: BoardData) => void;
};

export const AIChatSidebar = ({ token, board, onBoardUpdate }: AIChatSidebarProps) => {
  const [entries, setEntries] = useState<AIChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [open, setOpen] = useState(true);
  const [status, setStatus] = useState<"idle" | "sending" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const canSend = input.trim().length > 0 && status !== "sending";

  const submitMessage = async () => {
    if (!canSend) return;
    const message = input.trim();
    setInput("");
    setStatus("sending");
    setError(null);

    const newHistory: AIChatEntry[] = [
      ...entries,
      { id: crypto.randomUUID(), role: "user", content: message },
    ];
    setEntries(newHistory);

    try {
      const response = await aiChat(token, {
        board,
        message,
        history: newHistory.map(({ role, content }) => ({ role, content })),
      });

      const assistantEntry: AIChatEntry = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.reply,
      };

      setEntries((prev) => [...prev, assistantEntry]);
      if (response.board && response.board_updated) {
        onBoardUpdate(response.board);
      }
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "AI request failed");
      return;
    } finally {
      setStatus("idle");
      queueMicrotask(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      });
    }
  };

  const placeholder = useMemo(
    () =>
      status === "sending"
        ? "Thinking…"
        : "Ask how to rewrite, prioritize, or move cards",
    [status]
  );

  return (
    <aside
      className={clsx(
        "fixed right-0 top-16 z-40 flex h-[calc(100vh-4rem)] w-full max-w-md flex-col",
        "rounded-l-3xl border border-l-0 border-[var(--stroke)] bg-white/95 shadow-[var(--shadow)] backdrop-blur",
        "transition-transform duration-300",
        open ? "translate-x-0" : "translate-x-full"
      )}
    >
      <header className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
            AI Copilot
          </p>
          <h2 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
            Conversation
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--navy-dark)]"
        >
          {open ? "Close" : "Open"}
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        {entries.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-sm text-[var(--gray-text)]">
            <p>Ask for prioritization, card edits, or roadmap moves.</p>
          </div>
        ) : (
          <ul className="flex flex-col gap-3">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className={clsx(
                  "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
                  bubbleColors[entry.role],
                  entry.role === "user" ? "self-end" : "self-start"
                )}
              >
                <p className="whitespace-pre-wrap">{entry.content}</p>
                <span className="mt-2 block text-[10px] uppercase tracking-[0.2em] text-white/70">
                  {formatTimestamp()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <footer className="border-t border-[var(--stroke)] px-6 py-4">
        {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
        <div className="flex items-end gap-3">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={placeholder}
            rows={3}
            className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:ring-2 focus:ring-[var(--secondary-purple)]"
          />
          <button
            type="button"
            disabled={!canSend}
            onClick={submitMessage}
            className="rounded-2xl bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white disabled:opacity-40"
          >
            {status === "sending" ? "Sending…" : "Send"}
          </button>
        </div>
      </footer>
    </aside>
  );
};
