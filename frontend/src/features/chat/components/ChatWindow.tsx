import { CHAT_COPY } from '../constants';
import { useAutoScroll } from '../hooks/useAutoScroll';
import { useChat, type UseChatOptions } from '../hooks/useChat';
import { ChatComposer } from './ChatComposer';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { QuickReplies } from './QuickReplies';

export type ChatWindowProps = UseChatOptions;

/** Full-page chat: header, scrolling conversation, quick replies and composer. */
export function ChatWindow(props: ChatWindowProps) {
  const { messages, replies, isTyping, mode, sendText, selectReply, restart } = useChat(props);
  const copy = CHAT_COPY[mode];
  const scrollRef = useAutoScroll<HTMLElement>(
    `${messages.length}:${isTyping}:${replies.length}`,
  );

  return (
    <div className="flex h-dvh flex-col bg-canvas font-sans text-ink">
      <ChatHeader title={copy.title} subtitle={copy.subtitle} onRestart={restart} />

      <main ref={scrollRef} className="flex-1 overflow-y-auto">
        <MessageList messages={messages} isTyping={isTyping} />
      </main>

      <footer className="flex-none border-t border-divider">
        <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))] sm:px-6">
          <QuickReplies replies={replies} onSelect={selectReply} />
          <ChatComposer placeholder={copy.placeholder} onSend={sendText} />
        </div>
      </footer>
    </div>
  );
}
