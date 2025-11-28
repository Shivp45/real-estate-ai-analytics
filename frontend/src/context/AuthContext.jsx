import React, { createContext, useEffect, useState } from "react";
import { fetchMe, loginUser, registerUser } from "../api/client";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user;
  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      setLoading(false);
      return;
    }

    fetchMe()
      .then((res) => {
        if (res.success) setUser(res.user);
        else {
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
        }
      })
      .catch(() => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogin = async (username, password) => {
    const res = await loginUser({ username, password });
    if (res.success) {
      localStorage.setItem("accessToken", res.tokens.access);
      localStorage.setItem("refreshToken", res.tokens.refresh);
      setUser(res.user);
    }
    return res;
  };

  const handleRegister = async (username, email, password, password_confirm) => {
    const res = await registerUser({ username, email, password, password_confirm });
    if (res.success) {
      localStorage.setItem("accessToken", res.tokens.access);
      localStorage.setItem("refreshToken", res.tokens.refresh);
      setUser(res.user);
    }
    return res;
  };

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, loading, login: handleLogin, register: handleRegister, logout: handleLogout }}>
      {children}
    </AuthContext.Provider>
  );
};
