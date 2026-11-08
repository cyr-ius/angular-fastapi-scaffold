export interface User {
  id: number;
  username: string;
  is_admin: boolean;
}

export interface Health {
  status: string;
  app: string;
  version: string;
}
