import type { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
}

export function MessageList({ messages, isTyping }: MessageListProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-6 sm:px-6">
      <div
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label="Conversation"
        className="flex flex-col gap-3"
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
      {isTyping && <TypingIndicator />}
    </div>
  );
}
