export function SystemNotice({ text }: { text: string }) {
  return (
    <div className="flex w-full items-center gap-3 py-1.5 text-xs tracking-[0.06em] text-muted uppercase">
      <span aria-hidden="true" className="h-px flex-1 bg-divider" />
      <span>{text}</span>
      <span aria-hidden="true" className="h-px flex-1 bg-divider" />
    </div>
  );
}
