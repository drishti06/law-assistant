"use server";

import { cookies } from "next/headers";

export async function getAuthToken(): Promise<string | null> {
  const cookieStore = cookies();
  return cookieStore.get("access_token")?.value ?? null;
}

export async function isAuthenticated(): Promise<boolean> {
  const token = await getAuthToken();
  return !!token;
}
