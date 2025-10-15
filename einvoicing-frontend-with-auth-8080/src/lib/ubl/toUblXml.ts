import { MinimalInvoice } from './types'
export function toUblXml(inv: MinimalInvoice){
  const lineXml = inv.lines.map((l,i)=>
    `<cac:InvoiceLine>
       <cbc:ID>${i+1}</cbc:ID>
       <cbc:InvoicedQuantity>${l.quantity}</cbc:InvoicedQuantity>
       <cbc:LineExtensionAmount>${(l.quantity*l.unitPrice).toFixed(2)}</cbc:LineExtensionAmount>
       <cac:Item><cbc:Description>${l.description}</cbc:Description></cac:Item>
       <cac:Price><cbc:PriceAmount>${l.unitPrice}</cbc:PriceAmount></cac:Price>
     </cac:InvoiceLine>`).join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:ID>${inv.id}</cbc:ID>
  <cbc:IssueDate>${inv.issueDate}</cbc:IssueDate>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyName><cbc:Name>${inv.seller.name}</cbc:Name></cac:PartyName></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyName><cbc:Name>${inv.buyer.name}</cbc:Name></cac:PartyName></cac:Party></cac:AccountingCustomerParty>
  <cbc:DocumentCurrencyCode>${inv.currency}</cbc:DocumentCurrencyCode>
  ${lineXml}
  <cac:LegalMonetaryTotal><cbc:PayableAmount>${inv.legalMonetaryTotal.payableAmount}</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>`
}
