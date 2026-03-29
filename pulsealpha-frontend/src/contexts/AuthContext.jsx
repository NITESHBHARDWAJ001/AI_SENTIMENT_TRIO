import { useMemo, useState } from "react";
import { AuthContext } from "./auth-context";
import { login, register } from "../services/authService";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("pulsealpha_user");
    return raw ? JSON.parse(raw) : null;
  });

  const [token, setToken] = useState(() => localStorage.getItem("pulsealpha_token"));

  const signin = async (payload) => {
    const result = await login(payload);
    setUser(result.user);
    setToken(result.token);
    localStorage.setItem("pulsealpha_user", JSON.stringify(result.user));
    localStorage.setItem("pulsealpha_token", result.token);
    return result;
  };

  const signup = async (payload) => {
    const result = await register(payload);
    setUser(result.user);
    setToken(result.token);
    localStorage.setItem("pulsealpha_user", JSON.stringify(result.user));
    localStorage.setItem("pulsealpha_token", result.token);
    return result;
  };

  const signout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("pulsealpha_user");
    localStorage.removeItem("pulsealpha_token");
  };

  const setUserProfile = (profile) => {
    setUser(profile);
    localStorage.setItem("pulsealpha_user", JSON.stringify(profile));
  };

  const value = useMemo(
    () => ({ user, token, isAuthenticated: Boolean(token), signin, signup, signout, setUserProfile }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
