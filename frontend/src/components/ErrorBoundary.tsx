import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from './ui/Button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Report to your error tracker (Sentry, GCP Error Reporting) here.
    console.error(error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      this.props.fallback ?? (
        <div role="alert" className="flex h-dvh flex-col items-center justify-center gap-4 p-6">
          <p className="text-[15px]">Something went wrong while loading the chat.</p>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </div>
      )
    );
  }
}
