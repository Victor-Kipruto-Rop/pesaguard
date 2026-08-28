'use client';

import { ArrowRight, Download, Globe, PackageCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function PostmanCollectionPage() {
  return (
    <AccountPageShell
      title="Postman collection"
      subtitle="Download prebuilt request collections for rapid API exploration and workflow testing."
      actions={
        <button type="button" className="buttonAccent">
          <Download size={16} /> Download JSON
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Collection packages</h2>
              <p className="muted">Ready-to-import environments for onboarding and QA validation.</p>
            </div>
            <span className="badge">Latest</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><PackageCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>PesaGuard Production</strong>
                  <span className="statusPill success">Live</span>
                </div>
                <p>Full lifecycle collection covering payments, settlements, users, and audit routes.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Globe size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Sandbox environment</strong>
                  <span className="statusPill">Test</span>
                </div>
                <p>Safe mock endpoints and sample responses for integration validation.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Included resources</h2>
              <p className="muted">Everything needed for kickoff requests and environment setup.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Download size={18} /></div>
              <div>
                <p className="infoTitle">Preconfigured variables</p>
                <p className="muted">Base URLs, auth tokens, and example IDs are ready for import.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ArrowRight size={18} /></div>
              <div>
                <p className="infoTitle">Sample sequences</p>
                <p className="muted">Test requests are grouped by workflow to reduce onboarding friction.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
