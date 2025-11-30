const ua = (): string => navigator.userAgent;

const isIOSDevice = (): boolean => /iPhone|iPad|iPod/i.test(ua());
const isIPadOS13 = (): boolean => navigator.maxTouchPoints > 1 && /Mac/i.test(ua());

export const isIOS = (): boolean => isIOSDevice() || isIPadOS13();
