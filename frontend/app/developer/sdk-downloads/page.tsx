'use client';

import { ArrowRight, Download, FileCode2, Globe, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function SdkDownloadsPage() {
  return (
    <AccountPageShell
      title="SDK downloads"
      subtitle="Pull the client libraries, samples, and tooling needed to ship quickly with supported languages."
      actions={
        <button type="button" className="buttonAccent">
          <Download size={16} /> Download all
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Available SDKs</h2>
              <p className="muted">Official libraries maintained to match the live platform API.</p>
            </div>
            <span className="badge">Current</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><FileCode2 size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Node.js</strong>
                  <span className="statusPill success">Latest</span>
                </div>
                <p>Production-ready client for request signing, retries, and payment workflows.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Globe size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Python</strong>
                  <span className="statusPill">Stable</span>
                </div>
                <p>Strong support for reconciliation scripts, data extraction, and automation.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><ShieldCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Go</strong>
                  <span className="statusPill success">Maintained</span>
                </div>
                <p>Optimized for internal services and event-driven processing tooling.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Release notes</h2>
              <p className="muted">Version-specific improvements and compatibility updates.</p>
            </div>
          </div>

          <div className="placeholderPanel">
            <div className="placeholderHeader">Current release summary</div>
            <div className="placeholderRows">
              <div className="placeholderRow" />
              <div className="placeholderRow" />
              <div className="placeholderRow" />
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> SDKs are validated against the current production contract
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
