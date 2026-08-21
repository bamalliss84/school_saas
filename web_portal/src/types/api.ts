export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  errors: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
