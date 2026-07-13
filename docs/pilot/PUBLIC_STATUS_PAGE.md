<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PesaGuard Status</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; background: #07110d; color: #f5fff8; margin: 0; padding: 0; }
    .container { max-width: 860px; margin: 0 auto; padding: 3rem 1.5rem 4rem; }
    .card { background: #10231a; border: 1px solid #2d4b39; border-radius: 16px; padding: 2rem; box-shadow: 0 12px 40px rgba(0,0,0,0.25); }
    .badge { display: inline-block; padding: 0.45rem 0.8rem; border-radius: 999px; background: #1f6a3b; color: white; font-weight: 700; }
    h1 { font-size: 2rem; margin-top: 1rem; }
    .muted { color: #a9c4b0; }
    ul { line-height: 1.7; }
    a { color: #8fe0a9; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="badge">Operational</div>
      <h1>PesaGuard Pilot Status</h1>
      <p class="muted">All core reconciliation and alerting services are operating normally.</p>
      <h2>Current status</h2>
      <ul>
        <li>Webhook ingestion: healthy</li>
        <li>Reconciliation engine: healthy</li>
        <li>Alerting and dashboard services: healthy</li>
        <li>Backup and retention processes: scheduled</li>
      </ul>
      <h2>Support</h2>
      <p>For urgent pilot issues, contact the pilot support channel or the on-call operator.</p>
      <p><a href="./support.html">Pilot support details</a></p>
    </div>
  </div>
</body>
</html>
