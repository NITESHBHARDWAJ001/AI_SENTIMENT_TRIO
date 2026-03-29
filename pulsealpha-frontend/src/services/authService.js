import { apiClient } from "./apiClient";

export async function login(payload) {
  const { data } = await apiClient.post("/api/login", payload);
  return data;
}

export async function register(payload) {
  const { data } = await apiClient.post("/api/register", payload);
  return data;
}
