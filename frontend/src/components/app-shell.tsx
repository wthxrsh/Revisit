"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { Files, LogOut, MessagesSquare, NotebookPen } from "lucide-react";

import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Logo, LogoMark } from "@/components/logo";
import { IconButton } from "@/components/ui";

const NAV = [
  { href: "/ask", label: "Ask", icon: MessagesSquare },
  { href: "/notes", label: "Notes", icon: NotebookPen },
  { href: "/documents", label: "Documents", icon: Files },
] as const;

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function DesktopNavLink({
  href,
  label,
  icon: Icon,
}: {
  href: string;
  label: string;
  icon: (typeof NAV)[number]["icon"];
}) {
  const pathname = usePathname();
  const active = isActive(pathname, href);

  return (
    <Link
      href={href}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors duration-200",
        active ? "text-ink" : "text-muted hover:text-ink",
      )}
    >
      {active ? (
        <motion.span
          layoutId="revisit-nav-active"
          transition={{ type: "spring", stiffness: 420, damping: 34 }}
          className="absolute inset-0 rounded-xl bg-white/[0.07] ring-1 ring-inset ring-white/[0.06]"
        />
      ) : null}
      <Icon className="relative h-[18px] w-[18px]" strokeWidth={2} />
      <span className="relative hidden lg:inline">{label}</span>
    </Link>
  );
}

function MobileNavLink({
  href,
  label,
  icon: Icon,
}: {
  href: string;
  label: string;
  icon: (typeof NAV)[number]["icon"];
}) {
  const pathname = usePathname();
  const active = isActive(pathname, href);

  return (
    <Link
      href={href}
      className={cn(
        "relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
        active ? "text-ink" : "text-muted hover:text-ink",
      )}
    >
      {active ? (
        <motion.span
          layoutId="revisit-nav-active-mobile"
          transition={{ type: "spring", stiffness: 420, damping: 34 }}
          className="absolute inset-0 rounded-lg bg-white/[0.08]"
        />
      ) : null}
      <Icon className="relative h-4 w-4" />
      <span className="relative">{label}</span>
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { email, logout } = useAuth();

  return (
    <div className="flex h-dvh overflow-hidden bg-canvas">
      <aside className="hidden w-[72px] shrink-0 flex-col border-r border-line bg-surface/50 px-2.5 py-4 md:flex lg:w-[238px] lg:px-3">
        <div className="flex h-9 items-center px-1 lg:px-2">
          <Logo className="hidden lg:inline-flex" />
          <LogoMark className="lg:hidden" />
        </div>

        <nav className="mt-6 flex flex-col gap-1">
          {NAV.map((item) => (
            <DesktopNavLink key={item.href} {...item} />
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-2 border-t border-line pt-3 lg:flex-row lg:items-center lg:justify-between">
          <span
            className="hidden truncate px-2 text-xs text-muted lg:inline"
            title={email ?? undefined}
          >
            {email}
          </span>
          <IconButton
            label="Sign out"
            onClick={logout}
            className="lg:shrink-0"
          >
            <LogOut className="h-4 w-4" />
          </IconButton>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line bg-surface/60 px-4 py-3 backdrop-blur md:hidden">
          <Logo />
          <nav className="flex items-center gap-1">
            {NAV.map((item) => (
              <MobileNavLink key={item.href} {...item} />
            ))}
          </nav>
          <IconButton label="Sign out" onClick={logout}>
            <LogOut className="h-4 w-4" />
          </IconButton>
        </header>

        <main className="relative min-h-0 flex-1">
          <div className="pointer-events-none absolute -left-40 -top-40 h-80 w-80 rounded-full bg-accent/10 blur-[120px]" />
          <div className="relative h-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
