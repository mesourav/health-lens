export class ChatServiceError extends Error {
  readonly status: number | undefined;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ChatServiceError';
    this.status = status;
  }
}
