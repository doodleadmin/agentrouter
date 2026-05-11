interface LiquidButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  fullWidth?: boolean;
  type?: 'button' | 'submit';
}

export function LiquidButton({
  children,
  onClick,
  variant = 'primary',
  disabled,
  fullWidth = true,
  type = 'button',
}: LiquidButtonProps) {
  return (
    <button
      type={type}
      className={`liquid-button liquid-button--${variant} ${fullWidth ? 'liquid-button--full' : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
