import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ChatWindow, createChatService } from '@/features/chat';

// Created once at module scope so the service identity is stable across renders.
const chatService = createChatService();

export default function App() {
  return (
    <ErrorBoundary>
      <ChatWindow service={chatService} />
    </ErrorBoundary>
  );
}
