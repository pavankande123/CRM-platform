import { apiRequest } from './apiClient';
import type { StandardResponse, User } from '../types';

export interface CreateUserPayload {
  email: string;
  full_name: string;
  password: string;
  role_name?: string;
}

export const userService = {
  async getUsers(): Promise<User[]> {
    const res = await apiRequest<StandardResponse<User[]>>('/users');
    return res.data;
  },

  async createUser(payload: CreateUserPayload): Promise<User> {
    const res = await apiRequest<StandardResponse<User>>('/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};
