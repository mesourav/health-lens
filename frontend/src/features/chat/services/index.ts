import { env } from '@/config/env';
import type { ChatService } from '../types';
import { createHttpChatService } from './httpChatService';
import { createMockChatService } from './mock/mockChatService';

/** Real backend when VITE_CHAT_API_URL is set, scripted mock otherwise. */
export function createChatService(): ChatService {
  return env.chatApiUrl
    ? createHttpChatService({ baseUrl: env.chatApiUrl })
    : createMockChatService();
}

export { ChatServiceError } from './errors';
export { createHttpChatService } from './httpChatService';
export { createMockChatService } from './mock/mockChatService';
