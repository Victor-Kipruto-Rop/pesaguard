import Link from 'next/link';
import type { Route } from 'next';
import PageHeader from './PageHeader';

interface SectionLink {
  title: string;
  href: string;
  summary: string;
}

interface SuperAdminSectionPageProps {
  eyebrow: string;
  title: string;
  summary: string;
  links: SectionLink[];
}

export default function SuperAdminSectionPage({ eyebrow, title, summary, links }: SuperAdminSectionPageProps) {
  return (
    <main className="shell">
      <PageHeader eyebrow={eyebrow} title={title} summary={summary} />
      <section className="card">
        <div className="sectionTitle">Available modules</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginTop: 16 }}>
          {links.map((link) => (
            <Link key={link.href} href={link.href as Route} style={{ textDecoration: 'none', color: 'inherit' }}>
              <article className="card" style={{ height: '100%', border: '1px solid rgba(255,255,255,0.08)', transition: 'transform 0.2s ease, border-color 0.2s ease' }}>
                <div style={{ fontWeight: 700, marginBottom: 8 }}>{link.title}</div>
                <p className="muted" style={{ margin: 0, fontSize: 13 }}>{link.summary}</p>
              </article>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
