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
  access_token: string;
  token_type: string;
  user: UserInfo;
}
