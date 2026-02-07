'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceInputOptions {
  onResult?: (transcript: string) => void;
  onError?: (error: string) => void;
}

export function useVoiceInput(options: UseVoiceInputOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    const SpeechRecognitionAPI =
      typeof window !== 'undefined' &&
      (window.SpeechRecognition || (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition);
    setIsSupported(!!SpeechRecognitionAPI);
    if (!SpeechRecognitionAPI) return;
    const Recognition = window.SpeechRecognition ?? (window as unknown as { webkitSpeechRecognition: typeof SpeechRecognition }).webkitSpeechRecognition;
    recognitionRef.current = new Recognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'en-IN';
    recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join('');
      if (event.results[event.results.length - 1].isFinal && transcript.trim()) {
        options.onResult?.(transcript.trim());
      }
    };
    recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== 'aborted') options.onError?.(event.error);
    };
    recognitionRef.current.onend = () => setIsListening(false);
    return () => {
      recognitionRef.current?.abort();
      recognitionRef.current = null;
    };
  }, [options.onResult, options.onError]);

  const start = useCallback(() => {
    if (!recognitionRef.current || isListening) return;
    recognitionRef.current.start();
    setIsListening(true);
  }, [isListening]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (isListening) stop();
    else start();
  }, [isListening, start, stop]);

  return { isListening, isSupported, start, stop, toggle };
}
