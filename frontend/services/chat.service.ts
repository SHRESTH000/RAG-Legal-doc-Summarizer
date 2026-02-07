import type { ChatRequest, ChatResponse } from '@/types/chat';

const getBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url) throw new Error('NEXT_PUBLIC_API_BASE_URL is not set');
  return url.replace(/\/$/, '');
};

export async function sendMessage(
  payload: ChatRequest
): Promise<ChatResponse> {
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? 'Chat request failed');
  }
  return res.json() as Promise<ChatResponse>;
}
