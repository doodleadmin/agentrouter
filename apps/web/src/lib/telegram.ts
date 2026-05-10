type TelegramWebApp = {
  ready?: () => void;
  expand?: () => void;
  initData?: string;
  initDataUnsafe?: Record<string, unknown>;
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export interface TelegramContext {
  isTelegramWebApp: boolean;
  initData: string | null;
  initDataUnsafe: Record<string, unknown>;
}

export function getTelegramContext(): TelegramContext {
  const webApp = window.Telegram?.WebApp;

  if (!webApp) {
    return {
      isTelegramWebApp: false,
      initData: null,
      initDataUnsafe: {},
    };
  }

  webApp.ready?.();
  webApp.expand?.();

  return {
    isTelegramWebApp: true,
    initData: webApp.initData ?? null,
    initDataUnsafe: webApp.initDataUnsafe ?? {},
  };
}
