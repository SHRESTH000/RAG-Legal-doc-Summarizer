'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { FileUpload } from '@/components/chat/FileUpload';
import { useVoiceInput } from '@/hooks/useVoiceInput';

interface ChatInputProps {
  onSend: (content: string, fileIds?: string[]) => void;
  onFileSelect?: (file: File) => Promise<{ file_id: string }>;
  isLoading?: boolean;
}

export function ChatInput({
  onSend,
  onFileSelect,
  isLoading = false,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFileIds, setUploadedFileIds] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { isListening, isSupported, toggle: toggleVoice } = useVoiceInput({
    onResult: (transcript) => setValue((prev) => (prev ? `${prev} ${transcript}` : transcript)),
  });

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [value]);

  const handleSubmit = async () => {
    const text = value.trim();
    if (!text && uploadedFileIds.length === 0) return;
    if (isLoading) return;

    let fileIds = uploadedFileIds;
    if (selectedFile && onFileSelect) {
      try {
        const res = await onFileSelect(selectedFile);
        fileIds = [...fileIds, res.file_id];
      } catch {
        return;
      }
    }

    onSend(text || 'Summarize the uploaded document.', fileIds.length ? fileIds : undefined);
    setValue('');
    setSelectedFile(null);
    setUploadedFileIds([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border-default bg-surface-primary px-4 py-3">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-xl border border-border-default bg-surface-secondary p-2 focus-within:border-border-muted">
          <FileUpload
            onSelect={setSelectedFile}
            selectedFile={selectedFile}
            onClear={() => setSelectedFile(null)}
            disabled={isLoading}
          />
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Indian criminal law..."
            disabled={isLoading}
            rows={1}
            className="min-h-[24px] max-h-[200px] flex-1 resize-none bg-transparent px-2 py-2 text-text-primary placeholder:text-text-muted focus:outline-none text-[15px]"
            aria-label="Message"
          />
          {isSupported && (
            <button
              type="button"
              onClick={toggleVoice}
              disabled={isLoading}
              className={`p-2 rounded-lg transition-colors ${
                isListening
                  ? 'bg-red-500/20 text-red-400'
                  : 'text-text-secondary hover:bg-surface-tertiary hover:text-text-primary'
              }`}
              title={isListening ? 'Stop listening' : 'Voice input'}
              aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
          )}
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading || (!value.trim() && !selectedFile)}
            variant="primary"
            size="md"
            aria-label="Send message"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
}
