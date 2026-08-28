import { createContext } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastOptions {
  id?: string;
  type?: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

export interface ToastItem extends Required<Omit<ToastOptions, 'id'>> {
  id: string;
}

export interface ToastContextType {
  toasts: ToastItem[];
  showToast: (options: ToastOptions) => string;
  hideToast: (id: string) => void;
  success: (message: string, title?: string) => string;
  error: (message: string, title?: string) => string;
  warning: (message: string, title?: string) => string;
  info: (message: string, title?: string) => string;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);
