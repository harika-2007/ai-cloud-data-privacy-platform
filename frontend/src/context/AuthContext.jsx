import React, { createContext, useState, useCallback, useEffect, useMemo } from 'react';
import { authService } from '../services/authService';
import { TOKEN_KEYS } from '../utils/constants';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isAuthenticated = !!user;

  const storeTokens = useCallback((accessToken, refreshToken) => {
    localStorage.setItem(TOKEN_KEYS.ACCESS, accessToken);
    if (refreshToken) {
      localStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken);
    }
  }, []);

  const clearTokens = useCallback(() => {
    localStorage.removeItem(TOKEN_KEYS.ACCESS);
    localStorage.removeItem(TOKEN_KEYS.REFRESH);
    localStorage.removeItem('user');
  }, []);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEYS.ACCESS);
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const userData = await authService.getMe();
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (err) {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [clearTokens]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    setError(null);
  }, [clearTokens]);

  const updateUser = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const token = localStorage.getItem(TOKEN_KEYS.ACCESS);

  const contextValue = useMemo(
    () => ({
      user,
      token,
      loading,
      error,
      isAuthenticated,
      logout,
      updateUser,
      clearError,
      fetchUser,
    }),
    [user, token, loading, error, isAuthenticated, logout, updateUser, clearError, fetchUser]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;
