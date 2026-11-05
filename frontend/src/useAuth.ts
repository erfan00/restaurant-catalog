import { useContext } from "react";

import { AuthContext } from "./auth-context-base";
import type { AuthState } from "./auth-context-base";

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
