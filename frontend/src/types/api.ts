export interface User {
  id: number;
  username: string;
  email?: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface LoginResponse {
  data: {
    access_token: string;
    user: User;
  };
}

export interface RegisterResponse {
  data: {
    id: number;
    email: string;
    username: string;
    first_name: string;
    last_name: string;
    role: string;
  };
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'teacher' | 'parent' | 'librarian';
}

export interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

export interface StudentFormData {
  admission_number: string;
  roll_number: string;
  class_name: string;
  section: string;
  date_of_birth: string;
  gender: 'male' | 'female' | 'other';
  blood_group?: string;
  address?: string;
  phone?: string;
  parent_name: string;
  parent_phone: string;
  parent_email: string;
  emergency_contact?: string;
  medical_conditions?: string;
}
