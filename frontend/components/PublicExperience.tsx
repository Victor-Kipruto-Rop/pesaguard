import {
  ArrowRight, Sparkles, CircleCheck, Zap, ShieldCheck, Workflow,
  ChevronRight, BarChart3, Check, TrendingUp, Users, Globe, LockKeyhole
} from 'lucide-react';

type PageKey = 'home' | 'features' | 'pricing' | 'security' | 'about' | 'contact' | 'book-demo' | 
  'request-demo' | 'solutions' | 'industries' | 'integrations' | 'enterprise' |
  'customers' | 'testimonials' | 'documentation' | 'faq' | 'articles' |
  'article-details' | 'blog' | 'careers' | 'changelog' | 'newsletter' |
  'partners' | 'roadmap' | 'download-brochure';

const content: Record<PageKey, { eyebrow: string; title: string; description: string; primary: string; secondary: string; stats: string[] }> = {
  home: { eyebrow: 'ENTERPRISE PAYMENT RECONCILIATION', title: 'Masterful control over every transaction.', description: 'Experience the future of payment operations. PesaGuard delivers unprecedented clarity, speed, and confidence across your entire M-Pesa ecosystem.', primary: 'Start Free Trial', secondary: 'See Live Demo', stats: ['99.98% accuracy guaranteed', 'Real-time exception routing', 'Enterprise-grade compliance'] },
  features: { eyebrow: 'POWERFUL CAPABILITIES', title: 'Everything you need to operate with precision.', description: 'Sophisticated tools built for modern payment teams. Reconcile millions of transactions, detect anomalies instantly, and maintain complete audit readiness.', primary: 'Explore Features', secondary: 'View Integrations', stats: ['Live transaction monitoring', 'AI-powered anomaly detection', 'Automated rule engine'] },
  pricing: { eyebrow: 'TRANSPARENT PRICING', title: 'Scale without surprises.', description: 'Choose the plan that fits your operation. Upgrade anytime. No contracts, no hidden fees - just powerful reconciliation when you need it.', primary: 'Select Plan', secondary: 'Talk to Sales', stats: ['Flexible monthly billing', 'Unlimited API calls', '30-day money-back guarantee'] },
  security: { eyebrow: 'SECURITY & COMPLIANCE', title: 'Built on trust. Verified by experts.', description: 'Military-grade encryption, SOC 2 Type II certified, and complete regulatory compliance. Your data is protected with the highest industry standards.', primary: 'View Security', secondary: 'Download Whitepaper', stats: ['SOC 2 Type II certified', 'ISO 27001 compliant', '256-bit AES encryption'] },
  about: { eyebrow: 'OUR MISSION', title: 'Transforming payment operations globally.', description: 'Founded on the principle that financial accuracy should not require manual effort. We build tools that let teams focus on strategy, not spreadsheets.', primary: 'Meet Our Team', secondary: 'Join Us', stats: ['Trusted by 500+ teams', 'Processing 10M+ daily', 'East Africa headquarters'] },
  contact: { eyebrow: 'GET IN TOUCH', title: 'Lets build something remarkable together.', description: 'Have questions? Our expert team is ready to discuss your specific needs and show you exactly how PesaGuard can transform your operation.', primary: 'Schedule Demo', secondary: 'Send Message', stats: ['Less than 2 hour response', 'Expert product consultants', 'Personalized onboarding'] },
  'book-demo': { eyebrow: 'LIVE PRODUCT WALKTHROUGH', title: 'See PesaGuard in action.', description: 'Join an interactive session with our team. We will walk through your specific use case and show you how PesaGuard solves your toughest challenges.', primary: 'Book Your Slot', secondary: 'View Features', stats: ['30-45 minutes', 'Tailored to your workflow', 'No technical knowledge needed'] },
  'request-demo': { eyebrow: 'REQUEST DEMO', title: 'Discover the PesaGuard difference.', description: 'Connect with our product specialists for a personalized demo. We will answer all your questions and outline your clear path forward.', primary: 'Request Demo', secondary: 'See Testimonials', stats: ['1-on-1 with experts', 'Custom scenarios', 'Immediate ROI analysis'] },
  solutions: { eyebrow: 'INDUSTRY SOLUTIONS', title: 'Purpose-built for your specific needs.', description: 'Fintech, marketplaces, banks, or enterprises - we have architected solutions for every payment operation scenario.', primary: 'Explore Solutions', secondary: 'Talk to Specialist', stats: ['Fintech optimization', 'Marketplace workflows', 'Enterprise governance'] },
  industries: { eyebrow: 'TRUSTED BY LEADING TEAMS', title: 'Built for organizations that demand precision.', description: 'From regulated enterprises to high-growth fintechs, the most demanding payment operations choose PesaGuard.', primary: 'Explore Industries', secondary: 'Read Case Studies', stats: ['Fintech leaders', 'Enterprise banks', 'Regional marketplaces'] },
  integrations: { eyebrow: 'SEAMLESS CONNECTIVITY', title: 'Your entire stack, unified.', description: 'Direct integrations with M-Pesa, Daraja, and 50+ enterprise platforms. Sync data automatically, eliminate manual workflows entirely.', primary: 'View Integrations', secondary: 'API Documentation', stats: ['50+ native connectors', 'Webhook support', 'Real-time sync'] },
  enterprise: { eyebrow: 'ENTERPRISE SOLUTIONS', title: 'Power and control for large-scale operations.', description: 'Custom implementations, dedicated infrastructure, and white-glove support for your complex reconciliation needs.', primary: 'Contact Enterprise', secondary: 'Security Overview', stats: ['Dedicated infrastructure', 'Custom workflows', '99.99% SLA'] },
  customers: { eyebrow: 'CUSTOMER SUCCESS', title: 'Loved by the teams using it daily.', description: 'See how leading organizations transformed their payment operations, reduced manual work by 90%, and gained complete operational visibility.', primary: 'View Case Studies', secondary: 'Book a Demo', stats: ['90% time savings', '2-week deployment', 'Avg. 3x faster close'] },
  testimonials: { eyebrow: 'WHAT OUR CUSTOMERS SAY', title: 'The story behind the platform.', description: 'Hear directly from the finance and operations leaders who have built confidence into their payment operations with PesaGuard.', primary: 'Read Testimonials', secondary: 'Meet Our Customers', stats: ['500+ happy teams', '98% satisfaction score', 'Award-winning support'] },
  documentation: { eyebrow: 'HELPFUL RESOURCES', title: 'Everything you need to succeed.', description: 'Complete guides, video tutorials, and API documentation to help you get the most from PesaGuard.', primary: 'Browse Docs', secondary: 'Developer Portal', stats: ['1000+ pages', 'Video tutorials', 'Community forum'] },
  faq: { eyebrow: 'COMMON QUESTIONS', title: 'Quick answers to your concerns.', description: 'From implementation to security to pricing, we have covered everything you need to know.', primary: 'Get Answers', secondary: 'Contact Support', stats: ['50+ answered topics', 'Live chat support', 'Response guarantee'] },
  articles: { eyebrow: 'INSIGHTS & IDEAS', title: 'Learn from payment operation experts.', description: 'Deep dives into best practices, industry trends, and strategies for building world-class payment operations.', primary: 'Read Articles', secondary: 'Subscribe', stats: ['Weekly insights', 'Industry trends', 'Expert perspectives'] },
  'article-details': { eyebrow: 'FEATURED ARTICLE', title: 'The anatomy of world-class reconciliation.', description: 'Explore the systems, practices, and technologies that separate good operations from exceptional ones.', primary: 'Read Full Article', secondary: 'Share', stats: ['10-minute read', 'Best practices', 'Expert authored'] },
  blog: { eyebrow: 'COMPANY JOURNAL', title: 'Insights from the ground floor.', description: 'Our latest thinking on payment operations, product updates, and the future of financial technology in Africa.', primary: 'Read Latest', secondary: 'Subscribe Newsletter', stats: ['Published weekly', 'Written by operators', 'Always actionable'] },
  careers: { eyebrow: 'JOIN OUR TEAM', title: 'Build the future of African fintech.', description: 'We are hiring talented people who believe excellent tools can transform an industry. Come build something meaningful.', primary: 'View Jobs', secondary: 'Learn About Us', stats: ['High-impact roles', 'Competitive benefits', 'Remote-friendly'] },
  changelog: { eyebrow: 'PRODUCT UPDATES', title: 'Always improving. Always listening.', description: 'See what is new. Follow our continuous updates as we add powerful features based on customer feedback.', primary: 'View Latest', secondary: 'Subscribe', stats: ['Bi-weekly releases', 'Customer-driven', 'Backward compatible'] },
  newsletter: { eyebrow: 'STAY INFORMED', title: 'The operators edge.', description: 'Curated insights on payment operations, regulatory changes, and strategic thinking for modern finance teams.', primary: 'Subscribe', secondary: 'Read Latest Issue', stats: ['Published monthly', 'Exclusive content', 'Expert contributors'] },
  partners: { eyebrow: 'PARTNERSHIP PROGRAM', title: 'Grow together with PesaGuard.', description: 'Join our partner ecosystem. Integrate with PesaGuard and deliver enhanced value to your customers.', primary: 'Become Partner', secondary: 'View Integrations', stats: ['Revenue sharing', 'Co-marketing', 'Technical support'] },
  roadmap: { eyebrow: 'PRODUCT ROADMAP', title: 'See what is coming next.', description: 'Transparency into our product direction. Vote on features. Shape the future with us.', primary: 'View Roadmap', secondary: 'Share Feedback', stats: ['3-month outlook', 'Community voting', 'Quarterly updates'] },
  'download-brochure': { eyebrow: 'PRODUCT OVERVIEW', title: 'One-page reference guide.', description: 'Your complete guide to PesaGuard capabilities, pricing, and implementation. Perfect for sharing with your team.', primary: 'Download PDF', secondary: 'Book Demo', stats: ['4-page guide', 'Free forever', 'Updated monthly'] },
};

