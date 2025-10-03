import { apiClient, authenticatedClient, setAuthToken } from "@/lib/api-client";
import type { components } from "@/types/api";

type UserCreate = components["schemas"]["UserCreate"];
type UserRead = components["schemas"]["UserRead"];
type Token = components["schemas"]["Token"];

export interface RegisterParams {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

/**
 * Register a new user
 */
export async function register(params: RegisterParams): Promise<UserRead> {
  const { data, error } = await apiClient.POST("/auth/register", {
    body: params as UserCreate,
  });

  if (error) {
    throw new Error(error.detail || "Registration failed");
  }

  return data;
}

/**
 * Login with email and password
 */
export async function login(params: LoginParams): Promise<Token> {
  const { data, error } = await apiClient.POST("/auth/login", {
    headers: {
      Authorization: `Basic ${btoa(`${params.email}:${params.password}`)}`,
    },
  });

  if (error) {
    throw new Error(error.detail || "Login failed");
  }

  // Set token for future authenticated requests
  setAuthToken(data.access_token);

  return data;
}

/**
 * Refresh access token using refresh token
 */
export async function refreshToken(refreshToken: string): Promise<Token> {
  const { data, error } = await apiClient.POST("/auth/refresh", {
    body: { refresh_token: refreshToken },
  });

  if (error) {
    throw new Error(error.detail || "Token refresh failed");
  }

  // Update token for future authenticated requests
  setAuthToken(data.access_token);

  return data;
}

/**
 * Logout the current user
 */
export async function logout(): Promise<void> {
  await authenticatedClient.POST("/auth/logout", {});
  // Note: Backend doesn't blacklist tokens yet (Phase 7)
  // For now, just clear local token
}

/**
 * Get current authenticated user info
 */
export async function getCurrentUser(): Promise<UserRead> {
  const { data, error } = await authenticatedClient.GET("/auth/me");

  if (error) {
    throw new Error(error.detail || "Failed to get current user");
  }

  return data;
}
