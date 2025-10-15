import { useState } from 'react'
import { request } from '../../lib/request'

export default function SendPage(){
  const [xml, setXml] = useState<string>('')
  const [channel, setChannel] = useState<'email'|'sftp'|'peppol'>('email')
  const [to, setTo] = useState('demo@example.com')
  const [subject, setSubject] = useState('Invoice')
  const [body, setBody] = useState('Please find the invoice attached.')
  const [sftp, setSftp] = useState({ host:'', username:'', path:'/inbox' })
  const [peppol, setPeppol] = useState({ participantId:'', processId:'', docTypeId:'' })
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  async function handleSend(){
    setError(''); setResult(null); setLoading(true)
    try {
      const payload:any = { xml, channel }
      if (channel==='email') Object.assign(payload, { to, subject, body })
      if (channel==='sftp') Object.assign(payload, sftp)
      if (channel==='peppol') Object.assign(payload, peppol)
      const res = await request.post('/api/send', payload)
      setResult(res.data)
    } catch (e:any) {
      setError(e.message || 'Send failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Send Invoice</h2>
        <select className="input" value={channel} onChange={e=>setChannel(e.target.value as any)}>
          <option value="email">Email</option>
          <option value="sftp">SFTP</option>
          <option value="peppol">PEPPOL</option>
        </select>

        {channel==='email' && (
          <div className="card">
            <input className="input w-full mb-1" placeholder="To" value={to} onChange={e=>setTo(e.target.value)} />
            <input className="input w-full mb-1" placeholder="Subject" value={subject} onChange={e=>setSubject(e.target.value)} />
            <textarea className="input w-full h-20" placeholder="Body" value={body} onChange={e=>setBody(e.target.value)} />
          </div>
        )}
        {channel==='sftp' && (
          <div className="card">
            <input className="input w-full mb-1" placeholder="Host" value={sftp.host} onChange={e=>setSftp({...sftp,host:e.target.value})} />
            <input className="input w-full mb-1" placeholder="Username" value={sftp.username} onChange={e=>setSftp({...sftp,username:e.target.value})} />
            <input className="input w-full mb-1" placeholder="Path" value={sftp.path} onChange={e=>setSftp({...sftp,path:e.target.value})} />
          </div>
        )}
        {channel==='peppol' && (
          <div className="card">
            <input className="input w-full mb-1" placeholder="Participant ID" value={peppol.participantId} onChange={e=>setPeppol({...peppol,participantId:e.target.value})} />
            <input className="input w-full mb-1" placeholder="Process ID" value={peppol.processId} onChange={e=>setPeppol({...peppol,processId:e.target.value})} />
            <input className="input w-full mb-1" placeholder="Doc Type ID" value={peppol.docTypeId} onChange={e=>setPeppol({...peppol,docTypeId:e.target.value})} />
          </div>
        )}

        <textarea className="border w-full h-48 p-2 font-mono" value={xml} onChange={e=>setXml(e.target.value)} placeholder="Paste your validated XML..." />
        <button className="btn" onClick={handleSend} disabled={loading || !xml}>{loading?'Sending...':'Send'}</button>
        {error && <div className="text-red-600">{error}</div>}
      </div>
      <div>
        {result ? <pre className="card bg-gray-50">{JSON.stringify(result,null,2)}</pre> : <div className="text-gray-500">Delivery report will appear here.</div>}
      </div>
    </div>
  )
}
