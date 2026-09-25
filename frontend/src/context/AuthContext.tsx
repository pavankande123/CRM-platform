import React, { createContext, useContext, useEffect, useState } from 'react';
import type { User, Organization } from '../types';
import { authService, type LoginPayload, type RegisterPayload } from '../services/authService';
import { TOKEN_STORAGE_KEY } from '../services/apiClient';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  permissions: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setUser(null);
      setOrganization(null);
      setPermissions([]);
      setIsLoading(false);
      return;
    }

    try {
      const data = await authService.getMe();
      setUser(data.user);
      setOrganization(data.organization);
      setPermissions(data.permissions);
    } catch {
      setUser(null);
      setOrganization(null);
      setPermissions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const login = async (payload: LoginPayload) => {
    setIsLoading(true);
    try {
      const res = await authService.login(payload);
      setUser(res.user);
      setOrganization(res.organization);
      // Fetch full profile to get permissions
      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    try {
      const res = await authService.register(payload);
      setUser(res.user);
      setOrganization(res.organization);
      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setOrganization(null);
      setPermissions([]);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        permissions,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile: fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
