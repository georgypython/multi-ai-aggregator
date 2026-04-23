/**
 * Безопасный доступ к Telegram WebApp API.
 * Все методы являются no-op если Telegram недоступен (dev-режим).
 * Вызовы обёрнуты: в web.telegram.org (Web K) часть API недоступна или отклоняет Promise —
 * без этого в консоли «Uncaught (in promise)» и сбои инициализации.
 */

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

interface TelegramWebApp {
  initData?: string;
  initDataUnsafe?: {
    user?: {
      id?: number;
      username?: string;
      first_name?: string;
      last_name?: string;
      language_code?: string;
      photo_url?: string;
    };
    start_param?: string;
  };
  platform?: string;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  ready?: () => void | Promise<void>;
  disableVerticalSwipes?: () => void | Promise<void>;
  expand?: () => void | Promise<void>;
  SettingsButton?: { isVisible: boolean; onClick: (cb: () => void) => void };
  version?: string;
  lockOrientation?: () => void | Promise<void>;
  HapticFeedback?: {
    impactOccurred?: (style: string) => void;
    notificationOccurred?: (type: 'error' | 'success' | 'warning') => void;
  };
  openTelegramLink?: (url: string) => void | Promise<void>;
  /** Открыть URL во внешнем браузере / обработчике ОС (предпочтительно вместо window.open в Mini App). */
  openLink?: (url: string, options?: { try_instant_view?: boolean }) => void | Promise<void>;
  close?: () => void | Promise<void>;
  showAlert?: (message: string) => void | Promise<void>;
  showConfirm?: (message: string, callback: (confirmed: boolean) => void) => void | Promise<void>;
  addToHomeScreen?: () => void | Promise<void>;
}

const noop = () => {};

/** Синхронные исключения и отклонённые Promise от WebApp не рвут приложение. */
function safeTwa(label: string, fn: () => unknown): void {
  try {
    const out = fn();

    if (out != null && typeof (out as any).then === 'function') {
      Promise.resolve(out).catch((err: unknown) => {
        if (import.meta.env.DEV) {
          console.warn(`[tg:${label}]`, err);
        }
      });
    }
  } catch (err) {
    if (import.meta.env.DEV) {
      console.warn(`[tg:${label}]`, err);
    }
  }
}

/**
 * Ранний вызов WebApp.ready() — из main.tsx после загрузки telegram-web-app.js.
 * На web.telegram.org позже стабильнее появляется initData.
 */
export function initTelegramWebAppEarly(): void {
  const w = typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined;
  if (!w) return;
  safeTwa('ready', () => w.ready?.());
}

/**
 * Безопасный объект Telegram WebApp.
 * Возвращает реальный WebApp если доступен, иначе заглушки.
 */
export const tg = {
  get raw() {
    return typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined;
  },

  get isAvailable() {
    return !!this.raw;
  },

  /** Платформа клиента: webk / weba / android / ios / tdesktop / macos … */
  get platform() {
    return this.raw?.platform ?? '';
  },

  get initData() {
    return this.raw?.initData ?? '';
  },

  get initDataUnsafe() {
    return this.raw?.initDataUnsafe ?? {};
  },

  get user() {
    return this.initDataUnsafe.user ?? {};
  },

  get startParam() {
    return this.initDataUnsafe.start_param;
  },

  get version() {
    return this.raw?.version ?? '0.0';
  },

  setHeaderColor(color: string) {
    safeTwa('setHeaderColor', () => this.raw?.setHeaderColor?.(color));
  },

  setBackgroundColor(color: string) {
    safeTwa('setBackgroundColor', () => this.raw?.setBackgroundColor?.(color));
  },

  ready() {
    safeTwa('ready', () => this.raw?.ready?.());
  },

  expand() {
    safeTwa('expand', () => this.raw?.expand?.());
  },

  disableVerticalSwipes() {
    safeTwa('disableVerticalSwipes', () => this.raw?.disableVerticalSwipes?.());
  },

  lockOrientation() {
    safeTwa('lockOrientation', () => this.raw?.lockOrientation?.());
  },

  hapticImpact(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') {
    safeTwa('hapticImpact', () => this.raw?.HapticFeedback?.impactOccurred?.(style));
  },

  /** HapticFeedback.notificationOccurred — в обёртке tg раньше отсутствовал, на Web часть вызовов шла в «пустоту». */
  hapticNotification(type: 'error' | 'success' | 'warning') {
    safeTwa('hapticNotification', () =>
      this.raw?.HapticFeedback?.notificationOccurred?.(type)
    );
  },

  openTelegramLink(url: string) {
    safeTwa('openTelegramLink', () => this.raw?.openTelegramLink?.(url));
  },

  openLink(url: string, options?: { try_instant_view?: boolean }) {
    safeTwa('openLink', () => this.raw?.openLink?.(url, options));
  },

  close() {
    safeTwa('close', () => this.raw?.close?.());
  },

  showAlert(message: string) {
    safeTwa('showAlert', () => {
      if (this.raw?.showAlert) {
        return this.raw.showAlert(message);
      }
      alert(message);
    });
  },

  /** Подтверждение: в TWA через showConfirm, иначе window.confirm. */
  showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        const w = this.raw;
        if (w?.showConfirm) {
          const r = w.showConfirm(message, (ok: boolean) => resolve(!!ok));
          if (r != null && typeof (r as any).then === 'function') {
           Promise.resolve(r).catch(() => {
                resolve(window.confirm(message));
            });
          }
          return;
        }
      } catch {
        /* ignore */
      }
      resolve(window.confirm(message));
    });
  },

  addToHomeScreen() {
    safeTwa('addToHomeScreen', () => this.raw?.addToHomeScreen?.());
  },

  get SettingsButton() {
    return this.raw?.SettingsButton ?? { isVisible: false, onClick: noop };
  },
};

export default tg;
