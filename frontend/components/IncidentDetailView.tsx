'use client';

import { useState } from 'react';

interface Discrepancy {
  id: string;
  trans_id: string;
  anomaly_type: string;
  status: string;
  severity: string;
  resolved: boolean;
  tenant_id?: string;
  assignee?: string;
  notes?: string;
  timeline?: Array<{ ts: string; event: string; message: string }>;
  detected_at: string;
  sla_status?: string;
  sla_remaining_minutes?: number | null;
}

interface IncidentDetailViewProps {
  incident: Discrepancy;
  onSaveNote: (note: string) => void;
  onAssign: (assignee: string) => void;
}

export default function IncidentDetailView({ incident, onSaveNote, onAssign }: IncidentDetailViewProps) {
  const [noteDraft, setNoteDraft] = useState('');
  const [assigneeDraft, setAssigneeDraft] = useState('');
  const [expandedSection, setExpandedSection] = useState<string | null>('timeline');

  const handleSaveNote = () => {
    if (noteDraft.trim()) {
      onSaveNote(noteDraft.trim());
      setNoteDraft('');
    }
  };

  const handleAssign = () => {
    if (assigneeDraft.trim()) {
      onAssign(assigneeDraft.trim());
      setAssigneeDraft('');
    }
  };

  const SectionHeader = ({ title, id }: { title: string; id: string }) => (
    <div
      className="detailSectionHeader"
      onClick={() => setExpandedSection(expandedSection === id ? null : id)}
    >
      <strong>{title}</strong>
      <span className="toggleIcon">{expandedSection === id ? '▼' : '▶'}</span>
    </div>
  );

  return (
    <div className="incidentDetailPanel">
      <div className="detailHeader">
        <div>
          <h3 className="detailTitle">Transaction {incident.trans_id}</h3>
          <p className="detailMeta">{incident.detected_at}</p>
        </div>
        <div className={`statusBadge ${incident.resolved ? 'resolved' : 'open'}`}>
          {incident.resolved ? 'Resolved' : 'Open'}
        </div>
      </div>

      <div className="detailGrid">
        <div className="detailRow">
          <span>Anomaly Type</span>
          <strong>{incident.anomaly_type}</strong>
        </div>
        <div className="detailRow">
          <span>Status</span>
          <span className={`pill ${incident.severity === 'critical' ? 'danger' : incident.severity === 'warning' ? 'warning' : 'ok'}`}>
            {incident.status}
          </span>
        </div>
        <div className="detailRow">
          <span>Severity</span>
          <span className={`pill ${incident.severity === 'critical' ? 'danger' : incident.severity === 'warning' ? 'warning' : 'ok'}`}>
            {incident.severity}
          </span>
        </div>
        <div className="detailRow">
          <span>SLA Status</span>
          <strong>
            {incident.severity === 'critical'
              ? `${incident.sla_status || 'on_track'} • ${incident.sla_remaining_minutes ?? 'n/a'}m`
              : 'Not applicable'}
          </strong>
        </div>
        <div className="detailRow">
          <span>Tenant</span>
          <strong>{incident.tenant_id || 'unknown'}</strong>
        </div>
        <div className="detailRow">
          <span>Assigned To</span>
          <strong>{incident.assignee || 'Unassigned'}</strong>
        </div>
      </div>

      <div className="detailSections">
        {expandedSection === 'timeline' && (
          <div className="detailSection">
            <SectionHeader title="Activity Timeline" id="timeline" />
            {expandedSection === 'timeline' && (
              <div className="timelineContainer">
                {(incident.timeline || []).length > 0 ? (
                  (incident.timeline || []).map((entry, index) => (
                    <div key={`${entry.ts}-${index}`} className="timelineEntry">
                      <div className="timelineDot"></div>
                      <div className="timelineContent">
                        <strong className="timelineEvent">{entry.event}</strong>
                        <p className="timelineMessage">{entry.message}</p>
                        <span className="timelineTime">{entry.ts}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="emptyState">No activity yet</div>
                )}
              </div>
            )}
          </div>
        )}

        {expandedSection === 'notes' && (
          <div className="detailSection">
            <SectionHeader title="Operator Notes" id="notes" />
            {expandedSection === 'notes' && (
              <div className="notesArea">
                <textarea
                  value={noteDraft}
                  onChange={(e) => setNoteDraft(e.target.value)}
                  placeholder="Add an update, resolution note, or handoff message for the next shift..."
                  className="noteInput"
                />
                <button className="primaryBtn" onClick={handleSaveNote}>
                  Save note
                </button>
                {incident.notes && (
                  <div className="notesHistory">
                    <div className="notesLabel">Previous notes:</div>
                    <div className="notesList">{incident.notes}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {expandedSection === 'assignment' && (
          <div className="detailSection">
            <SectionHeader title="Assignment & Routing" id="assignment" />
            {expandedSection === 'assignment' && (
              <div className="assignmentArea">
                <div className="assignmentInput">
                  <input
                    value={assigneeDraft}
                    onChange={(e) => setAssigneeDraft(e.target.value)}
                    placeholder="Assign an operator (e.g., alice@team.io)"
                    className="textInput"
                  />
                  <button className="primaryBtn" onClick={handleAssign}>
                    Assign
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="detailFooterTabs">
        <button
          className={`tabButton ${expandedSection === 'timeline' ? 'active' : ''}`}
          onClick={() => setExpandedSection('timeline')}
        >
          Timeline
        </button>
        <button
          className={`tabButton ${expandedSection === 'notes' ? 'active' : ''}`}
          onClick={() => setExpandedSection('notes')}
        >
          Notes
        </button>
        <button
          className={`tabButton ${expandedSection === 'assignment' ? 'active' : ''}`}
          onClick={() => setExpandedSection('assignment')}
        >
          Assign
        </button>
      </div>
    </div>
  );
}
