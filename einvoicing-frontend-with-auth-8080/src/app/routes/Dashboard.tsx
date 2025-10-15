export default function Dashboard(){
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">E-invoicing Demo (Auth)</h1>
      <ol className="list-decimal list-inside space-y-1">
        <li>Create: GUI form / CSV-Excel / DB (SQLite) / OCR (image) → UBL.</li>
        <li>Validate: ESS (rules) + Schema validation → Grouped report; export JSON/HTML/PDF.</li>
        <li>Send: Email / SFTP / PEPPOL → delivery report。</li>
      </ol>
    </div>
  )
}
