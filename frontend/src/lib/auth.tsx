"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  api,
  clearSession,
  getStoredEmail,
  getToken,
  setSession,
  UNAUTHORIZED_EVENT,
} from "./api";

type Status = "loading" | "authed" | "anon";

interface AuthContextValue {
  status: Status;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;
      setEmail(getStoredEmail());
      setStatus(getToken() ? "authed" : "anon");
    });

    const onUnauthorized = () => {
      setEmail(null);
      setStatus("anon");
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => {
      active = false;
      window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    };
  }, []);

  const login = useCallback(async (nextEmail: string, password: string) => {
    const token = await api.login(nextEmail, password);
    setSession(token, nextEmail);
    setEmail(nextEmail);
    setStatus("authed");
  }, []);

  const register = useCallback(async (nextEmail: string, password: string) => {
    await api.register(nextEmail, password);
    const token = await api.login(nextEmail, password);
    setSession(token, nextEmail);
    setEmail(nextEmail);
    setStatus("authed");
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setEmail(null);
    setStatus("anon");
  }, []);

  const value = useMemo(
    () => ({ status, email, login, register, logout }),
    [status, email, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
