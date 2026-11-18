/** Typed, validated access to build-time environment variables. Import this, not import.meta.env. */
export const env = {
  chatApiUrl: import.meta.env.VITE_CHAT_API_URL?.trim() || undefined,
  isDev: import.meta.env.DEV,
} as const;
