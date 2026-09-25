import { apiRequest, TOKEN_STORAGE_KEY, REFRESH_TOKEN_STORAGE_KEY } from './apiClient';
import type { StandardResponse, TokenResponse, User, Organization } from '../types';

export interface LoginPayload {
  email: string;
  password: string;
  organization_slug?: string;
}

export interface RegisterPayload {
  organization_name: string;
  full_name: string;
  email: string;
  password: string;
}

export interface CurrentUserResponse {
  user: User;
  organization: Organization;
  permissions: string[];
}

export const authService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const res = await apiRequest<StandardResponse<TokenResponse>>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
      skipAuth: true,
    });
    localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token);
    localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, res.data.refresh_token);
    return res.data;
  },

  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const res = await apiRequest<StandardResponse<TokenResponse>>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
      skipAuth: true,
    });
    localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token);
    localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, res.data.refresh_token);
    return res.data;
  },

  async getMe(): Promise<CurrentUserResponse> {
    const res = await apiRequest<StandardResponse<CurrentUserResponse>>('/auth/me');
    return res.data;
  },

  async logout(): Promise<void> {
    try {
      await apiRequest<StandardResponse<{ logged_out: boolean }>>('/auth/logout', {
        method: 'POST',
      });
    } finally {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
    }
  },
};
