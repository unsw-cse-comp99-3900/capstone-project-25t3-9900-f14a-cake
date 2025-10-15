export interface MinimalInvoice {
  id: string; issueDate: string;
  seller: { name: string; abn?: string };
  buyer: { name: string; abn?: string };
  currency: string;
  lines: { description: string; quantity: number; unitPrice: number }[];
  taxTotal?: number;
  legalMonetaryTotal: { payableAmount: number };
}
