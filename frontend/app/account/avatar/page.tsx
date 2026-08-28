import { Camera, UserCircle, UploadCloud, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountAvatarPage() {
  return (
    <AccountPageShell
      title="Avatar"
      subtitle="Update your profile image and keep the account identity consistent across PesaGuard."
      actions={
        <button type="button" className="buttonGhost">
          <UploadCloud size={16} /> Upload image
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel centerPanel">
          <div className="avatarPreview">
            <UserCircle size={72} />
          </div>
          <p className="muted">Use a clear and professional avatar to help colleagues recognize your account.</p>
          <button type="button" className="buttonAccent">
            <Camera size={16} /> Update avatar
          </button>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Avatar guidance</h2>
              <p className="muted">Choose an image that fits your enterprise profile.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Keep the image simple and recognizable.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Use a square image with strong contrast and clarity.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Avoid personal photos for organization-managed accounts.</span>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Brand consistency</p>
                <p className="muted">A consistent profile image improves trust during investigations and handoffs.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