const iconCards = [
  { icon: Zap, title: 'Lightning-Fast', body: 'Reconcile millions of transactions in seconds with industry-leading performance and real-time updates across all channels.' },
  { icon: ShieldCheck, title: 'Enterprise Security', body: 'Bank-grade encryption, compliance certifications, and comprehensive audit trails to keep your operations secure and auditable.' },
  { icon: Workflow, title: 'Seamless Workflows', body: 'Intuitive tools built for operators. Automate reconciliation, route exceptions intelligently, and close operations with confidence.' },
];

const homeFeatureCards = [
  { icon: Zap, title: 'Real-time reconciliation', body: 'Match transactions instantly across M-Pesa, banks, wallets, and internal ledgers with zero waiting for manual review.' },
  { icon: BarChart3, title: 'Operational intelligence', body: 'Track rate, volume, settlements, and exceptions in one live command center built for busy finance teams.' },
  { icon: ShieldCheck, title: 'Governed by design', body: 'Protect every action with approval flows, role control, immutable audit trails, and enterprise-grade security.' },
  { icon: Workflow, title: 'Smart exception routing', body: 'Route anomalies to the right team automatically, prioritize by severity, and close issues without spreadsheet chaos.' },
  { icon: TrendingUp, title: 'Revenue recovery', body: 'Recover blocked or delayed payments quickly while reducing financial leakage and settlement delays.' },
  { icon: Globe, title: 'Built for Africa', body: 'Optimized for local payment realities, multi-entity operations, and the speed required by modern fintech teams.' },
];

const workflowSteps = [
  { number: '01', title: 'Connect systems', body: 'Bring in M-Pesa, banks, wallets, and ERP data with secure integrations and no heavy setup.' },
  { number: '02', title: 'Match and monitor', body: 'Reconcile transactions continuously and get live alerts when anything differs from expectation.' },
  { number: '03', title: 'Resolve and learn', body: 'Assign exceptions, approve actions, and use AI-informed insights to improve operational performance.' },
];

const industryCards = [
  { title: 'Fintech teams', body: 'Keep revenue moving, reduce reconciliation lag, and maintain confidence in every payout.' },
  { title: 'SACCOs & cooperatives', body: 'Track member activity, manage risk, and protect operational accuracy across every account flow.' },
  { title: 'Banks & lenders', body: 'Accelerate settlement visibility, monitor exceptions, and maintain best-in-class governance.' },
];

const trustMetrics = [
  { amount: '99.98%', label: 'match rate' },
  { amount: '10M+', label: 'transactions / month' },
  { amount: '2x', label: 'faster closeouts' },
  { amount: '24/7', label: 'monitoring' },
];

const customerQuotes = [
  { quote: 'PesaGuard gave our operations team real visibility instead of endless spreadsheet checks.', author: 'Head of Finance', company: 'Regional fintech' },
  { quote: 'We reduced exception backlog in days and cut our reconciliation cycle from hours to minutes.', author: 'Ops Director', company: 'Payments platform' },
  { quote: 'It feels like an operating system for our payment engine, not another reporting tool.', author: 'CTO', company: 'Digital lender' },
];

