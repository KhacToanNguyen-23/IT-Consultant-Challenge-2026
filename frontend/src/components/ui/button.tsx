import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type Size = "default" | "sm" | "lg" | "icon";

const variants: Record<Variant, string> = {
  primary: "bg-[var(--primary)] text-white shadow-sm hover:bg-[var(--primary-hover)] focus-visible:ring-[var(--primary)]",
  secondary: "bg-[var(--surface-muted)] text-[var(--ink)] ring-1 ring-inset ring-[var(--line)] hover:bg-white",
  outline: "bg-white text-[var(--ink)] ring-1 ring-inset ring-[var(--line-strong)] hover:bg-[var(--surface-muted)]",
  ghost: "bg-transparent text-[var(--ink-soft)] hover:bg-[var(--surface-muted)] hover:text-[var(--ink)]",
  danger: "bg-[var(--bad)] text-white shadow-sm hover:bg-[#951b13] focus-visible:ring-[var(--bad)]",
};

const sizes: Record<Size, string> = {
  default: "min-h-11 px-4 py-2.5 text-sm",
  sm: "min-h-9 px-3 py-2 text-sm",
  lg: "min-h-12 px-5 py-3 text-base",
  icon: "size-11 p-0",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export function Button({ className, variant = "outline", size = "default", type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-2 rounded-lg font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:translate-y-px",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  );
}
