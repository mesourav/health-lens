import { Button } from '@/components/ui/Button';

interface ChatHeaderProps {
  title: string;
  subtitle: string;
  onRestart: () => void;
}

export function ChatHeader({ title, subtitle, onRestart }: ChatHeaderProps) {
  return (
    <header className="flex-none border-b border-divider">
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3.5 sm:px-6">
        <div className="flex min-w-0 flex-1 flex-col">
          <h1 className="truncate font-heading text-xl leading-tight font-semibold">{title}</h1>
          <p className="flex items-center gap-1.5 text-xs text-muted">
            <span aria-hidden="true" className="size-1.5 rounded-full bg-brand-600" />
            {subtitle}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onRestart}>
          Restart
        </Button>
      </div>
    </header>
  );
}
