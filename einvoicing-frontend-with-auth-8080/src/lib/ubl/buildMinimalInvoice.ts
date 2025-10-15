import { MinimalInvoice } from './types'
type Line = { description: string; quantity: number; unitPrice: number }
export function buildMinimalInvoice(form: any): MinimalInvoice {
  const lines: Line[] = form.lines.map((l: any) => ({
    description: String(l.description),
    quantity: Number(l.quantity),
    unitPrice: Number(l.unitPrice),
  }))
  const subtotal = lines.reduce((sum: number, line: Line) => sum + line.quantity * line.unitPrice, 0)
  const tax = form.taxRate ? +(subtotal * Number(form.taxRate)).toFixed(2) : 0
  const total = +(subtotal + tax).toFixed(2)
  return {
    id: String(form.id),
    issueDate: String(form.issueDate),
    seller: { name: String(form.sellerName || '') },
    buyer:  { name: String(form.buyerName || '') },
    currency: String(form.currency || 'AUD'),
    lines,
    taxTotal: tax,
    legalMonetaryTotal: { payableAmount: total },
  }
}
