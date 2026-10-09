"use client";

import { AnimatePresence, motion } from "motion/react";
import { Loader2, X } from "lucide-react";
import { useEffect } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "subtle" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "icon";

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent/90 shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_8px_24px_-12px_var(--color-accent)]",
  subtle: "bg-white/[0.06] text-ink hover:bg-white/[0.1]",
  ghost: "text-muted hover:text-ink hover:bg-white/[0.06]",
  danger: "bg-danger/15 text-danger hover:bg-danger/25",
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-[13px] gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  icon: "h-9 w-9 justify-center",
};

export function Button({
  variant = "subtle",
  size = "md",
  className,
  loading = false,
  children,
  disabled,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={cn(
        "inline-flex select-none items-center rounded-lg font-medium transition-colors duration-200 outline-none",
        "focus-visible:ring-2 focus-visible:ring-accent/60 focus-visible:ring-offset-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
      {children}
    </button>
  );
}

export function IconButton({
  label,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      {...props}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors duration-200 hover:bg-white/[0.08] hover:text-ink focus-visible:ring-2 focus-visible:ring-accent/60 outline-none disabled:opacity-40",
        className,
      )}
    />
  );
}

const fieldClass =
  "w-full rounded-lg border border-line bg-white/[0.03] px-3 py-2 text-sm text-ink placeholder:text-muted/70 outline-none transition-colors duration-200 focus:border-accent/60 focus:bg-white/[0.05] focus:ring-2 focus:ring-accent/20";

export function Input({
  className,
  ...props
}: React.ComponentPropsWithRef<"input">) {
  return <input {...props} className={cn(fieldClass, className)} />;
}

export function Textarea({
  className,
  ...props
}: React.ComponentPropsWithRef<"textarea">) {
  return (
    <textarea
      {...props}
      className={cn(fieldClass, "resize-none leading-relaxed", className)}
    />
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted">{label}</span>
      {children}
      {hint ? <span className="text-xs text-muted/70">{hint}</span> : null}
    </label>
  );
}

type BadgeTone = "neutral" | "accent" | "success" | "warning" | "danger";

const badgeTones: Record<BadgeTone, string> = {
  neutral: "bg-white/[0.06] text-muted",
  accent: "bg-accent/15 text-accent",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  danger: "bg-danger/15 text-danger",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        badgeTones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-4 w-4 animate-spin", className)} />;
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-lg bg-white/[0.05]", className)} />
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line px-6 py-16 text-center"
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.05] text-muted">
        {icon}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-ink">{title}</p>
        {description ? (
          <p className="mx-auto max-w-sm text-xs text-muted">{description}</p>
        ) : null}
      </div>
      {action}
    </motion.div>
  );
}

export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  width = "max-w-lg",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "relative z-10 w-full overflow-hidden rounded-2xl border border-line bg-elevated shadow-2xl",
              width,
            )}
          >
            <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
              <h2 className="text-sm font-semibold text-ink">{title}</h2>
              <IconButton label="Close" onClick={onClose}>
                <X className="h-4 w-4" />
              </IconButton>
            </div>
            <div className="px-5 py-4">{children}</div>
            {footer ? (
              <div className="flex items-center justify-end gap-2 border-t border-line px-5 py-3.5">
                {footer}
              </div>
            ) : null}
          </motion.div>
        </div>
      ) : null}
    </AnimatePresence>
  );
}
