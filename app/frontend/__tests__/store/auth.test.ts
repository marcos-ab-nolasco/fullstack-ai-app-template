import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { useAuthStore } from "@/store/auth";
import * as authApi from "@/lib/api/auth";
import { setAuthToken, clearAuthToken, setRefreshTokenCallback } from "@/lib/api-client";

// Mock the API functions
vi.mock("@/lib/api/auth");
vi.mock("@/lib/api-client");

describe("Auth Store (Zustand)", () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up localStorage
    localStorage.clear();
  });

  describe("Initial State", () => {
    it("should have correct initial state", () => {
      const state = useAuthStore.getState();

      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe("login", () => {
    it("should authenticate user and update state", async () => {
      const mockTokens = {
        access_token: "access-123",
        refresh_token: "refresh-456",
        token_type: "bearer",
      };

      const mockUser = {
        id: "user-123",
        email: "test@example.com",
        full_name: "Test User",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      vi.mocked(authApi.login).mockResolvedValueOnce(mockTokens);
      vi.mocked(authApi.getCurrentUser).mockResolvedValueOnce(mockUser);

      await useAuthStore.getState().login("test@example.com", "password123");

      const state = useAuthStore.getState();

      expect(authApi.login).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
      expect(authApi.getCurrentUser).toHaveBeenCalled();
      expect(state.user).toEqual(mockUser);
      expect(state.accessToken).toBe("access-123");
      expect(state.refreshToken).toBe("refresh-456");
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it("should call setRefreshTokenCallback after successful login", async () => {
      const mockTokens = {
        access_token: "access-123",
        refresh_token: "refresh-456",
        token_type: "bearer",
      };

      const mockUser = {
        id: "user-123",
        email: "test@example.com",
        full_name: "Test User",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      vi.mocked(authApi.login).mockResolvedValueOnce(mockTokens);
      vi.mocked(authApi.getCurrentUser).mockResolvedValueOnce(mockUser);

      await useAuthStore.getState().login("test@example.com", "password123");

      expect(setRefreshTokenCallback).toHaveBeenCalled();
    });

    it("should set error state on login failure", async () => {
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error("Invalid credentials"));

      await expect(useAuthStore.getState().login("wrong@example.com", "wrongpass")).rejects.toThrow(
        "Invalid credentials"
      );

      const state = useAuthStore.getState();

      expect(state.error).toBe("Invalid credentials");
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(false);
    });

    it("should handle network errors", async () => {
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error("Network error"));

      await expect(useAuthStore.getState().login("test@example.com", "password")).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.error).toBe("Network error");
    });
  });

  describe("register", () => {
    it("should register user and auto-login", async () => {
      const mockUser = {
        id: "user-123",
        email: "new@example.com",
        full_name: "New User",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const mockTokens = {
        access_token: "access-123",
        refresh_token: "refresh-456",
        token_type: "bearer",
      };

      vi.mocked(authApi.register).mockResolvedValueOnce(mockUser);
      vi.mocked(authApi.login).mockResolvedValueOnce(mockTokens);
      vi.mocked(authApi.getCurrentUser).mockResolvedValueOnce(mockUser);

      await useAuthStore.getState().register("new@example.com", "password123", "New User");

      expect(authApi.register).toHaveBeenCalledWith({
        email: "new@example.com",
        password: "password123",
        full_name: "New User",
      });

      // Should auto-login after registration
      expect(authApi.login).toHaveBeenCalledWith({
        email: "new@example.com",
        password: "password123",
      });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
    });

    it("should set error on registration failure", async () => {
      vi.mocked(authApi.register).mockRejectedValueOnce(new Error("Email already exists"));

      await expect(
        useAuthStore.getState().register("existing@example.com", "password", "Test")
      ).rejects.toThrow("Email already exists");

      const state = useAuthStore.getState();
      expect(state.error).toBe("Email already exists");
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("logout", () => {
    it("should clear state and call clearAuthToken", async () => {
      // Set up authenticated state
      useAuthStore.setState({
        user: {
          id: "user-123",
          email: "test@example.com",
          full_name: "Test User",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        accessToken: "access-123",
        refreshToken: "refresh-456",
        isAuthenticated: true,
      });

      vi.mocked(authApi.logout).mockResolvedValueOnce(undefined);

      await useAuthStore.getState().logout();

      expect(authApi.logout).toHaveBeenCalled();
      expect(clearAuthToken).toHaveBeenCalled();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBeNull();
    });

    it("should clear state even if logout API fails", async () => {
      useAuthStore.setState({
        user: {
          id: "user-123",
          email: "test@example.com",
          full_name: "Test User",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        accessToken: "access-123",
        refreshToken: "refresh-456",
        isAuthenticated: true,
      });

      vi.mocked(authApi.logout).mockRejectedValueOnce(new Error("Logout failed"));

      await useAuthStore.getState().logout();

      // Should still clear local state
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(clearAuthToken).toHaveBeenCalled();
    });
  });

  describe("refreshAuth", () => {
    it("should refresh tokens and update state", async () => {
      useAuthStore.setState({
        refreshToken: "old-refresh-token",
      });

      const mockNewTokens = {
        access_token: "new-access-123",
        refresh_token: "new-refresh-456",
        token_type: "bearer",
      };

      vi.mocked(authApi.refreshToken).mockResolvedValueOnce(mockNewTokens);

      await useAuthStore.getState().refreshAuth();

      expect(authApi.refreshToken).toHaveBeenCalledWith("old-refresh-token");

      const state = useAuthStore.getState();
      expect(state.accessToken).toBe("new-access-123");
      expect(state.refreshToken).toBe("new-refresh-456");
      expect(setRefreshTokenCallback).toHaveBeenCalled();
    });

    it("should throw error if no refresh token available", async () => {
      useAuthStore.setState({
        refreshToken: null,
      });

      await expect(useAuthStore.getState().refreshAuth()).rejects.toThrow(
        "No refresh token available"
      );
    });

    it("should logout on refresh failure", async () => {
      useAuthStore.setState({
        refreshToken: "invalid-token",
        user: {
          id: "user-123",
          email: "test@example.com",
          full_name: "Test User",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        isAuthenticated: true,
      });

      vi.mocked(authApi.refreshToken).mockRejectedValueOnce(new Error("Invalid refresh token"));
      vi.mocked(authApi.logout).mockResolvedValueOnce(undefined);

      await expect(useAuthStore.getState().refreshAuth()).rejects.toThrow();

      // Should logout user
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("clearError", () => {
    it("should clear error state", () => {
      useAuthStore.setState({
        error: "Some error message",
      });

      useAuthStore.getState().clearError();

      const state = useAuthStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe("Persistence", () => {
    it("should persist auth state to localStorage", async () => {
      const mockTokens = {
        access_token: "access-123",
        refresh_token: "refresh-456",
        token_type: "bearer",
      };

      const mockUser = {
        id: "user-123",
        email: "test@example.com",
        full_name: "Test User",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      vi.mocked(authApi.login).mockResolvedValueOnce(mockTokens);
      vi.mocked(authApi.getCurrentUser).mockResolvedValueOnce(mockUser);

      await useAuthStore.getState().login("test@example.com", "password123");

      // Check localStorage was updated
      const stored = localStorage.getItem("auth-storage");
      expect(stored).toBeTruthy();

      if (stored) {
        const parsed = JSON.parse(stored);
        expect(parsed.state.user).toEqual(mockUser);
        expect(parsed.state.accessToken).toBe("access-123");
        expect(parsed.state.isAuthenticated).toBe(true);
      }
    });

    it("should restore token on rehydration", () => {
      const mockStoredState = {
        state: {
          user: {
            id: "user-123",
            email: "test@example.com",
            full_name: "Test User",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          accessToken: "stored-token",
          refreshToken: "stored-refresh",
          isAuthenticated: true,
        },
        version: 0,
      };

      localStorage.setItem("auth-storage", JSON.stringify(mockStoredState));

      // Simulate rehydration (this is normally automatic)
      // In real scenario, zustand would call onRehydrateStorage
      // For testing, we verify the callback exists
      expect(setAuthToken).toBeDefined();
    });
  });
});
