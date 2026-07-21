const USER_ID_KEY = 'pesaguard.user_id';

export function getUserId(): string {
  if (typeof window === 'undefined') {
    return 'anonymous';
  }

  const existing = window.localStorage.getItem(USER_ID_KEY);
  if (existing) {
    return existing;
  }

  const generated = `user-${crypto.randomUUID().slice(0, 8)}`;
  window.localStorage.setItem(USER_ID_KEY, generated);
  return generated;
}
