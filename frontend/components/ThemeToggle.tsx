'use client';

import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const saved = window.localStorage.getItem('pesaguard.theme') as 'dark' | 'light' | null;
    const initial = saved || 'dark';
    setTheme(initial);
    document.documentElement.setAttribute('data-theme', initial);
  }, []);

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    window.localStorage.setItem('pesaguard.theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return <button onClick={toggle} className="themeToggle">{theme === 'dark' ? '☀️ Light' : '🌙 Dark'}</button>;
}
