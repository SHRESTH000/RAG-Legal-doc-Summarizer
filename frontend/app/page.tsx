import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-surface-primary px-4">
      <h1 className="text-3xl font-semibold text-text-primary mb-2">
        Legal RAG Assistant
      </h1>
      <p className="text-text-secondary text-center max-w-md mb-8">
        Indian Criminal Law summarization powered by retrieval-augmented generation.
      </p>
      <Link
        href="/chat"
        className="rounded-lg bg-white text-surface-primary px-6 py-3 font-medium hover:bg-gray-200 transition-colors"
      >
        Open Chat
      </Link>
    </main>
  );
}
