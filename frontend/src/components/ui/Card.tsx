/**
 * Card Component
 * Reusable card container
 */
import React from 'react';
import { clsx } from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  className,
  ...props
}) => {
  const variants = {
    default: 'bg-white rounded-lg shadow-sm border border-gray-200',
    bordered: 'bg-white rounded-lg border-2 border-gray-300',
    elevated: 'bg-white rounded-lg shadow-lg',
  };

  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={clsx(variants[variant], paddings[padding], className)}
      {...props}
    >
      {children}
    </div>
  );
};
