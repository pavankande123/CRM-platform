import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';
import { Button } from './Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught rendering error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center p-6 text-slate-100">
          <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md text-center">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-rose-950/60 border border-rose-800/50 flex items-center justify-center text-rose-400 mb-6">
              <AlertOctagon className="w-8 h-8" />
            </div>

            <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
            <p className="text-sm text-slate-400 mb-6">
              An unexpected client error occurred. The technical details have been recorded.
            </p>

            {this.state.error && (
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-left mb-6 overflow-x-auto text-xs text-rose-300 font-mono">
                {this.state.error.message}
              </div>
            )}

            <Button
              variant="primary"
              size="md"
              leftIcon={<RotateCcw className="w-4 h-4" />}
              onClick={this.handleReset}
              className="w-full"
            >
              Reload Application
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
