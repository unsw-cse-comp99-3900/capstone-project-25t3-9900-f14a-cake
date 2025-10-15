import { useState } from 'react'
import { RULE_SETS, essValidateMulti } from '../../lib/ess'
import EssReport from '../../components/EssReport'
import { exportAsHTML, exportAsJSON, exportAsPDF } from '../../lib/export'

export default function ValidateESS(){
  const [xml, setXml] = useState<string>('')
  const [selected, setSelected] = useState<string[]>([RULE_SETS[0]])
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [schemaOk, setSchemaOk] = useState<boolean|null>(null)

  function toggle(rule: string){
    setSelected(s => s.includes(rule) ? s.filter(r=>r!==rule) : [...s, rule])
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0]; if(!f) return
    const reader = new FileReader()
    reader.onload = () => setXml(String(reader.result))
    reader.readAsText(f)
  }

  async function run(){
    setError(''); setLoading(true); setData(null); setSchemaOk(null)
    try{
      const s = await fetch('/api/schema/validate', { method:'POST', body: xml, headers:{'Content-Type':'application/xml'} })
      if (s.ok){ const js = await s.json(); setSchemaOk(!!js?.ok) } else { setSchemaOk(false) }
      const res = await essValidateMulti(xml, selected)
      setData(res)
    }catch(e:any){
      setError(e.message || 'Validate failed')
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Validate (ESS + Schema)</h2>
        <textarea className="border w-full h-64 p-2 font-mono" value={xml} onChange={e=>setXml(e.target.value)} placeholder="Paste your XML or upload below..." />
        <input type="file" accept=".xml" onChange={onFile}/>
        <div className="card">
          <div className="font-medium mb-1">Rule Sets</div>
          <div className="flex flex-wrap gap-2">
            {RULE_SETS.map(r=>(
              <label key={r} className="flex items-center gap-1">
                <input type="checkbox" checked={selected.includes(r)} onChange={()=>toggle(r)}/>
                <span>{r}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
          <button className="btn" onClick={run} disabled={loading || !xml || selected.length===0}>{loading?'Validating...':'Validate'}</button>
          {data && <button className="btn" onClick={()=>exportAsJSON(data,'ess-report.json')}>Export JSON</button>}
          {data && <button className="btn" onClick={()=>exportAsHTML(data,'ess-report.html')}>Export HTML</button>}
          {data && <button className="btn" onClick={()=>exportAsPDF(data,'ess-report.pdf')}>Export PDF</button>}
          {schemaOk!==null && <span className={schemaOk?'text-green-600':'text-red-600'}>Schema: {schemaOk?'OK':'Failed'}</span>}
        </div>
        {error && <div className="text-red-600">{error}</div>}
      </div>
      <div><EssReport data={data} /></div>
    </div>
  )
}
