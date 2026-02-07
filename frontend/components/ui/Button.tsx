'use client';

import { type ButtonHTMLAttributes, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = '',
      variant = 'primary',
      size = 'md',
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const base =
      'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface-primary disabled:opacity-50 disabled:pointer-events-none';
    const variants = {
      primary:
        'bg-white text-surface-primary hover:bg-gray-200 focus:ring-white',
      secondary:
        'bg-surface-tertiary text-text-primary border border-border-default hover:bg-border-muted focus:ring-border-muted',
      ghost:
        'text-text-secondary hover:bg-surface-tertiary hover:text-text-primary focus:ring-surface-tertiary',
      danger:
        'bg-red-600/90 text-white hover:bg-red-600 focus:ring-red-500',
    };
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-5 py-2.5 text-base',
    };
    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
