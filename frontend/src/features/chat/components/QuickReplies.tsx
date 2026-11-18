import { Button } from '@/components/ui/Button';
import type { QuickReply } from '../types';

interface QuickRepliesProps {
  replies: QuickReply[];
  onSelect: (reply: QuickReply) => void;
}

export function QuickReplies({ replies, onSelect }: QuickRepliesProps) {
  if (replies.length === 0) return null;

  return (
    <div role="group" aria-label="Suggested replies" className="flex flex-wrap justify-end gap-2">
      {replies.map((reply) => (
        <Button
          key={`${reply.intent}:${reply.label}`}
          variant="outline"
          size="sm"
          onClick={() => onSelect(reply)}
        >
          {reply.label}
        </Button>
      ))}
    </div>
  );
}
