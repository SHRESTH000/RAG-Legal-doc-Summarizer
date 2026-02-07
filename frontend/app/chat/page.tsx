'use client';

import Link from 'next/link';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { useChat } from '@/hooks/useChat';
import { Button } from '@/components/ui/Button';

export default function ChatPage() {
  const {
    activeSession,
    activeSessionId,
    sessions,
    createSession,
    setActiveSession,
    send,
    uploadFile,
    isLoading,
  } = useChat();

  return (
    <div className="h-screen flex flex-col bg-surface-primary">
      <header className="flex items-center justify-between px-4 py-3 border-b border-border-default shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-text-secondary hover:text-text-primary transition-colors p-1 rounded"
            aria-label="Home"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </Link>
          <span className="font-semibold text-text-primary text-lg">
            Legal RAG
          </span>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={createSession}
          disabled={isLoading}
        >
          New chat
        </Button>
      </header>

      <div className="flex flex-1 min-h-0">
        {sessions.length > 0 && (
          <aside className="w-56 border-r border-border-default flex flex-col shrink-0 hidden md:flex">
            <div className="p-2 overflow-y-auto">
              {sessions.map((s) => (
                <button
                  key={s.session_id}
                  type="button"
                  onClick={() => setActiveSession(s.session_id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                    activeSessionId === s.session_id
                      ? 'bg-surface-tertiary text-text-primary'
                      : 'text-text-secondary hover:bg-surface-tertiary hover:text-text-primary'
                  }`}
                >
                  {s.title}
                </button>
              ))}
            </div>
          </aside>
        )}
        <main className="flex-1 min-w-0 flex flex-col">
          <ChatWindow
            session={activeSession}
            onSend={send}
            onFileUpload={uploadFile}
            isLoading={isLoading}
          />
        </main>
      </div>
    </div>
  );
}
