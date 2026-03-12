import React from 'react';
import '../styles/componentsStyles/buttons.css';

type ButtonProps = {
  label: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  disabled?: boolean;
  style?: React.CSSProperties;
  tooltip?: string;
};

const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  type = 'button',
  className = '',
  disabled = false,
  style,
  tooltip,
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`button ${className}`}
      disabled={disabled}
      style={style}
      data-tooltip={disabled ? tooltip : ''} // Tooltip only appears if enabled
      aria-label={label}
    >
      {label}
    </button>
  );
};

export default Button;