const homeMetrics = [
  { label: 'Real-time', value: 'Transaction Visibility' },
  { label: 'Automated', value: 'Reconciliation' },
  { label: '24/7', value: 'Monitoring' },
  { label: 'Multi-channel', value: 'Data Integration' },
];

const problemSteps = [
  'M-Pesa data',
  'CSV export',
  'Excel matching',
  'Manual review',
  'Correction cycles',
  'Delayed reporting',
];

const faqItems = [
  { q: 'What is PesaGuard?', a: 'PesaGuard is a real-time financial operations platform for monitoring transaction flows, automating reconciliation, and surfacing exceptions before they become operational problems.' },
  { q: 'How does automated reconciliation work?', a: 'The platform ingests transaction data from connected channels, normalizes it, compares events against expected outcomes, and routes mismatches into exception workflows for review and resolution.' },
  { q: 'Does PesaGuard support M-Pesa?', a: 'It is designed for payment environments that include mobile money, banking, wallet, ERP, and API-driven data sources, with flexible integration patterns to support connected financial ecosystems.' },
  { q: 'How are exceptions handled?', a: 'Exceptions are surfaced in priority order with supporting context, ownership paths, and resolution tracking so teams can investigate and close issues quickly.' },
  { q: 'How secure is PesaGuard?', a: 'The platform is designed around secure operational principles, including encrypted transport, restricted access patterns, auditability, and operational monitoring across the financial workflow.' },
];

const articleSections = [
  'Why modern reconciliation matters',
  'The architecture behind operational visibility',
  'How teams reduce manual review',
  'What it looks like in practice',
  'Key takeaways for scaling teams',
];

const articleRelated = [
  { title: 'The payment operations checklist every scaling fintech should use', meta: '5 min read' },
  { title: 'Why manual reconciliation is quietly draining your operating margin', meta: '7 min read' },
  { title: 'Three signs your finance team is ready for a smarter exception workflow', meta: '4 min read' },
];

const aboutValues = [
  { icon: Zap, title: 'Built for speed', body: 'We created PesaGuard for teams that cannot afford delays, blind spots, or rework in high-volume payment operations.' },
  { icon: ShieldCheck, title: 'Designed for trust', body: 'Operational control, security, and accountability are built into every workflow from the start.' },
  { icon: Workflow, title: 'Made for operators', body: 'Our product is shaped by finance and ops teams who live with reconciliation pressure every day.' },
];

const aboutTimeline = [
  { year: '2018', title: 'The problem becomes clear', body: 'We observed recurring operational failures caused by fragmented payment data and spreadsheet-heavy reconciliation.' },
  { year: '2021', title: 'The first system is built', body: 'We launched a more structured way to monitor transaction integrity and route exceptions faster.' },
  { year: '2024', title: 'PesaGuard becomes a platform', body: 'The product matured into a full financial operations engine for modern fintech and payment businesses.' },
];

function DashboardPreview() {
  return (
    <div className="publicDashboard" aria-label="PesaGuard reconciliation dashboard preview">
      <div className="publicDashboardTop">
        <span className="publicLogoMark">P</span>
        <span>Live Operations</span>
        <span className="liveChip"><i /> Live</span>
      </div>
      <div className="publicMetricGrid">
        <div><small>Today Volume</small><strong>KES 12.4M</strong><em>+18.7%</em></div>
        <div><small>Match Rate</small><strong>99.98%</strong><em>Excellent</em></div>
        <div><small>Pending Review</small><strong>3</strong><em className="warm">Routed</em></div>
      </div>
      <div className="publicChart">
        <div className="chartHeading"><span>Reconciliation Trend</span><small>7-day moving average</small></div>
        <svg viewBox="0 0 620 180" role="img" aria-label="Upward reconciliation trend">
          <defs>
            <linearGradient id="lineFill" x1="0" x2="0" y1="0" y2="1">
              <stop stopColor="#10b981" stopOpacity=".35"/>
              <stop offset="1" stopColor="#10b981" stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d="M0 153 C36 143 55 112 90 125 S145 141 178 101 S235 110 272 86 S337 112 374 72 S429 67 465 81 S522 47 555 57 S588 25 620 31 V180 H0Z" fill="url(#lineFill)"/>
          <path d="M0 153 C36 143 55 112 90 125 S145 141 178 101 S235 110 272 86 S337 112 374 72 S429 67 465 81 S522 47 555 57 S588 25 620 31" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="exceptionRow">
        <span className="exceptionDot"/>
        <div><strong>Paybill reconciliation variance</strong><small>Detected 2 minutes ago</small></div>
        <span className="reviewTag">Analyze <ChevronRight size={14}/></span>
      </div>
    </div>
  );
}

