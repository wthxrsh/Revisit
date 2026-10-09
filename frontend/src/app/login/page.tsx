"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Eye, EyeOff, Lock, Mail, Sparkles } from "lucide-react";

import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { Button, Field, Input } from "@/components/ui";
import { Logo } from "@/components/logo";
import { useToast } from "@/components/toast";

type Mode = "login" | "register";

const HIGHLIGHTS = [
  "Capture notes and PDFs in one calm workspace.",
  "Ask questions and get answers grounded only in your documents.",
  "Every answer cites the exact passage it came from.",
];

export default function LoginPage() {
  const { status, login, register } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authed") router.replace("/ask");
  }, [status, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting) return;

    if (mode === "register" && password.length < 8) {
      toast("Password must be at least 8 characters.", "error");
      return;
    }

    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email.trim(), password);
        toast("Welcome back to Revisit.", "success");
      } else {
        await register(email.trim(), password);
        toast("Your Revisit account is ready.", "success");
      }
      router.replace("/ask");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Something went wrong.";
      toast(message, "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh overflow-hidden bg-canvas lg:grid-cols-2">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.15]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, #ffffff55 1px, transparent 0)",
          backgroundSize: "38px 38px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 0%, black, transparent)",
        }}
      />
      <div className="pointer-events-none absolute -left-32 top-[-10%] h-[26rem] w-[26rem] animate-aurora rounded-full bg-accent/25 blur-[130px]" />
      <div className="pointer-events-none absolute right-[-10%] bottom-[-15%] h-[24rem] w-[24rem] animate-aurora rounded-full bg-accent-2/20 blur-[130px] [animation-delay:-6s]" />

      <section className="relative hidden flex-col justify-between p-12 lg:flex">
        <Logo />
        <div className="max-w-md space-y-6">
          <motion.h1
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl font-semibold leading-tight tracking-tight"
          >
            Your second brain,{" "}
            <span className="text-gradient">revisited.</span>
          </motion.h1>
          <motion.ul
            initial="hidden"
            animate="show"
            variants={{
              hidden: {},
              show: { transition: { staggerChildren: 0.09, delayChildren: 0.15 } },
            }}
            className="space-y-3"
          >
            {HIGHLIGHTS.map((item) => (
              <motion.li
                key={item}
                variants={{
                  hidden: { opacity: 0, x: -10 },
                  show: { opacity: 1, x: 0 },
                }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="flex items-start gap-3 text-sm text-muted"
              >
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                {item}
              </motion.li>
            ))}
          </motion.ul>
        </div>
        <p className="text-xs text-muted/70">
          Notes · Documents · Grounded answers
        </p>
      </section>

      <section className="relative flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <div className="mb-6 flex rounded-xl border border-line bg-white/[0.03] p-1">
            {(["login", "register"] as Mode[]).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setMode(option)}
                className="relative flex-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
              >
                {mode === option ? (
                  <motion.span
                    layoutId="revisit-auth-tab"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    className="absolute inset-0 rounded-lg bg-white/[0.08] ring-1 ring-inset ring-white/[0.06]"
                  />
                ) : null}
                <span
                  className={
                    mode === option
                      ? "relative text-ink"
                      : "relative text-muted"
                  }
                >
                  {option === "login" ? "Sign in" : "Create account"}
                </span>
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Email">
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <Input
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="pl-9"
                />
              </div>
            </Field>

            <Field
              label="Password"
              hint={mode === "register" ? "At least 8 characters." : undefined}
            >
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <Input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="pl-9 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-muted transition-colors hover:text-ink"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </Field>

            <Button
              type="submit"
              variant="primary"
              loading={submitting}
              className="w-full"
            >
              <AnimatePresence mode="wait" initial={false}>
                <motion.span
                  key={mode}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18 }}
                  className="inline-flex items-center gap-2"
                >
                  {mode === "login" ? "Sign in" : "Create account"}
                  <ArrowRight className="h-4 w-4" />
                </motion.span>
              </AnimatePresence>
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-muted">
            {mode === "login"
              ? "New here? Switch to Create account."
              : "Already have an account? Switch to Sign in."}
          </p>
        </div>
      </section>
    </div>
  );
}
