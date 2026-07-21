'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import LoadingState from '../../../components/LoadingState';

export default function PrivacyPage() {
  const [content, setContent] = useState('');

  useEffect(() => {
    void fetch('/assets/privacy-policy.txt').then((r) => r.text()).then(setContent);
  }, []);

  return (
    <main className="publicMain">
      <PageHeader eyebrow="Legal" title="Privacy Policy" summary="How customer and payer data is collected, used, retained, and deleted." />
      <section className="card">
        {!content ? <LoadingState /> : <pre className="mono" style={{ whiteSpace: 'pre-wrap' }}>{content}</pre>}
      </section>
    </main>
  );
}
