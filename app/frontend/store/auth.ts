import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { components } from "@/types/api";
import * as authApi from "@/lib/api/auth";
import { setAuthToken, clearAuthToken, setRefreshTokenCallback } from "@/lib/api-client";

type UserRead = components["schemas"]["UserRead"];
type Token = components["schemas"]["Token"];

interface AuthState {
  // State
  user: UserRead | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authApi.login({ email, password });
          const user = await authApi.getCurrentUser();

          set({
            user,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : "Login failed";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Register action
      register: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register({ email, password, full_name: fullName });
          // After registration, automatically log in
          await get().login(email, password);
        } catch (error) {
          const message = error instanceof Error ? error.message : "Registration failed";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        try {
          await authApi.logout();
        } catch (error) {
          console.error("Logout error:", error);
        } finally {
          clearAuthToken();
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      // Refresh token action
      refreshAuth: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        try {
          const tokens = await authApi.refreshToken(refreshToken);
          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
          });
        } catch (error) {
          // If refresh fails, logout
          await get().logout();
          throw error;
        }
      },

      // Clear error action
      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Restore auth token when store rehydrates from localStorage
        if (state?.accessToken) {
          setAuthToken(state.accessToken);
          // Register refresh callback for auto-refresh on 401
          setRefreshTokenCallback(async () => {
            await useAuthStore.getState().refreshAuth();
          });
        }
      },
    }
  )
);
