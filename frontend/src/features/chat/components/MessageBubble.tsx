import { cn } from '@/lib/cn';
import type { ChatMessage, Sender } from '../types';
import { SystemNotice } from './SystemNotice';

const bubbleClasses: Record<Exclude<Sender, 'system'>, string> = {
  user: 'border-brand-300 bg-brand-100 py-2 leading-snug text-brand-900',
  bot: 'border-divider py-2.5 leading-normal',
  agent: 'border-brand-400 py-2.5 leading-normal',
};

export function MessageBubble({ message }: { message: ChatMessage }) {
  const { sender, text, author } = message;
  if (sender === 'system') return <SystemNotice text={text} />;

  const isUser = sender === 'user';
  return (
    <div
      className={cn('flex flex-col gap-1', isUser ? 'max-w-[80%] self-end' : 'max-w-[88%] self-start')}
    >
      {author && <span className="text-xs text-muted">{author}</span>}
      <div
        className={cn(
          'rounded-sm border px-4 text-[15px] text-pretty break-words whitespace-pre-line',
          bubbleClasses[sender],
        )}
      >
        {text}
      </div>
    </div>
  );
}
