import type { ComponentProps } from 'react';
import { cn } from '@/lib/cn';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost';
type Size = 'sm' | 'md' | 'icon';

const variantClasses: Record<Variant, string> = {
  primary: 'border-brand-700 bg-brand-700 text-white hover:bg-brand-800 active:bg-brand-900',
  secondary: 'border-divider text-ink hover:bg-ink/5 active:bg-ink/10',
  outline: 'border-brand-400 text-brand-700 hover:bg-brand-100 active:bg-brand-200',
  ghost: 'border-transparent text-brand-700 hover:bg-brand-600/10 active:bg-brand-600/20',
};

const sizeClasses: Record<Size, string> = {
  sm: 'min-h-9 px-3 text-sm',
  md: 'min-h-11 px-4 text-[15px]',
  icon: 'size-11 shrink-0',
};

export interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant;
  size?: Size;
}

export function Button({
  variant = 'secondary',
  size = 'md',
  type = 'button',
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex cursor-pointer items-center justify-center gap-1.5 border font-heading leading-tight font-semibold transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}
