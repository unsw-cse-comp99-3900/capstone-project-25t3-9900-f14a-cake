import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from datetime import datetime, timedelta


def safe_get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def get_any(data, candidates, default=None):
    for path in candidates:
        v = safe_get(data, *path, default=None)
        if v not in (None, ""):
            return v
    return default


def abn_is_valid(abn: str) -> bool:
    if not abn or not abn.isdigit() or len(abn) != 11:
        return False
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    digits = [int(x) for x in abn]
    digits[0] -= 1
    total = sum(d * w for d, w in zip(digits, weights))
    return total % 89 == 0


def normalize_abn(abn: str) -> str:
    digits = re.sub(r"\D", "", abn or "")
    if len(digits) == 11 and abn_is_valid(digits):
        return digits
    return "53004085616"  # 测试 ABN


def parse_date_any(s: str) -> str:
    if not s:
        return None
    s = s.strip().replace("/", "-")
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d-%m-%y"]:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return None


def json_to_ubl_invoice(data: dict) -> dict:
    """从 Veryfi JSON 生成完整合规的 UBL 发票 XML"""
    src = data.get("fields", {}) or data
    warnings, missing = [], []

    # 命名空间定义
    NS = {
        "": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }
    for pfx, uri in NS.items():
        ET.register_namespace(pfx, uri)
    cbc = "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
    cac = "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"

    invoice = ET.Element("{" + NS[""] + "}Invoice")

    # ======= 基本信息 =======
    invoice_id = get_any(src, [("invoice_number",), ("invoice_number", "value")]) or "INV-000"
    if not get_any(src, [("invoice_number",), ("invoice_number", "value")]):
        missing.append("invoice_number (发票号)")

    issue_date = parse_date_any(get_any(src, [("date",), ("date", "value")])) or datetime.now().strftime("%Y-%m-%d")
    print(issue_date)
    due_date = parse_date_any(data.get("due_date")) or (
        datetime.strptime(issue_date, "%Y-%m-%d") + timedelta(days=14)
    ).strftime("%Y-%m-%d")

    currency = data.get("currency_code", "AUD")
    subtotal = float(data.get("subtotal", 0.0))
    total = float(data.get("total", subtotal))
    tax_total = safe_get(data, "tax_lines", 0, "total", default=0.0)
    tax_rate = safe_get(data, "tax_lines", 0, "rate", default=10.0)
    country_code = data.get("country_code", "AU")
    created_date = parse_date_any(data.get("created_date") or data.get("updated_date"))

    document_type = data.get("document_type", "Invoice")
    document_title = data.get("document_title", f"Invoice {invoice_id}")
    reference_number = data.get("reference_number", invoice_id)

    # ===== Header =====
    ET.SubElement(invoice, cbc + "CustomizationID").text = (
        "urn:cen.eu:en16931:2017#conformant#"
        "urn:fdc:peppol.eu:2017:poacc:billing:international:aunz:3.0"
    )
    ET.SubElement(invoice, cbc + "ProfileID").text = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    ET.SubElement(invoice, cbc + "ID").text = invoice_id
    ET.SubElement(invoice, cbc + "IssueDate").text = issue_date
    ET.SubElement(invoice, cbc + "DueDate").text = due_date
    ET.SubElement(invoice, cbc + "InvoiceTypeCode").text = "380"
    ET.SubElement(invoice, cbc + "DocumentCurrencyCode").text = currency
    ET.SubElement(invoice, cbc + "DocumentType").text = document_type
    ET.SubElement(invoice, cbc + "DocumentTitle").text = document_title
    ET.SubElement(invoice, cbc + "ReferenceNumber").text = reference_number
    ET.SubElement(invoice, cbc + "CountryCode").text = country_code

    # ===== Supplier =====
    vendor = data.get("vendor", {}) or {}
    supplier_name = vendor.get("name") or "Unknown Supplier"
    supplier_abn = normalize_abn(vendor.get("abn_number") or vendor.get("vat_number"))
    supplier_address = vendor.get("address") or "Address Not Provided"
    if supplier_abn == "53004085616":
        warnings.append("⚠️ Supplier ABN 缺失或无效，已填入测试 ABN")

    cac_sup = ET.SubElement(invoice, cac + "AccountingSupplierParty")
    sup_party = ET.SubElement(cac_sup, cac + "Party")
    ET.SubElement(sup_party, cbc + "EndpointID", schemeID="0151").text = supplier_abn
    ET.SubElement(ET.SubElement(sup_party, cac + "PartyName"), cbc + "Name").text = supplier_name
    addr = ET.SubElement(sup_party, cac + "PostalAddress")
    ET.SubElement(addr, cbc + "StreetName").text = supplier_address.split("\n")[0]

    # ===== Customer =====
    bill_to = data.get("bill_to", {}) or {}
    customer_name = bill_to.get("name") or "Unknown Customer"
    customer_address = bill_to.get("address") or "Address Not Provided"
    customer_abn = normalize_abn(bill_to.get("vat_number"))
    if not bill_to.get("name"):
        missing.append("customer_name (客户名称)")

    cac_cust = ET.SubElement(invoice, cac + "AccountingCustomerParty")
    cust_party = ET.SubElement(cac_cust, cac + "Party")
    ET.SubElement(cust_party, cbc + "EndpointID", schemeID="0151").text = customer_abn
    ET.SubElement(ET.SubElement(cust_party, cac + "PartyName"), cbc + "Name").text = customer_name
    caddr = ET.SubElement(cust_party, cac + "PostalAddress")
    ET.SubElement(caddr, cbc + "StreetName").text = customer_address.split("\n")[0]

    # ===== 明细行 =====
    total_taxable = 0.0
    for i, item in enumerate(data.get("line_items", []), start=1):
        desc = item.get("description") or "Item"
        qty = float(item.get("quantity") or 1.0)
        price = float(item.get("price") or 0.0)
        total_line = float(item.get("total") or qty * price)
        total_taxable += total_line

        line = ET.SubElement(invoice, cac + "InvoiceLine")
        ET.SubElement(line, cbc + "ID").text = str(i)
        ET.SubElement(line, cbc + "InvoicedQuantity").text = str(int(qty))
        ET.SubElement(line, cbc + "LineExtensionAmount", currencyID=currency).text = f"{total_line:.2f}"
        item_tag = ET.SubElement(line, cac + "Item")
        ET.SubElement(item_tag, cbc + "Description").text = desc
        price_tag = ET.SubElement(line, cac + "Price")
        ET.SubElement(price_tag, cbc + "PriceAmount", currencyID=currency).text = f"{price:.2f}"

    # ===== 税 =====
    cac_tax = ET.SubElement(invoice, cac + "TaxTotal")
    ET.SubElement(cac_tax, cbc + "TaxAmount", currencyID=currency).text = f"{float(tax_total):.2f}"
    tax_sub = ET.SubElement(cac_tax, cac + "TaxSubtotal")
    ET.SubElement(tax_sub, cbc + "TaxableAmount", currencyID=currency).text = f"{total_taxable:.2f}"
    ET.SubElement(tax_sub, cbc + "TaxAmount", currencyID=currency).text = f"{float(tax_total):.2f}"
    tax_cat = ET.SubElement(tax_sub, cac + "TaxCategory")
    ET.SubElement(tax_cat, cbc + "ID").text = "S"
    ET.SubElement(tax_cat, cbc + "Percent").text = f"{float(tax_rate):.2f}"
    ET.SubElement(ET.SubElement(tax_cat, cac + "TaxScheme"), cbc + "ID").text = "GST"

    # ===== 总金额 =====
    ET.SubElement(ET.SubElement(invoice, cac + "LegalMonetaryTotal"), cbc + "PayableAmount", currencyID=currency).text = f"{float(total):.2f}"

    # ===== 输出 XML =====
    xml_str = ET.tostring(invoice, encoding="utf-8")
    xml_output = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    summary = {
        "document_type": document_type,
        "document_title": document_title,
        "invoice_number": invoice_id,
        "reference_number": reference_number,
        "issue_date": issue_date,
        "due_date": due_date,
        "currency_code": currency,
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{float(tax_total):.2f}",
        "total": f"{float(total):.2f}",
        "country_code": country_code,
        "created_date": created_date,
        "supplier_name": supplier_name,
        "customer_name": customer_name,
    }

    return {
        "xml": xml_output,
        "summary": summary,
        "missing_fields": missing,
        "warnings": warnings,
    }
