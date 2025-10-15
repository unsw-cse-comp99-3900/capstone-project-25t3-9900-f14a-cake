export default function XmlViewer({ xml }: { xml: string }){
  return <pre className="border p-2 rounded bg-gray-50 overflow-auto text-sm whitespace-pre-wrap">{xml}</pre>
}
