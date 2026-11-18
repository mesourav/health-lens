import type { ChatService } from '../types';
import { ChatServiceError } from './errors';
import { parseChatTurn } from './parseChatTurn';

interface HttpChatServiceOptions {
  /** e.g. "/api" or "https://chat.example.com" — the client POSTs to `${baseUrl}/chat`. */
  baseUrl: string;
  timeoutMs?: number;
}

/**
 * Talks to your own backend (Python + RAG). Policy data stays between the
 * browser and that backend; auth rides on the session cookie it sets after
 * policy-number + DOB verification, so no tokens are kept in JS.
 */
export function createHttpChatService({
  baseUrl,
  timeoutMs = 30_000,
}: HttpChatServiceOptions): ChatService {
  const endpoint = `${baseUrl.replace(/\/+$/, '')}/chat`;

  return {
    async respond(request, signal) {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        credentials: 'include',
        body: JSON.stringify(request),
        signal: AbortSignal.any([signal, AbortSignal.timeout(timeoutMs)]),
      });

      if (!response.ok) {
        throw new ChatServiceError(`Chat request failed (${response.status})`, response.status);
      }
      return parseChatTurn(await response.json());
    },
  };
}
