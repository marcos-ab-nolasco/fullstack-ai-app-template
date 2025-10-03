import createClient from "openapi-fetch";
import type { paths } from "@/types/api";

const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = createClient<paths>({ baseUrl });

/**
 * API client with authentication token injection
 * Usage: import { authenticatedClient } from '@/lib/api-client'
 */
export const authenticatedClient = createClient<paths>({ baseUrl });

/**
 * Set the authentication token for all authenticated requests
 */
export function setAuthToken(token: string | null) {
  if (token) {
    authenticatedClient.use({
      onRequest({ request }) {
        request.headers.set("Authorization", `Bearer ${token}`);
        return request;
      },
    });
  }
}

/**
 * Clear the authentication token
 */
export function clearAuthToken() {
  // Create a new client instance without auth headers
  Object.assign(authenticatedClient, createClient<paths>({ baseUrl }));
}
