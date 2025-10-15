export default function EssReport({ data }: { data:any }){
  if (!data) return <div className="text-gray-500">Run validation to see report.</div>
  const groups = data?.report?.reports || {}
  const keys = Object.keys(groups)
  if (keys.length===0) return <div className="text-gray-500">No report groups.</div>
  return (
    <div className="space-y-4">
      {keys.map(k=>{
        const g = groups[k]
        const rows = g?.firedAssertionErrors || []
        return (
          <section key={k} className="card">
            <div className="font-semibold mb-2">{k} — {g?.successful ? '✅ Passed' : '❌ Failed'}（{rows.length}）</div>
            {rows.length===0 ? <div className="text-gray-500">No errors</div> : (
              <table className="w-full text-sm border-collapse">
                <thead><tr><th className="border p-1 text-left">ID</th><th className="border p-1 text-left">Message</th><th className="border p-1 text-left">XPath</th></tr></thead>
                <tbody>
                  {rows.map((r:any,i:number)=>(
                    <tr key={i}>
                      <td className="border p-1">{r.id}</td>
                      <td className="border p-1">{r.text}</td>
                      <td className="border p-1">{r.location}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )
      })}
    </div>
  )
}
