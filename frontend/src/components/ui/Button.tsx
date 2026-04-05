import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', ...props }, ref) => {
    const baseStyles = 'px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50';
    const variants = {
      primary: 'bg-primary text-white hover:bg-gray-800',
      secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
      ghost: 'bg-transparent hover:bg-gray-100',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${className}`}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
export { Button };
