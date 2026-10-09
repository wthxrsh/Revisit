"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";
import { Logo } from "@/components/logo";

export default function Home() {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authed") router.replace("/ask");
    else if (status === "anon") router.replace("/login");
  }, [status, router]);

  return (
    <div className="grid h-dvh place-items-center bg-canvas">
      <div className="animate-pulse-soft">
        <Logo />
      </div>
    </div>
  );
}
