"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";
import { Logo } from "@/components/logo";

function Splash() {
  return (
    <div className="grid h-dvh place-items-center bg-canvas">
      <div className="animate-pulse-soft">
        <Logo />
      </div>
    </div>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "anon") router.replace("/login");
  }, [status, router]);

  if (status !== "authed") return <Splash />;

  return <>{children}</>;
}
