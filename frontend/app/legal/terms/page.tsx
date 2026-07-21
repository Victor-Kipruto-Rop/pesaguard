'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import LoadingState from '../../../components/LoadingState';

export default function TermsPage() {
  const [content, setContent] = useState('');

  useEffect(() => {
    void fetch('/assets/terms-of-service.txt').then((r) => r.text()).then(setContent);
  }, []);

  return (
    <main className="publicMain">
      <PageHeader eyebrow="Legal" title="Terms of Service" summary="Service boundaries, customer responsibilities, and support commitments." />
      <section className="card">
        {!content ? <LoadingState /> : <pre className="mono" style={{ whiteSpace: 'pre-wrap' }}>{content}</pre>}
      </section>
    </main>
  );
}
