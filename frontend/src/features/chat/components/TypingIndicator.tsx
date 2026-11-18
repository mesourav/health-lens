const DOT_DELAYS = ['0ms', '150ms', '300ms'];

export function TypingIndicator() {
  return (
    <div role="status" className="flex gap-1.5 self-start rounded-sm border border-divider p-4">
      <span className="sr-only">Assistant is typing</span>
      {DOT_DELAYS.map((delay) => (
        <span
          key={delay}
          aria-hidden="true"
          className="size-1.5 animate-typing rounded-full bg-muted motion-reduce:animate-none"
          style={{ animationDelay: delay }}
        />
      ))}
    </div>
  );
}
