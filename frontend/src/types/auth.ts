export interface Permission {
  name: string;
  codename: string;
  description?: string;
}

export interface Group {
  name: string;
  description?: string;
  permissions: Permission[];
}

export interface UserInfo {
  id: string;
  email: string;
  groups: Group[];
}

export interface LoginResponse {
  token_type: string;
  user: UserInfo;
}

export interface ForgotPasswordResponse {
  success: boolean;
  message: string;
}

export interface VerifyResetTokenResponse {
  valid: boolean;
  message: string;
}

export interface ResetPasswordResponse {
  success: boolean;
  message: string;
}
