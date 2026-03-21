export const isMac = /Mac|iPhone|iPad/.test(navigator.platform);
export const modKey = isMac ? '⌘' : 'Ctrl';
export const isModEnter = (e) => e.key === 'Enter' && (isMac ? e.metaKey : e.ctrlKey);
