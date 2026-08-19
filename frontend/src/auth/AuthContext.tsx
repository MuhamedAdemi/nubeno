import { createContext, useContext, useState, type ReactNode } from "react";
import { api } from "../api/client";

interface AuthUser {
  username: string;
  is_admin: boolean;
  initials: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "nubeno_token";
const USER_KEY = "nubeno_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });

  async function login(username: string, password: string) {
    const res = await api.login(username, password);
    localStorage.setItem(TOKEN_KEY, res.token);
    const authUser = { username: res.username, is_admin: res.is_admin, initials: res.initials };
    localStorage.setItem(USER_KEY, JSON.stringify(authUser));
    setUser(authUser);
  }

  function logout() {
    api.logout().catch(() => undefined);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
