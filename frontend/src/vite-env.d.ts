/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the chat backend, e.g. "/api". Empty → built-in mock flows. */
  readonly VITE_CHAT_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
