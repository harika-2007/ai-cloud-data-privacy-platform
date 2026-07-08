import React, { createContext, useState, useCallback, useEffect, useMemo } from 'react';
import toast from 'react-hot-toast';
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

  const login = useCallback(async (email, password) => {
    setError(null);
    setLoading(true);

    try {
      const data = await authService.login(email, password);
      const tokens = data;

      const accessToken = tokens.access_token;
      const refreshToken = tokens.refresh_token;

      if (!accessToken) {
        throw new Error('No access token received');
      }

      storeTokens(accessToken, refreshToken);

      const userData = await authService.getMe();
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));

      toast.success('Login successful');
      return userData;
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Login failed. Please check your credentials.';
      setError(message);
      toast.error(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [storeTokens]);

  const register = useCallback(async (name, email, password) => {
    setError(null);
    setLoading(true);

    try {
      const data = await authService.register(name, email, password);
      const accessToken = data.access_token;
      const refreshToken = data.refresh_token;

      if (accessToken) {
        storeTokens(accessToken, refreshToken);

        const userData = await authService.getMe();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      }

      toast.success('Registration successful');
      return data;
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Registration failed. Please try again.';
      setError(message);
      toast.error(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [storeTokens]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    setError(null);
    toast.success('Logged out successfully');
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
      login,
      register,
      logout,
      updateUser,
      clearError,
      fetchUser,
    }),
    [user, token, loading, error, isAuthenticated, login, register, logout, updateUser, clearError, fetchUser]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;
