'use client';

import { useEffect, useRef } from 'react';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import type { ChatSession } from '@/types/chat';

interface ChatWindowProps {
  session: ChatSession | null;
  onSend: (content: string, fileIds?: string[]) => void;
  onFileUpload?: (file: File, sessionId?: string) => Promise<{ file_id: string }>;
  isLoading?: boolean;
}

export function ChatWindow({
  session,
  onSend,
  onFileUpload,
  isLoading = false,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const messages = session?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const lastMessage = messages[messages.length - 1];
  const isStreaming =
    isLoading &&
    lastMessage?.role === 'assistant' &&
    lastMessage.content === '';

  return (
    <div className="flex flex-col h-full bg-surface-primary">
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <h2 className="text-xl font-semibold text-text-primary mb-2">
              Legal RAG Assistant
            </h2>
            <p className="text-text-secondary max-w-md text-[15px]">
              Ask questions about Indian criminal law, upload a judgment (PDF, DOCX, TXT), or use voice input to get started.
            </p>
          </div>
        ) : (
          <div className="py-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isStreaming={
                  isStreaming && msg.id === lastMessage?.id
                }
              />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput
        onSend={onSend}
        onFileSelect={
          onFileUpload && session
            ? (file) => onFileUpload(file, session.session_id)
            : undefined
        }
        isLoading={isLoading}
      />
    </div>
  );
}
