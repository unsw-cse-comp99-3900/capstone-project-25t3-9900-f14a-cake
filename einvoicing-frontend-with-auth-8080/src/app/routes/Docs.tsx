export default function DocsPage(){
  return (
    <div className="prose max-w-none">
      <h2>Endpoints used by this app</h2>
      <ul>
        <li><code>POST /api/auth/login</code>, <code>GET /api/auth/me</code>, <code>POST /api/auth/logout</code></li>
        <li><code>POST /api/ess/validate</code> — ESS validation proxy (expects {"{ content, checksum, rules }"})</li>
        <li><code>POST /api/schema/validate</code> — XSD validation proxy</li>
        <li><code>POST /api/send</code> — Send invoice (email/sftp/peppol)</li>
      </ul>
      <p>Set API_BASE in .env and run docker-compose.proxy.yml to avoid CORS.</p>
    </div>
  )
}
