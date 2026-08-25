import { create } from "zustand";
import type { User, Role, Permission } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  roles: Role[];
  permissions: string[];
  
  // Actions
  setUser: (user: User | null) => void;
  setRoles: (roles: Role[]) => void;
  setPermissions: (permissions: string[]) => void;
  clearAuth: () => void;
  
  // Permission checks
  hasPermission: (permission: string) => boolean;
  hasRole: (roleName: string) => boolean;
  hasChatAccess: () => boolean;
  hasAgentAccess: () => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  roles: [],
  permissions: [],

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  
  setRoles: (roles) => {
    const permissionNames = roles.flatMap((r) => r.permissions?.map((p) => p.name) || []);
    set({ roles, permissions: [...new Set(permissionNames)] });
  },
  
  setPermissions: (permissions) => set({ permissions }),
  
  clearAuth: () => set({ 
    user: null, 
    isAuthenticated: false, 
    roles: [], 
    permissions: [] 
  }),

  hasPermission: (permission) => {
    const { permissions, user } = get();
    if (user?.is_superuser) return true;
    return permissions.includes(permission);
  },

  hasRole: (roleName) => {
    const { roles } = get();
    return roles.some((r) => r.name === roleName);
  },

  hasChatAccess: () => {
    return get().hasPermission("chat.access");
  },

  hasAgentAccess: () => {
    return get().hasPermission("agent.access");
  },

  isAdmin: () => {
    const { user, hasRole } = get();
    return user?.is_superuser || hasRole("SUPER_ADMIN") || hasRole("ADMIN");
  },
}));

export default useAuthStore;
