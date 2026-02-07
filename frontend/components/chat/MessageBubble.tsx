'use client';

import type { ChatMessage } from '@/types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} px-4 py-3`}
    >
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-surface-tertiary text-text-primary rounded-br-md'
            : 'bg-surface-secondary text-text-primary border border-border-default rounded-bl-md'
        }`}
      >
        <div className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
          {message.content || (isStreaming ? (
            <span className="inline-flex gap-1">
              <span className="animate-pulse">●</span>
              <span className="animate-pulse [animation-delay:150ms]">●</span>
              <span className="animate-pulse [animation-delay:300ms]">●</span>
            </span>
          ) : null)}
        </div>
      </div>
    </div>
  );
}
