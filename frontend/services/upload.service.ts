import type { UploadResponse } from '@/types/chat';

const getBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url) throw new Error('NEXT_PUBLIC_API_BASE_URL is not set');
  return url.replace(/\/$/, '');
};

export async function uploadDocument(
  file: File,
  sessionId?: string
): Promise<UploadResponse> {
  const base = getBaseUrl();
  const form = new FormData();
  form.append('file', file);
  if (sessionId) form.append('session_id', sessionId);
  const res = await fetch(`${base}/api/upload`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? 'Upload failed');
  }
  return res.json() as Promise<UploadResponse>;
}