export default function PublicExperience({ page }: { page: PageKey }) {
  const item = content[page];
  const home = page === 'home';
  const pricing = page === 'pricing';
  const security = page === 'security';

  if (page === 'article-details') {
    return (
      <main className="marketingPage articleDetailPage">
        <section className="marketingHero articleHero">
          <div className="marketingGlow marketingGlowOne" />
          <div className="marketingGlow marketingGlowTwo" />
          <div className="marketingContainer articleHeroContainer">
            <div className="articleTagRow">
              <span className="miniBadge">Featured article</span>
              <span className="articleMetaText">8 min read • Updated July 2026</span>
            </div>
            <h1>The anatomy of world-class reconciliation.</h1>
            <p className="marketingLead">
              Leading payment teams do not win by collecting more data. They win by turning noisy transaction flows into a clear, trusted operating picture that guides decisions in real time.
            </p>
            <div className="articleMetaRow">
              <div className="authorChip">
                <span className="publicLogoMark">P</span>
                <div>
                  <strong>PesaGuard Editorial</strong>
                  <small>Operations insights</small>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection articleBodySection">
          <div className="marketingContainer articleShell">
            <article className="articleMain">
              <div className="articleContentCard">
                <h2>Why modern reconciliation matters</h2>
                <p>Finance teams are not failing because they lack effort. They are failing because the systems around them were never designed for the speed and complexity of modern payment operations.</p>
                <p>Revenue enters through mobile money, bank rails, wallets, settlements, and internal ledgers. Each channel produces its own timestamps, IDs, and operational assumptions. Without a disciplined, real-time reconciliation layer, the result is a backlog of exceptions, confusion, and unnecessary exposure.</p>

                <blockquote>
                  The strongest operations teams treat reconciliation as a live operating system, not a periodic spreadsheet task.
                </blockquote>

                <h2>The architecture behind operational visibility</h2>
                <p>At the core of a high-performing reconciliation engine sits a simple principle: normalize everything, then compare only what matters. That means ingesting raw transaction data from every source, standardizing identifiers, and applying contextual matching rules for amount, reference, account, and timing.</p>
                <p>The moment the platform sees a mismatch, it becomes a guidepost. Teams can inspect the exception, identify root cause, and route it to the appropriate owner without losing context or wasting time reassembling evidence.</p>

                <div className="articleGraphic">
                  <div className="graphicCard"><span>Ingest</span><strong>Raw data</strong></div>
                  <div className="graphicArrow">→</div>
                  <div className="graphicCard"><span>Normalize</span><strong>Context</strong></div>
                  <div className="graphicArrow">→</div>
                  <div className="graphicCard emphasis"><span>Match</span><strong>Reconcile</strong></div>
                  <div className="graphicArrow">→</div>
                  <div className="graphicCard"><span>Act</span><strong>Resolve</strong></div>
                </div>

                <h2>How teams reduce manual review</h2>
                <p>One of the biggest operational wins after adopting a smarter reconciliation process is the reduction in repetitive review work. Instead of manually scanning matches across channels, teams focus only on real exceptions and variance outliers.</p>
                <p>That happens through defensible rules, intelligent matching, and created workflows that prioritize impact. A genuine system helps the team triage what matters first — payment failures, duplicate entries, pending settlement variance, or mismatched references.</p>

                <ul>
                  <li>Reduce duplicate investigations through deterministic matching logic.</li>
                  <li>Resolve drift faster with exception scores and priority labels.</li>
                  <li>Preserve accountability through visible ownership and audit trails.</li>
                </ul>

                <h2>What it looks like in practice</h2>
                <p>In a modern team, the reconciliation dashboard is no longer a passive report. It is a live signal environment. A team can immediately tell whether transactions are matching, which channels are underperforming, whether a settlement batch is delayed, and where intervention is necessary.</p>
                <p>That is what gives high-performing operations a real edge: not the volume of data they process, but the speed with which they can make confident decisions based on trusted information.</p>

                <h2>Key takeaways for scaling teams</h2>
                <p>If your operations are growing, your reconciliation system must grow with them. That means designing for visibility, automating the repeatable path, and making exception handling a disciplined workflow rather than a reactive scramble.</p>
                <p>When you give finance teams clarity, speed, and confidence, the entire organization gets sharper. Reconciliation stops being a back-office task and becomes a strategic moat.</p>
              </div>
            </article>

            <aside className="articleSidebar">
              <div className="articleSidebarCard stickyCard">
                <h3>In this article</h3>
                <ul>
                  {articleSections.map((section) => (
                    <li key={section}>{section}</li>
                  ))}
                </ul>
              </div>

              <div className="articleSidebarCard">
                <h3>More reads</h3>
                <div className="relatedList">
                  {articleRelated.map(({ title, meta }) => (
                    <div key={title} className="relatedItem">
                      <strong>{title}</strong>
                      <span>{meta}</span>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section className="marketingCta">
          <div className="marketingContainer">
            <div>
              <p className="marketingEyebrow">READY TO SEE IT IN ACTION?</p>
              <h2>Turn payment complexity into operational clarity.</h2>
              <p>See how PesaGuard helps teams reconcile faster and operate with more confidence.</p>
            </div>
            <a href="/public/book-demo" className="marketingPrimary">Request a Demo <ArrowRight size={17} /></a>
          </div>
        </section>
      </main>
    );
  }

  if (page === 'about') {
    return (
      <main className="marketingPage aboutPage">
        <section className="marketingHero aboutHero">
          <div className="marketingGlow marketingGlowOne" />
          <div className="marketingGlow marketingGlowTwo" />
          <div className="marketingContainer aboutHeroGrid">
            <div className="marketingCopy">
              <p className="marketingEyebrow"><Sparkles size={14} /> OUR MISSION</p>
              <h1>We build confidence into every payment flow.</h1>
              <p className="marketingLead">
                PesaGuard was created to help ambitious finance teams run clearer, faster, and more reliable operations in a world where payment complexity is rising every day.
              </p>
              <div className="marketingActions">
                <a href="/public/book-demo" className="marketingPrimary">Book a Demo <ArrowRight size={17} /></a>
                <a href="/public/contact" className="marketingSecondary">Talk to Us</a>
              </div>
              <div className="marketingStats">
                <span><CircleCheck size={16} />Trusted by growing fintechs</span>
                <span><CircleCheck size={16} />Built for operational precision</span>
                <span><CircleCheck size={16} />Focused on real-world execution</span>
              </div>
            </div>

            <div className="aboutHeroVisual">
              <div className="aboutVisionCard mainCard">
                <div className="aboutCardHeader">
                  <span className="publicLogoMark">P</span>
                  <strong>PesaGuard</strong>
                </div>
                <div className="aboutMiniStats">
                  <div>
                    <small>Operations</small>
                    <strong>99.98%</strong>
                  </div>
                  <div>
                    <small>Closed</small>
                    <strong>2.4x</strong>
                  </div>
                </div>
                <div className="aboutSignalLine">
                  <span className="signalPulse" />
                  <small>Payment integrity monitored</small>
                </div>
              </div>

              <div className="aboutVisionCard floatingCardOne">
                <span>Mission</span>
                <strong>Clarify finance operations.</strong>
              </div>
              <div className="aboutVisionCard floatingCardTwo">
                <span>Focus</span>
                <strong>Fewer blind spots.</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="metricsStrip">
          <div className="marketingContainer metricsGrid">
            <div className="metricTile"><small>Teams</small><strong>500+</strong></div>
            <div className="metricTile"><small>Transactions</small><strong>10M+/day</strong></div>
            <div className="metricTile"><small>Faster closeouts</small><strong>2x</strong></div>
            <div className="metricTile"><small>Headquarters</small><strong>Nairobi</strong></div>
          </div>
        </section>

        <section className="marketingSection">
          <div className="marketingContainer aboutStoryGrid">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">WHO WE ARE</p>
              <h2>We exist to make financial operations legible.</h2>
              <p>Payment businesses are growing faster than their systems can keep up. We saw the same pattern again and again: fragmented data, high manual effort, and too much uncertainty around what was actually happening in real time.</p>
              <p>PesaGuard brings operational clarity to the people holding the line — finance teams, reconciliation specialists, compliance operators, and product leaders who need accuracy without friction.</p>
            </div>

            <div className="aboutStoryPanel">
              <div className="storyPill"><BarChart3 size={18} /> Financial visibility</div>
              <div className="storyPill"><Users size={18} /> Operator-first design</div>
              <div className="storyPill"><TrendingUp size={18} /> Scalable infrastructure</div>
              <div className="storyPill"><ShieldCheck size={18} /> Built with trust</div>
            </div>
          </div>
        </section>

        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">OUR VALUES</p>
              <h2>Built around the realities of modern finance teams.</h2>
            </div>

            <div className="capabilityGrid">
              {aboutValues.map(({ icon: Icon, title, body }) => (
                <article className="capabilityCard" key={title}>
                  <span className="capabilityIcon"><Icon size={22} /></span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingSection aboutTimelineSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">OUR JOURNEY</p>
              <h2>A product built from operational pain.</h2>
            </div>

            <div className="aboutTimeline">
              {aboutTimeline.map(({ year, title, body }) => (
                <div className="aboutTimelineItem" key={year}>
                  <span className="timelineYear">{year}</span>
                  <div className="timelineContent">
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">WHY TEAMS CHOOSE US</p>
              <h2>We turn financial complexity into operational confidence.</h2>
            </div>

            <div className="capsuleGrid">
              <div className="capsuleCard">
                <strong>Operator-first</strong>
                <span>Designed for real workflows, not abstract dashboards.</span>
              </div>
              <div className="capsuleCard">
                <strong>Transparent</strong>
                <span>Every action is visible, traceable, and reviewable.</span>
              </div>
              <div className="capsuleCard">
                <strong>Adaptive</strong>
                <span>Flexible enough for growth-stage teams and enterprise complexity.</span>
              </div>
              <div className="capsuleCard">
                <strong>Secure by default</strong>
                <span>Trust and compliance are not optional features here.</span>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingCta">
          <div className="marketingContainer">
            <div>
              <p className="marketingEyebrow">JOIN THE NEXT CHAPTER</p>
              <h2>Build a sharper operational future with us.</h2>
              <p>Whether you are scaling a fintech product or modernizing a payments operation, PesaGuard is ready to help.</p>
            </div>
            <div className="ctaActions">
              <a href="/public/book-demo" className="marketingPrimary">Request a Demo <ArrowRight size={17} /></a>
              <a href="/public/contact" className="marketingSecondary darkSecondary">Contact Sales</a>
            </div>
          </div>
        </section>

        <footer className="marketingFooter">
          <div className="marketingContainer footerGrid">
            <div className="footerBrandBlock">
              <a href="/public/home" className="footerBrand"><span className="publicLogoMark">P</span><b>PesaGuard</b></a>
              <span>Financial clarity for modern operations.</span>
            </div>

            <div className="footerLinks">
              <div>
                <h4>Company</h4>
                <a href="/public/about">About</a>
                <a href="/public/contact">Contact</a>
                <a href="/public/faq">FAQ</a>
              </div>
              <div>
                <h4>Platform</h4>
                <a href="/public/features">Features</a>
                <a href="/public/security">Security</a>
                <a href="/public/documentation">Docs</a>
              </div>
              <div>
                <h4>Resources</h4>
                <a href="/public/blog">Blog</a>
                <a href="/public/solutions">Solutions</a>
                <a href="/auth/login">Sign in</a>
              </div>
            </div>
          </div>
          <div className="marketingContainer footerBottom">
            <span>© 2026 PesaGuard</span>
            <div>
              <a href="/public/security">Privacy</a>
              <a href="/public/security">Terms</a>
            </div>
          </div>
        </footer>
      </main>
    );
  }

  if (home) {
    return (
      <main className="marketingPage">
        <section className="marketingHero marketingHeroHome">
          <div className="marketingGlow marketingGlowOne" />
          <div className="marketingGlow marketingGlowTwo" />
          <div className="marketingContainer marketingHeroGrid">
            <div className="marketingCopy">
              <p className="marketingEyebrow"><Sparkles size={14} /> REAL-TIME FINANCIAL INFRASTRUCTURE</p>
              <h1>Reconcile every transaction.<br />Automatically.</h1>
              <p className="marketingLead">
                PesaGuard gives businesses real-time visibility into transactions, settlements, reconciliation, and financial exceptions — without spreadsheets, manual matching, or guesswork.
              </p>
              <div className="marketingActions">
                <a href="/public/book-demo" className="marketingPrimary">Request a Demo <ArrowRight size={17} /></a>
                <a href="/public/features" className="marketingSecondary">Explore Platform</a>
              </div>
              <div className="heroStatusRow">
                <span className="statusDot" />
                <span>PesaGuard Systems Operational</span>
              </div>
            </div>

            <div className="heroDashboardWrap">
              <div className="heroDashboard">
                <div className="heroDashboardHeader">
                  <div className="heroBrand"><span className="publicLogoMark">P</span> PesaGuard</div>
                  <span className="heroLiveBadge"><span className="statusDot" /> System Live</span>
                </div>

                <div className="heroCardStats">
                  <div className="heroMetric">
                    <span>Transactions Today</span>
                    <strong>1,284,932</strong>
                  </div>
                  <div className="heroMetric">
                    <span>Reconciled</span>
                    <strong>99.98%</strong>
                  </div>
                  <div className="heroMetric">
                    <span>Exceptions</span>
                    <strong>27</strong>
                  </div>
                  <div className="heroMetric accent">
                    <span>Processing</span>
                    <strong>2,481/min</strong>
                  </div>
                </div>

                <div className="miniChartBox">
                  <div className="miniChartHeader">
                    <span>Transaction flow</span>
                    <span className="chartPill">+12.8%</span>
                  </div>
                  <svg viewBox="0 0 420 140" aria-label="reconciliation chart" role="img">
                    <path d="M0 94 C60 85, 90 66, 130 71 S210 54, 240 40 S310 22, 350 32 S390 18, 420 24 L420 140 L0 140 Z" fill="rgba(46,204,135,0.18)" />
                    <path d="M0 94 C60 85, 90 66, 130 71 S210 54, 240 40 S310 22, 350 32 S390 18, 420 24" fill="none" stroke="#65df9d" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                </div>

                <div className="floatingCards">
                  <div className="floatingCard positive">
                    <span className="cardLabel">M-Pesa payment</span>
                    <strong>+ KES 4,500</strong>
                    <small>✓ matched</small>
                  </div>
                  <div className="floatingCard positive alt">
                    <span className="cardLabel">Settlement</span>
                    <strong>+ KES 18,200</strong>
                    <small>✓ reconciled</small>
                  </div>
                  <div className="floatingCard warning">
                    <span className="cardLabel">Transaction</span>
                    <strong>KES 7,800</strong>
                    <small>⚠ exception</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="metricsStrip">
          <div className="marketingContainer metricsGrid">
            {homeMetrics.map(({ label, value }) => (
              <div key={label} className="metricTile">
                <small>{label}</small>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="marketingSection problemSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">THE PROBLEM</p>
              <h2>Reconciliation shouldn’t live in spreadsheets.</h2>
              <p>Fragmented payment flows create blind spots. Manual work slows teams down, hides discrepancies, and leaves money exposed to delays and avoidable risk.</p>
            </div>

            <div className="problemLayout">
              <div className="problemChain" aria-label="old disconnected reconciliation flow">
                {problemSteps.map((step, index) => (
                  <div key={step} className={`problemNode ${index >= 3 ? 'warning' : ''}`}>
                    <span>{step}</span>
                  </div>
                ))}
              </div>

              <div className="problemDetails">
                <div className="problemCard warningCard">
                  <span className="miniBadge danger">Missing</span>
                  <h3>Missing transactions</h3>
                  <p>Disconnected sources leave gaps in your financial picture and delay operational reporting.</p>
                </div>
                <div className="problemCard warningCard">
                  <span className="miniBadge danger">Duplicate</span>
                  <h3>Duplicate payments</h3>
                  <p>Without matching logic, duplicate or partial entries create false balances and review loops.</p>
                </div>
                <div className="problemCard warningCard">
                  <span className="miniBadge danger">Delayed</span>
                  <h3>Delayed reporting</h3>
                  <p>Teams work off stale exports and end-of-day checks instead of real-time confidence.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection transformSection">
          <div className="marketingContainer transformGrid">
            <div className="transformationBlock">
              <p className="marketingEyebrow">BEFORE</p>
              <ul className="tagList">
                <li>Fragmented data</li>
                <li>Manual work</li>
                <li>Delayed visibility</li>
                <li>Unresolved exceptions</li>
              </ul>
            </div>

            <div className="transformArrow">→</div>

            <div className="transformationBlock active">
              <p className="marketingEyebrow">PESAGUARD</p>
              <ul className="tagList">
                <li>Connected</li>
                <li>Automated</li>
                <li>Real-time</li>
                <li>Observable</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="marketingSection streamSection">
          <div className="marketingContainer">
            <div className="sectionIntro wideIntro">
              <p className="marketingEyebrow">LIVE TRANSACTION STREAM</p>
              <h2>One command center for your financial operations.</h2>
            </div>

            <div className="transactionStreamPanel">
              <div className="streamHeader">
                <div className="streamTitle">Live Transaction Stream</div>
                <span className="streamLive"><span className="statusDot" /> LIVE</span>
              </div>
              <div className="streamRows">
                {[
                  ['14:32:41', 'M-Pesa', 'KES 12,500', '✓ MATCHED'],
                  ['14:32:40', 'Bank', 'KES 3,200', '✓ MATCHED'],
                  ['14:32:38', 'Wallet', 'KES 8,700', '⚠ REVIEW'],
                  ['14:32:37', 'M-Pesa', 'KES 15,000', '✓ MATCHED'],
                  ['14:32:35', 'Settlement', 'KES 2,450', '✓ MATCHED'],
                ].map(([time, channel, amount, status]) => (
                  <div key={`${time}-${amount}`} className="streamRow">
                    <span>{time}</span>
                    <span>{channel}</span>
                    <span>{amount}</span>
                    <span className={status.includes('⚠') ? 'warningLabel' : 'successLabel'}>{status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection platformSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">PLATFORM OVERVIEW</p>
              <h2>Operational clarity, across every financial source.</h2>
            </div>

            <div className="platformCanvas">
              <aside className="platformSidebar">
                <div className="navPill active">Overview</div>
                <div className="navPill">Transactions</div>
                <div className="navPill">Reconciliation</div>
                <div className="navPill">Exceptions</div>
                <div className="navPill">Settlements</div>
                <div className="navPill">Analytics</div>
              </aside>

              <div className="platformMain">
                <div className="platformHeader">
                  <div>
                    <strong>Financial operations</strong>
                    <small>Realtime system overview</small>
                  </div>
                  <span className="tinyStatus"><span className="statusDot" /> Healthy</span>
                </div>

                <div className="overviewMetrics">
                  <div className="overviewMetric"><span>Volume</span><strong>1.2M</strong></div>
                  <div className="overviewMetric"><span>Reconciled</span><strong>99.8%</strong></div>
                  <div className="overviewMetric"><span>Exceptions</span><strong>27</strong></div>
                  <div className="overviewMetric"><span>Settled</span><strong>94.7%</strong></div>
                </div>

                <div className="overviewChart">
                  <svg viewBox="0 0 520 170" aria-label="analytics chart" role="img">
                    <path d="M0 120 C70 110, 100 90, 150 75 S220 58, 270 63 S340 30, 390 38 S470 22, 520 12" fill="none" stroke="#74e7b0" strokeWidth="3" strokeLinecap="round"/>
                    <path d="M0 150 C80 122, 132 96, 186 98 S290 88, 340 72 S445 60, 520 42" fill="none" stroke="rgba(255,255,255,0.45)" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>

                <div className="recentActions">
                  <div className="recentRow"><span>Payment cycle</span><strong>Completed</strong></div>
                  <div className="recentRow"><span>Exception queue</span><strong>3 high priority</strong></div>
                  <div className="recentRow"><span>Settlement batch</span><strong>Processing</strong></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">CORE FEATURES</p>
              <h2>Control every step of the financial flow.</h2>
            </div>

            <div className="capabilityGrid">
              {homeFeatureCards.map(({ icon: Icon, title, body }) => (
                <article className="capabilityCard" key={title}>
                  <span className="capabilityIcon"><Icon size={22} /></span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                  <a href="/public/features">Learn more <ArrowRight size={14} /></a>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingSection deepDiveSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">FEATURE DEEP-DIVE</p>
              <h2>See every transaction. Resolve what doesn’t match.</h2>
            </div>

            <div className="deepDiveGrid">
              <div className="deepDiveCard">
                <div>
                  <p className="miniBadge">Visibility</p>
                  <h3>See every transaction.</h3>
                  <p>Monitor transaction opportunities and risks in real time across all connected financial channels.</p>
                  <ul>
                    <li>Live transaction feed</li>
                    <li>Processing visibility</li>
                    <li>Failure monitoring</li>
                  </ul>
                </div>
              </div>

              <div className="deepDiveCard inverse">
                <div>
                  <p className="miniBadge">Control</p>
                  <h3>Find what doesn’t match.</h3>
                  <p>Surface financial exceptions with context, severity, and ownership so teams can act with confidence.</p>
                  <ul>
                    <li>Unmatched transactions</li>
                    <li>Settlement mismatches</li>
                    <li>Priority based review</li>
                  </ul>
                </div>
              </div>

              <div className="deepDiveCard">
                <div>
                  <p className="miniBadge">Automation</p>
                  <h3>Automate reconciliation.</h3>
                  <p>Compare references, amounts, timestamps, entities, and account flows automatically without queueing everything for manual review.</p>
                  <ul>
                    <li>Amount matching</li>
                    <li>Reference validation</li>
                    <li>Duplicate detection</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection flowSection">
          <div className="marketingContainer flowWrap">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">AUTOMATED RECONCILIATION ENGINE</p>
              <h2>From raw transaction data to financial truth.</h2>
            </div>

            <div className="reconciliationFlow">
              <div className="flowStep">Transaction</div>
              <div className="flowArrow">↓</div>
              <div className="flowStep">Validation</div>
              <div className="flowArrow">↓</div>
              <div className="flowStep">Normalization</div>
              <div className="flowArrow">↓</div>
              <div className="flowStep emphasis">Matching Engine</div>
              <div className="flowArrow">↓</div>
              <div className="flowStep">Reconciliation</div>
              <div className="flowArrow">↓</div>
              <div className="flowStep success">Audit Event</div>
            </div>

            <div className="matchCheckRow">
              <span>✓ Amount</span>
              <span>✓ Reference</span>
              <span>✓ Account</span>
              <span>✓ Timestamp</span>
            </div>
          </div>
        </section>

        <section className="marketingSection securitySection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">SECURITY</p>
              <h2>Financial data deserves infrastructure-grade security.</h2>
            </div>

            <div className="securityPanel">
              <div className="securityList">
                <div className="securityItem"><span className="miniBadge">Secure</span><strong>Encryption in transit</strong></div>
                <div className="securityItem"><span className="miniBadge">Secure</span><strong>Encryption at rest</strong></div>
                <div className="securityItem"><span className="miniBadge">Secure</span><strong>Role-based access control</strong></div>
                <div className="securityItem"><span className="miniBadge">Secure</span><strong>Audit logs and monitoring</strong></div>
              </div>
              <div className="securityStatusPanel">
                <div className="systemStatusItem"><span className="statusDot" /> API</div>
                <div className="systemStatusItem"><span className="statusDot" /> Transaction ingest</div>
                <div className="systemStatusItem"><span className="statusDot" /> Reconciliation</div>
                <div className="systemStatusItem"><span className="statusDot" /> Alerting</div>
              </div>
            </div>
          </div>
        </section>

        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">INDUSTRY SOLUTIONS</p>
              <h2>Built for the speed and complexity of modern finance.</h2>
            </div>

            <div className="capabilityGrid">
              {industryCards.map(({ title, body }) => (
                <article className="capabilityCard" key={title}>
                  <span className="capabilityIcon"><Users size={22} /></span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingSection pricingSection">
          <div className="marketingContainer">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">TRANSPARENT PRICING</p>
              <h2>Choose a plan that matches your scale.</h2>
            </div>
            <div className="pricingGrid">
              {[
                ['Starter', 'For growing businesses needing cleaner visibility.', 'Custom', ['Transaction monitoring', 'Basic reconciliation', 'Email support', 'Shared workspace']],
                ['Growth', 'For high-volume operations teams.', 'Custom', ['Smart exception routing', 'Priority monitoring', 'Team dashboards', 'Advanced workflows']],
                ['Enterprise', 'For complex multi-entity financial operations.', 'Custom', ['Custom integrations', 'Dedicated support', 'Advanced controls', 'SLA coverage']]
              ].map(([name, desc, price, benefits], index) => (
                <article className={`priceCard ${index === 1 ? 'featured' : ''}`} key={name as string}>
                  {index === 1 && <span className="popularTag">Most popular</span>}
                  <h3>{name}</h3>
                  <p>{desc}</p>
                  <strong>{price}<small>{index < 2 ? ' / month' : ''}</small></strong>
                  <a href="/public/contact" className={index === 1 ? 'marketingPrimary' : 'priceButton'}>Talk to sales <ArrowRight size={16} /></a>
                  <ul>{(benefits as string[]).map((benefit) => <li key={benefit}><Check size={16} />{benefit}</li>)}</ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingSection faqSection">
          <div className="marketingContainer faqWrap">
            <div className="sectionIntro clampIntro">
              <p className="marketingEyebrow">FAQ</p>
              <h2>Answers for growing financial teams.</h2>
            </div>

            <div className="faqList">
              {faqItems.map(({ q, a }) => (
                <details key={q} className="faqItem" open={q === 'What is PesaGuard?'}>
                  <summary>{q}</summary>
                  <p>{a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="marketingCta">
          <div className="marketingContainer">
            <div>
              <p className="marketingEyebrow">READY TO TRANSFORM?</p>
              <h2>Stop chasing transactions.<br />Start knowing where they are.</h2>
              <p>Discover how PesaGuard can turn fragmented transaction data into a real-time source of financial truth.</p>
            </div>
            <div className="ctaActions">
              <a href="/public/book-demo" className="marketingPrimary">Request a Demo <ArrowRight size={17} /></a>
              <a href="/public/contact" className="marketingSecondary darkSecondary">Talk to an Expert</a>
            </div>
          </div>
        </section>

        <footer className="marketingFooter">
          <div className="marketingContainer footerGrid">
            <div className="footerBrandBlock">
              <a href="/public/home" className="footerBrand"><span className="publicLogoMark">P</span><b>PesaGuard</b></a>
              <span>Real-Time Financial Reconciliation</span>
            </div>

            <div className="footerLinks">
              <div>
                <h4>Product</h4>
                <a href="/public/features">Platform</a>
                <a href="/public/features">Features</a>
                <a href="/public/integrations">Integrations</a>
                <a href="/public/security">Security</a>
              </div>
              <div>
                <h4>Solutions</h4>
                <a href="/public/solutions">FinTech</a>
                <a href="/public/industries">SACCOs</a>
                <a href="/public/solutions">E-commerce</a>
                <a href="/public/enterprise">Enterprise</a>
              </div>
              <div>
                <h4>Resources</h4>
                <a href="/public/documentation">Documentation</a>
                <a href="/public/faq">FAQ</a>
                <a href="/public/blog">Blog</a>
                <a href="/public/contact">Contact</a>
              </div>
            </div>
          </div>
          <div className="marketingContainer footerBottom">
            <span>© 2026 PesaGuard</span>
            <div>
              <a href="/public/security">Privacy</a>
              <a href="/public/security">Terms</a>
              <a href="/auth/login">Sign in</a>
            </div>
          </div>
        </footer>
      </main>
    );
  }

  return (
    <main className="marketingPage">
      <section className={`marketingHero ${home ? 'marketingHeroHome' : ''}`}>
        <div className="marketingGlow marketingGlowOne"/><div className="marketingGlow marketingGlowTwo"/>
        <div className="marketingContainer marketingHeroGrid">
          <div className="marketingCopy">
            <p className="marketingEyebrow"><Sparkles size={14}/>{item.eyebrow}</p>
            <h1>{item.title}</h1>
            <p className="marketingLead">{item.description}</p>
            <div className="marketingActions">
              <a href={page === 'pricing' || page === 'enterprise' ? '/public/contact' : '/public/book-demo'} className="marketingPrimary">{item.primary}<ArrowRight size={17}/></a>
              <a href={page === 'documentation' ? '/developer/developer-home' : '/public/features'} className="marketingSecondary">{item.secondary}</a>
            </div>
            <div className="marketingStats">{item.stats.map((stat) => <span key={stat}><CircleCheck size={16}/>{stat}</span>)}</div>
          </div>
          <DashboardPreview />
        </div>
      </section>

      {pricing ? (
        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro">
              <p className="marketingEyebrow">TRANSPARENT PRICING</p>
              <h2>Plans designed for growth.</h2>
              <p>Start small, scale up. All plans include a 30-day free trial. No credit card required. Upgrade or downgrade anytime.</p>
            </div>
            <div className="pricingGrid">
              {[
                ['Starter', 'Perfect for teams just getting started with reconciliation.', 'KES 18,000', ['Up to 1M transactions/month', 'Basic reconciliation rules', 'Email support', '30-day history']],
                ['Professional', 'For growing operations that need advanced features.', 'KES 48,000', ['Up to 20M transactions/month', 'Advanced rules engine', 'Priority support', '1-year history', 'Custom reports']],
                ['Enterprise', 'For large-scale operations with custom needs.', 'Custom', ['Unlimited transactions', 'Dedicated infrastructure', '24/7 white-glove support', 'Custom integrations', 'SLA guarantee']]
              ].map(([name, desc, price, benefits], index) => (
                <article className={`priceCard ${index === 1 ? 'featured' : ''}`} key={name as string}>
                  {index === 1 && <span className="popularTag">Most Popular</span>}
                  <h3>{name}</h3>
                  <p>{desc}</p>
                  <strong>{price}<small>{index < 2 ? ' / month' : ''}</small></strong>
                  <a href="/public/contact" className={index === 1 ? 'marketingPrimary' : 'priceButton'}>Get Started <ArrowRight size={16}/></a>
                  <ul>{(benefits as string[]).map((benefit) => <li key={benefit}><Check size={16}/>{benefit}</li>)}</ul>
                </article>
              ))}
            </div>
          </div>
        </section>
      ) : (
        <section className="marketingSection">
          <div className="marketingContainer">
            <div className="sectionIntro">
              <p className="marketingEyebrow">WHY PESAGUARD</p>
              <h2>{security ? 'Security built into every layer.' : 'Powerful features, elegantly simple.'}</h2>
              <p>{security ? 'Every component of PesaGuard is designed with security first. Encryption, access control, and audit trails are woven into the platform architecture.' : 'We designed PesaGuard to handle complex reconciliation workflows without complexity. Professional power meets intuitive design.'}</p>
            </div>
            <div className="capabilityGrid">
              {iconCards.map(({ icon: Icon, title, body }) => (
                <article className="capabilityCard" key={title}>
                  <span className="capabilityIcon"><Icon size={22}/></span>
                  <h3>{title}</h3>
                  <p>{body}</p>
                  <a href="/public/features">Learn more <ArrowRight size={14}/></a>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="marketingProof">
        <div className="marketingContainer proofGrid">
          <div>
            <p className="marketingEyebrow">TRUSTED BY LEADERS</p>
            <h2>Built for those who care about precision.</h2>
            <p>Leading fintech companies, banks, and operations teams rely on PesaGuard every single day to keep their payment operations running smoothly and securely.</p>
            <a href="/public/customers" className="textLink">View customer stories <ArrowRight size={16}/></a>
          </div>
          <div className="proofList">
            <span><TrendingUp size={19}/><b>Real-Time Intelligence</b><small>Know transaction status instantly, not tomorrow.</small></span>
            <span><Users size={19}/><b>Team Collaboration</b><small>Assign, comment, and resolve issues together seamlessly.</small></span>
            <span><Globe size={19}/><b>Global Reach, Local Touch</b><small>Built for Africa. Designed for the world.</small></span>
          </div>
        </div>
      </section>

      <section className="marketingCta">
        <div className="marketingContainer">
          <div>
            <p className="marketingEyebrow">READY TO TRANSFORM?</p>
            <h2>Join the leaders building tomorrows payment operations.</h2>
            <p>Get started free. No credit card required. Start reconciling like a Fortune 500 company in minutes.</p>
          </div>
          <a href="/public/book-demo" className="marketingPrimary">Start Your Free Trial <ArrowRight size={17}/></a>
        </div>
      </section>

      <footer className="marketingFooter">
        <div className="marketingContainer">
          <a href="/public/home" className="footerBrand"><span className="publicLogoMark">P</span><b>PesaGuard</b></a>
          <span>The operating system for modern payment operations.</span>
          <div><a href="/public/security"><LockKeyhole size={14}/>Security</a><a href="/public/contact">Contact</a><a href="/public/documentation">Docs</a><a href="/auth/login">Sign in</a></div>
        </div>
      </footer>
    </main>
  );
}
