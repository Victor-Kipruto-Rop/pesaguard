"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminDocumentsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Documents"
        summary="Access statements, imports, templates, exports, and document archives."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/documents/document-center" className="secondaryBtn">Document center</Link>
          <Link href="/admin/documents/uploaded-files" className="secondaryBtn">Uploaded files</Link>
          <Link href="/admin/documents/statements" className="secondaryBtn">Statements</Link>
          <Link href="/admin/documents/templates" className="secondaryBtn">Templates</Link>
          <Link href="/admin/documents/imports" className="secondaryBtn">Imports</Link>
          <Link href="/admin/documents/exports" className="secondaryBtn">Exports</Link>
          <Link href="/admin/documents/archived-files" className="secondaryBtn">Archived files</Link>
        </div>
      </section>
    </main>
  );
}
