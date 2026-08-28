'use client';

import { History, FileText } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';

export default function NotificationHistoryPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Notification History" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent deliveries</h2>
              <p className="muted">Searchable audit trail for notification deliveries and failures.</p>
            </div>
            <span className="badge">30 days</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><History size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>#DEL-30421</strong>
                  <span className="statusPill success">Delivered</span>
                </div>
                <p>Email delivered to recipient@example.com (200 OK)</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Export</h2>
              <p className="muted">Export delivery logs for compliance and analytics.</p>
            </div>
          </div>

          <div className="optionList">
            <a className="optionCard">
              <div>
                <span className="optionTitle">Export recent 30 days</span>
                <p className="muted">Download CSV formatted delivery logs for analysis.</p>
              </div>
              <FileText size={18} />
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
