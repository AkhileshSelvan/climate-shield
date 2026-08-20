import { type ReactNode } from "react";

// ─── Card ───────────────────────────────────────────────────
interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = "", hover = true }: CardProps) {
  return (
    <div
      className={`
        glass-card p-6
        ${hover ? "hover:border-climate-500/20" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

// ─── Badge ──────────────────────────────────────────────────
interface BadgeProps {
  children: ReactNode;
  variant?: "low" | "medium" | "high" | "severe" | "info" | "success" | "warning";
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
}

const BADGE_STYLES = {
  low: "bg-climate-500/15 text-climate-400 border-climate-500/30",
  medium: "bg-alert-500/15 text-alert-400 border-alert-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  severe: "bg-danger-500/15 text-danger-400 border-danger-500/30",
  info: "bg-ocean-500/15 text-ocean-400 border-ocean-500/30",
  success: "bg-climate-500/15 text-climate-400 border-climate-500/30",
  warning: "bg-alert-500/15 text-alert-400 border-alert-500/30",
};

const BADGE_SIZES = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-1.5 text-base font-semibold",
};

export function Badge({
  children,
  variant = "info",
  size = "md",
  pulse = false,
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-medium
        ${BADGE_STYLES[variant]}
        ${BADGE_SIZES[size]}
        ${pulse ? "simulated-pulse" : ""}
      `}
    >
      {children}
    </span>
  );
}

// ─── Button ─────────────────────────────────────────────────
interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: "button" | "submit";
  id?: string;
}

const BUTTON_STYLES = {
  primary:
    "bg-gradient-to-r from-climate-600 to-climate-500 hover:from-climate-500 hover:to-climate-400 text-white shadow-[0_4px_20px_rgba(16,185,129,0.3)]",
  secondary:
    "bg-navy-700 hover:bg-navy-600 text-gray-200 border border-gray-700 hover:border-gray-600",
  danger:
    "bg-gradient-to-r from-danger-600 to-danger-500 hover:from-danger-500 hover:to-danger-400 text-white",
  ghost:
    "bg-transparent hover:bg-navy-700 text-gray-400 hover:text-gray-200",
};

const BUTTON_SIZES = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-8 py-3.5 text-base",
};

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  className = "",
  type = "button",
  id,
}: ButtonProps) {
  return (
    <button
      id={id}
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2 rounded-xl font-semibold
        transition-all duration-200 cursor-pointer
        disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
        active:scale-[0.98]
        ${BUTTON_STYLES[variant]}
        ${BUTTON_SIZES[size]}
        ${className}
      `}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}

// ─── Input ──────────────────────────────────────────────────
interface InputProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  required?: boolean;
  id?: string;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  helpText?: string;
}

export function Input({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required = false,
  id,
  min,
  max,
  step,
  disabled = false,
  helpText,
}: InputProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-gray-300"
      >
        {label}
        {required && <span className="text-danger-400 ml-1">*</span>}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className="w-full px-4 py-2.5 bg-navy-800 border border-gray-700 rounded-xl
                   text-gray-100 placeholder-gray-500
                   focus:border-climate-500 focus:ring-1 focus:ring-climate-500/30
                   transition-all duration-200
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
      {helpText && (
        <p className="text-xs text-gray-500">{helpText}</p>
      )}
    </div>
  );
}

// ─── Select ─────────────────────────────────────────────────
interface SelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly { value: string; label: string }[] | readonly string[];
  placeholder?: string;
  required?: boolean;
  id?: string;
  disabled?: boolean;
}

export function Select({
  label,
  value,
  onChange,
  options,
  placeholder = "Select...",
  required = false,
  id,
  disabled = false,
}: SelectProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-gray-300"
      >
        {label}
        {required && <span className="text-danger-400 ml-1">*</span>}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        disabled={disabled}
        className="w-full px-4 py-2.5 bg-navy-800 border border-gray-700 rounded-xl
                   text-gray-100 appearance-none cursor-pointer
                   focus:border-climate-500 focus:ring-1 focus:ring-climate-500/30
                   transition-all duration-200
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const label = typeof opt === "string" ? opt : opt.label;
          return (
            <option key={val} value={val}>
              {label}
            </option>
          );
        })}
      </select>
    </div>
  );
}

// ─── Loader ─────────────────────────────────────────────────
interface LoaderProps {
  text?: string;
  size?: "sm" | "md" | "lg";
}

export function Loader({ text = "Loading...", size = "md" }: LoaderProps) {
  const sizes = {
    sm: "h-6 w-6",
    md: "h-10 w-10",
    lg: "h-16 w-16",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 animate-fade-in">
      <div className="relative">
        <div
          className={`${sizes[size]} rounded-full border-2 border-navy-700 border-t-climate-500 animate-spin`}
        />
      </div>
      {text && <p className="text-sm text-gray-400">{text}</p>}
    </div>
  );
}

// ─── Skeleton ───────────────────────────────────────────────
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "h-4 w-full" }: SkeletonProps) {
  return <div className={`skeleton ${className}`} />;
}

// ─── ErrorState ─────────────────────────────────────────────
interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 animate-fade-in">
      <div className="w-16 h-16 rounded-full bg-danger-500/10 flex items-center justify-center">
        <svg
          className="w-8 h-8 text-danger-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-200">{title}</h3>
        <p className="text-sm text-gray-400 mt-1 max-w-md">{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}

// ─── EmptyState ─────────────────────────────────────────────
interface EmptyStateProps {
  title: string;
  message: string;
  icon?: ReactNode;
}

export function EmptyState({ title, message, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 animate-fade-in">
      {icon ? (
        icon
      ) : (
        <div className="w-16 h-16 rounded-full bg-navy-700 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
      )}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-200">{title}</h3>
        <p className="text-sm text-gray-400 mt-1 max-w-md">{message}</p>
      </div>
    </div>
  );
}

// ─── MetricCard ─────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const METRIC_ACCENTS = {
  default: "border-l-gray-600",
  success: "border-l-climate-500",
  warning: "border-l-alert-500",
  danger: "border-l-danger-500",
  info: "border-l-ocean-500",
};

export function MetricCard({
  label,
  value,
  subtitle,
  icon,
  variant = "default",
}: MetricCardProps) {
  return (
    <div
      className={`glass-card p-5 border-l-4 ${METRIC_ACCENTS[variant]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {label}
          </p>
          <p className="text-2xl font-bold text-gray-100 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-gray-500">{icon}</div>
        )}
      </div>
    </div>
  );
}

// ─── SimulatedBadge ─────────────────────────────────────────
export function SimulatedBadge() {
  return (
    <Badge variant="warning" size="sm" pulse>
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      Simulated Data
    </Badge>
  );
}
