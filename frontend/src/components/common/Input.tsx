import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightElement, className = '', id, ...props }, ref) => {
    const inputId = id || props.name || Math.random().toString(36).substring(2, 9);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {label}
            {props.required && <span className="text-rose-400 ml-1">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 flex items-center pointer-events-none text-slate-500">
              {leftIcon}
            </div>
          )}

          <input
            id={inputId}
            ref={ref}
            className={`w-full bg-slate-900/80 text-slate-100 border text-sm rounded-lg px-3.5 py-2.5 transition-all outline-none placeholder:text-slate-500 disabled:opacity-50 disabled:bg-slate-950 ${
              leftIcon ? 'pl-10' : ''
            } ${rightElement ? 'pr-10' : ''} ${
              error
                ? 'border-rose-500 focus:border-rose-400 focus:ring-1 focus:ring-rose-400/30'
                : 'border-slate-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30'
            } ${className}`}
            {...props}
          />

          {rightElement && (
            <div className="absolute right-3 flex items-center">
              {rightElement}
            </div>
          )}
        </div>

        {error ? (
          <p className="text-xs text-rose-400 font-medium">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-slate-400">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
