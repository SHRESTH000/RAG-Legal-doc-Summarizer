# Legal RAG Chat Frontend

Next.js frontend for the Indian Criminal Law RAG summarization system. ChatGPT-like chat interface with session management, file upload, and voice input.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Zustand** (state)
- **Web Speech API** (voice-to-text)

## Setup

1. **Install dependencies**

   ```bash
   cd frontend
   npm install
   ```

2. **Environment**

   Copy `env.example` to `.env.local` in the `frontend` folder and set your backend URL:

   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

   Replace with your backend base URL (no trailing slash).

3. **Run**

   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000). Use **Open Chat** or go to `/chat`.

## Scripts

- `npm run dev` – Development server
- `npm run build` – Production build
- `npm run start` – Run production server
- `npm run lint` – ESLint

## Backend API Contract

The frontend expects these endpoints:

- **POST `/api/chat`**  
  Body: `{ "query": string, "session_id"?: string, "file_ids"?: string[] }`  
  Response: `{ "response": string, "session_id": string }`

- **POST `/api/upload`**  
  Body: `FormData` with `file` and optional `session_id`  
  Response: `{ "file_id": string, "filename": string }`

Set `NEXT_PUBLIC_API_BASE_URL` to the backend base URL.

## Folder Structure

```
frontend/
├── app/              # App Router pages & layout
├── components/       # Chat & UI components
├── services/         # API layer (chat, upload)
├── store/            # Zustand chat store
├── hooks/            # useChat, useVoiceInput
├── types/            # TypeScript types
├── utils/            # Constants
└── styles/           # Global CSS
```

## Features

- Full-screen ChatGPT-style chat
- Create / continue sessions (persisted in `localStorage`)
- Text input, file upload (PDF, DOCX, TXT), voice-to-text (Web Speech API)
- Loading state and error handling
- No API calls inside UI components; all in `services/`
