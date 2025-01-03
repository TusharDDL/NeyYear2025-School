import axiosInstance from '@/lib/axios';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  phone: string;
  address: string;
  profile_picture: string | null;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RegistrationData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  role: string;
  phone: string;
  address: string;
}

export interface PasswordChangeData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetRequestData {
  email: string;
}

export interface PasswordResetConfirmData {
  token: string;
  password: string;
  confirm_password: string;
}

const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await axiosInstance.post('/api/v1/accounts/login/', credentials);
    return response.data;
  },

  async register(data: RegistrationData): Promise<User> {
    const response = await axiosInstance.post('/api/v1/accounts/users/', data);
    return response.data;
  },

  async refreshToken(refresh: string): Promise<{ access: string }> {
    const response = await axiosInstance.post('/api/v1/accounts/token/refresh/', { refresh });
    return response.data;
  },

  async changePassword(data: PasswordChangeData): Promise<void> {
    await axiosInstance.post('/api/v1/accounts/users/change-password/', data);
  },

  async resetPasswordRequest(data: PasswordResetRequestData): Promise<void> {
    await axiosInstance.post('/api/v1/accounts/users/reset-password-request/', data);
  },

  async resetPasswordConfirm(data: PasswordResetConfirmData): Promise<void> {
    await axiosInstance.post('/api/v1/accounts/users/reset-password-confirm/', data);
  },

  async getProfile(): Promise<User> {
    const response = await axiosInstance.get('/api/v1/accounts/users/me/');
    return response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await axiosInstance.put('/api/v1/accounts/users/update-profile/', data);
    return response.data;
  },
};

export default authService;
