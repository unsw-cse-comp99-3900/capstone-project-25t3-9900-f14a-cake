import { useState } from 'react'
import * as XLSX from 'xlsx'
import initSqlJs from 'sql.js'
import Tesseract from 'tesseract.js'
import { buildMinimalInvoice } from '../../lib/ubl/buildMinimalInvoice'
import { toUblXml } from '../../lib/ubl/toUblXml'
import XmlViewer from '../../components/XmlViewer'

type CsvRow = { id?: string; issueDate?: string; sellerName?: string; buyerName?: string; currency?: string; taxRate?: number; description?: string; quantity?: number; unitPrice?: number }

export default function CreatePage(){
  const [form, setForm] = useState({
    id: 'INV-001',
    issueDate: new Date().toISOString().slice(0,10),
    sellerName: 'ACME Pty Ltd',
    buyerName: 'UNSW',
    currency: 'AUD',
    taxRate: 0.1,
    lines: [{ description: 'Consulting service', quantity: 2, unitPrice: 120 }],
  })
  const [xml, setXml] = useState<string>('')
  const [batch, setBatch] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  const handleGenerate = () => {
    const invoice = buildMinimalInvoice(form as any)
    setXml(toUblXml(invoice))
  }

  const download = (name='invoice.xml') => {
    const blob = new Blob([xml], {type:'application/xml'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href=url; a.download=name; a.click(); URL.revokeObjectURL(url)
  }

  function onCsvUpload(e: React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0]; if(!f) return
    const reader = new FileReader()
    reader.onload = () => {
      const wb = XLSX.read(reader.result as string, {type:'binary'})
      const ws = wb.Sheets[wb.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json<CsvRow>(ws)
      const xmls:string[] = rows.map((r: CsvRow, i: number)=>{
        const inv = buildMinimalInvoice({
          id: r.id || `INV-${i+1}`,
          issueDate: r.issueDate || new Date().toISOString().slice(0,10),
          sellerName: r.sellerName || form.sellerName,
          buyerName: r.buyerName || form.buyerName,
          currency: r.currency || form.currency,
          taxRate: (typeof r.taxRate === 'number') ? r.taxRate : form.taxRate,
          lines: [{ description: r.description || 'Item', quantity: Number(r.quantity||1), unitPrice: Number(r.unitPrice||1) }]
        })
        return toUblXml(inv)
      })
      setBatch(xmls)
      setMsg(`Imported ${xmls.length} rows from CSV/Excel.`)
    }
    reader.readAsBinaryString(f)
  }

  async function onDbUpload(e: React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0]; if(!f) return
    setBusy(true); setMsg('Reading SQLite...')
    const buf = new Uint8Array(await f.arrayBuffer())
    const SQL = await initSqlJs({})
    const db = new SQL.Database(buf)
    const res = db.exec("SELECT id, issueDate, sellerName, buyerName, currency, taxRate, description, quantity, unitPrice FROM invoices LIMIT 500")
    const rows = ((res[0]?.values || []) as any[]).map((v: any)=>({
      id: String(v[0]||''), issueDate: String(v[1]||''), sellerName: String(v[2]||''), buyerName: String(v[3]||''),
      currency: String(v[4]||'AUD'), taxRate: Number(v[5]||0), description: String(v[6]||'Item'),
      quantity: Number(v[7]||1), unitPrice: Number(v[8]||1)
    }))
    const xmls = rows.map((r:any,i:number)=> toUblXml(buildMinimalInvoice({
      id: r.id || `INV-${i+1}`, issueDate: r.issueDate || new Date().toISOString().slice(0,10),
      sellerName: r.sellerName, buyerName: r.buyerName, currency: r.currency, taxRate: r.taxRate,
      lines: [{ description: r.description, quantity: r.quantity, unitPrice: r.unitPrice }]
    })))
    setBatch(xmls); setBusy(false); setMsg(`Imported ${xmls.length} rows from DB.`)
  }

  async function onImageUpload(e: React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0]; if(!f) return
    setBusy(true); setMsg('Running OCR...')
    const { data } = await (Tesseract as any).recognize(f, 'eng')
    const text = data.text || ''
    const map:any = {}
    text.split(/\r?\n/).forEach((line: string)=>{
      const m = line.match(/^(id|invoice|issueDate|seller|buyer|currency|tax|description|qty|quantity|unitPrice)\s*[:\-]\s*(.+)$/i)
      if (m) map[m[1].toLowerCase()] = m[2].trim()
    })
    const inv = buildMinimalInvoice({
      id: map['id'] || 'INV-OCR-001',
      issueDate: map['issuedate'] || new Date().toISOString().slice(0,10),
      sellerName: map['seller'] || form.sellerName,
      buyerName: map['buyer'] || form.buyerName,
      currency: map['currency'] || 'AUD',
      taxRate: map['tax'] ? parseFloat(map['tax']) : form.taxRate,
      lines: [{ description: map['description'] || 'Item', quantity: Number(map['qty']||map['quantity']||1), unitPrice: Number(map['unitprice']||1) }]
    })
    setXml(toUblXml(inv)); setBusy(false); setMsg('OCR parsed → populated form & XML.')
  }

  const downloadZip = async () => {
    const { default: JSZip } = await import('jszip')
    const zip = new JSZip()
    batch.forEach((x:string,i:number)=>zip.file(`invoice-${i+1}.xml`, x))
    const blob = await zip.generateAsync({type:'blob'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href=url; a.download='invoices.zip'; a.click(); URL.revokeObjectURL(url)
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Create Minimal Invoice</h2>
        {busy && <div className="text-sm text-gray-600">Processing...</div>}
        {msg && <div className="text-sm text-gray-600">{msg}</div>}
        <div className="grid gap-2">
          <input className="input" placeholder="Invoice ID" value={form.id} onChange={e=>setForm({...form,id:e.target.value})}/>
          <input className="input" type="date" value={form.issueDate} onChange={e=>setForm({...form,issueDate:e.target.value})}/>
          <input className="input" placeholder="Seller Name" value={form.sellerName} onChange={e=>setForm({...form,sellerName:e.target.value})}/>
          <input className="input" placeholder="Buyer Name" value={form.buyerName} onChange={e=>setForm({...form,buyerName:e.target.value})}/>
          <input className="input" placeholder="Currency" value={form.currency} onChange={e=>setForm({...form,currency:e.target.value})}/>
          <input className="input" type="number" step="0.01" placeholder="Tax rate" value={form.taxRate} onChange={e=>setForm({...form,taxRate:parseFloat(e.target.value)})}/>
          <div className="card">
            <div className="font-medium mb-1">Line 1</div>
            <input className="input w-full mb-1" placeholder="Description" value={form.lines[0].description} onChange={e=>setForm({...form,lines:[{...form.lines[0],description:e.target.value}]})}/>
            <div className="grid grid-cols-2 gap-2">
              <input className="input" type="number" placeholder="Quantity" value={form.lines[0].quantity} onChange={e=>setForm({...form,lines:[{...form.lines[0],quantity:parseFloat(e.target.value)}]})}/>
              <input className="input" type="number" placeholder="Unit Price" value={form.lines[0].unitPrice} onChange={e=>setForm({...form,lines:[{...form.lines[0],unitPrice:parseFloat(e.target.value)}]})}/>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn" onClick={handleGenerate}>Generate XML</button>
            {xml && <button className="btn" onClick={()=>download(`${form.id}.xml`)}>Download</button>}
          </div>

          <div className="card">
            <div className="font-medium mb-1">Batch: CSV/Excel</div>
            <input type="file" accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" onChange={onCsvUpload}/>
            {batch.length>0 && <button className="btn mt-2" onClick={downloadZip}>Download ZIP ({batch.length})</button>}
          </div>

          <div className="card">
            <div className="font-medium mb-1">Import from SQLite DB</div>
            <input type="file" accept=".sqlite,.db" onChange={onDbUpload}/>
          </div>

          <div className="card">
            <div className="font-medium mb-1">OCR from Image</div>
            <input type="file" accept="image/*" onChange={onImageUpload}/>
          </div>
        </div>
      </div>
      <div>{xml ? <XmlViewer xml={xml} /> : <div className="text-gray-500">XML preview will appear here.</div>}</div>
    </div>
  )
}
