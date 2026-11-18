// Public API of the chat feature. Import from '@/features/chat', not from inside the folder.
export { ChatWindow, type ChatWindowProps } from './components/ChatWindow';
export { useChat, type UseChatOptions } from './hooks/useChat';
export {
  ChatServiceError,
  createChatService,
  createHttpChatService,
  createMockChatService,
} from './services';
export type * from './types';
