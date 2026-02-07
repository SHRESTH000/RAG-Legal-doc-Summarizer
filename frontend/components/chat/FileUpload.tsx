'use client';

import { useRef } from 'react';
import { ACCEPTED_FILE_TYPES, MAX_FILE_SIZE_MB } from '@/utils/constants';

const MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface FileUploadProps {
  onSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  disabled?: boolean;
  accept?: string;
}

export function FileUpload({
  onSelect,
  selectedFile,
  onClear,
  disabled,
  accept = ACCEPTED_FILE_TYPES,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_BYTES) {
      return;
    }
    onSelect(file);
    e.target.value = '';
  };

  return (
    <div className="flex items-center gap-2">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
        aria-label="Upload document"
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className="p-2 rounded-lg text-text-secondary hover:bg-surface-tertiary hover:text-text-primary transition-colors disabled:opacity-50"
        title="Upload PDF, DOCX, or TXT"
        aria-label="Upload document"
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
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </button>
      {selectedFile && (
        <span className="text-sm text-text-secondary truncate max-w-[140px]" title={selectedFile.name}>
          {selectedFile.name}
        </span>
      )}
      {selectedFile && (
        <button
          type="button"
          onClick={onClear}
          disabled={disabled}
          className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-surface-tertiary"
          aria-label="Remove file"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      )}
    </div>
  );
}
