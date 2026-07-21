'use client';

import { useEffect, useState } from 'react';
import LoadingState from './LoadingState';

interface MarkdownDocProps {
  src: string;
}

function renderMarkdown(text: string): string {
  return text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])/gm, (line) => (line.trim() ? `<p>${line}</p>` : ''));
}

export default function MarkdownDoc({ src }: MarkdownDocProps) {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    void fetch(src)
      .then((r) => (r.ok ? r.text() : Promise.reject()))
      .then(setContent)
      .catch(() => setError(true));
  }, [src]);

  if (error) {
    return <div className="emptyState">Document could not be loaded. Check the file path or try again.</div>;
  }
  if (!content) return <LoadingState message="Loading document…" />;

  return (
    <article
      className="markdownDoc"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}
