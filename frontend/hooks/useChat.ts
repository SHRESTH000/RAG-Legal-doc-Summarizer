'use client';

import { useCallback, useEffect, useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import { sendMessage } from '@/services/chat.service';
import { uploadDocument } from '@/services/upload.service';
import type { ChatMessage } from '@/types/chat';

function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat() {
  const [isLoading, setIsLoading] = useState(false);
  const {
    sessions,
    activeSessionId,
    hydrate,
    createSession,
    setActiveSession,
    getActiveSession,
    addMessage,
    updateMessage,
  } = useChatStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const send = useCallback(
    async (content: string, fileIds?: string[]) => {
      let sessionId = activeSessionId;
      if (!sessionId) {
        sessionId = createSession();
      }
      const userMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'user',
        content,
        timestamp: Date.now(),
      };
      addMessage(sessionId, userMessage);

      const placeholderId = generateMessageId();
      const assistantMessage: ChatMessage = {
        id: placeholderId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };
      addMessage(sessionId, assistantMessage);
      setIsLoading(true);
      try {
        const res = await sendMessage({
          query: content,
          session_id: sessionId,
          file_ids: fileIds?.length ? fileIds : undefined,
        });
        updateMessage(sessionId, placeholderId, res.response);
      } catch (err) {
        updateMessage(
          sessionId,
          placeholderId,
          `Error: ${err instanceof Error ? err.message : 'Request failed'}. Please try again.`
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeSessionId, createSession, addMessage, updateMessage]
  );

  const uploadFile = useCallback(async (file: File, sessionId?: string) => {
    return uploadDocument(file, sessionId ?? activeSessionId ?? undefined);
  }, [activeSessionId]);

  return {
    sessions: Object.values(sessions).sort(
      (a, b) => b.updatedAt - a.updatedAt
    ),
    activeSessionId,
    activeSession: getActiveSession(),
    createSession,
    setActiveSession,
    send,
    uploadFile,
    isLoading,
  };
}
