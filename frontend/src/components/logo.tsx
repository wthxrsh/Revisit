import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative grid h-8 w-8 shrink-0 place-items-center rounded-[10px] bg-gradient-to-br from-accent to-accent-2 shadow-[0_10px_30px_-14px_var(--color-accent)]",
        className,
      )}
    >
      <span className="absolute inset-0 rounded-[10px] ring-1 ring-inset ring-white/25" />
      <svg viewBox="0 0 24 24" className="relative h-4 w-4" aria-hidden="true">
        <path
          d="M5.5 12a6.5 6.5 0 1 0 1.9-4.6"
          fill="none"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
        <path
          d="M5.2 5.6v3.6h3.6"
          fill="none"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="12" r="2.4" fill="white" />
      </svg>
    </span>
  );
}

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string;
  showWordmark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {showWordmark ? (
        <span className="text-gradient select-none text-[15px] font-semibold tracking-tight">
          Revisit
        </span>
      ) : null}
    </span>
  );
}
