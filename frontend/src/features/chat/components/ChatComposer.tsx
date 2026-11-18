import { useId, useState, type FormEvent } from 'react';
import { SendIcon } from '@/components/icons/SendIcon';
import { Button } from '@/components/ui/Button';
import { MAX_MESSAGE_LENGTH } from '../constants';

interface ChatComposerProps {
  placeholder: string;
  onSend: (text: string) => void;
}

export function ChatComposer({ placeholder, onSend }: ChatComposerProps) {
  const [draft, setDraft] = useState('');
  const inputId = useId();
  const canSend = draft.trim().length > 0;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSend) return;
    onSend(draft);
    setDraft('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <label htmlFor={inputId} className="sr-only">
        Message
      </label>
      <input
        id={inputId}
        type="text"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder={placeholder}
        maxLength={MAX_MESSAGE_LENGTH}
        autoComplete="off"
        className="min-h-11 min-w-0 flex-1 border border-divider bg-surface px-3 text-[15px] text-ink caret-brand-600 placeholder:text-muted hover:border-ink/40 focus-visible:border-brand-600 focus-visible:outline-2 focus-visible:outline-brand-600"
      />
      <Button type="submit" variant="primary" size="icon" aria-label="Send message" disabled={!canSend}>
        <SendIcon />
      </Button>
    </form>
  );
}
