import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from datetime import datetime, timedelta


# ========= 工具函数 =========

def safe_get(d, *keys, default=None):
    """安全取嵌套键"""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def abn_is_valid(abn: str) -> bool:
    """验证 ABN 格式"""
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
    return "53004085616"  # fallback test ABN


def parse_date_any(s: str) -> str:
    """通用日期解析"""
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


# ========= 主函数 =========

def json_to_ubl_invoice(data: dict):
    """
    将 Veryfi JSON 转换为 UBL 发票 XML。
    """
    missing, warnings = [], []

    # ✅ 定义 src（防止未定义错误）
    src = data.get("fields", {}) or data

    # 命名空间
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

    # ===== 基本信息 =====
    document_type = src.get("document_type", "invoice")
    document_title = src.get("document_title", "Tax invoice")
    invoice_id = src.get("invoice_number") or "INV-000"
    reference_number = src.get("reference_number", "N/A")
    issue_date = parse_date_any(src.get("date")) or datetime.today().strftime("%Y-%m-%d")
    due_date = parse_date_any(src.get("due_date")) or (
        datetime.strptime(issue_date, "%Y-%m-%d") + timedelta(days=14)
    ).strftime("%Y-%m-%d")
    currency = src.get("currency_code", "AUD")
    subtotal = float(src.get("subtotal", 0))
    country_code = src.get("country_code", "AU")
    created_date = parse_date_any(src.get("created_date"))
    updated_date = parse_date_any(src.get("updated_date"))

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
    ET.SubElement(invoice, cbc + "SubtotalAmount", currencyID=currency).text = f"{subtotal:.2f}"

    # ===== Supplier =====
    vendor = src.get("vendor", {}) or {}
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
    bill_to = src.get("bill_to", {}) or {}
    customer_name = bill_to.get("name") or "Unknown Customer"
    customer_address = bill_to.get("address") or "Address Not Provided"
    customer_vat = bill_to.get("vat_number") or ""
    customer_abn = normalize_abn(customer_vat)
    if not bill_to.get("name"):
        missing.append("customer_name (客户名称)")

    cac_cust = ET.SubElement(invoice, cac + "AccountingCustomerParty")
    cust_party = ET.SubElement(cac_cust, cac + "Party")
    ET.SubElement(cust_party, cbc + "EndpointID", schemeID="0151").text = customer_abn
    ET.SubElement(ET.SubElement(cust_party, cac + "PartyName"), cbc + "Name").text = customer_name
    caddr = ET.SubElement(cust_party, cac + "PostalAddress")
    ET.SubElement(caddr, cbc + "StreetName").text = customer_address.split("\n")[0]

    ET.SubElement(invoice, cbc + "BuyerReference").text = customer_name

    # ===== 明细行 =====
    line_items = src.get("line_items", [])
    total_taxable = 0.0
    for i, item in enumerate(line_items, start=1):
        desc = item.get("description") or "Item"
        qty = float(item.get("quantity") or 1.0)
        price = float(item.get("price") or 0.0)
        total = float(item.get("total") or price * qty)
        total_taxable += total

        line = ET.SubElement(invoice, cac + "InvoiceLine")
        ET.SubElement(line, cbc + "ID").text = str(i)
        ET.SubElement(line, cbc + "InvoicedQuantity").text = str(int(qty))
        ET.SubElement(line, cbc + "LineExtensionAmount", currencyID=currency).text = f"{total:.2f}"
        item_tag = ET.SubElement(line, cac + "Item")
        ET.SubElement(item_tag, cbc + "Description").text = desc
        price_tag = ET.SubElement(line, cac + "Price")
        ET.SubElement(price_tag, cbc + "PriceAmount", currencyID=currency).text = f"{price:.2f}"

    # ===== 税 =====
    tax_total = safe_get(src, "tax_lines", 0, "total", default=None)
    tax_rate = safe_get(src, "tax_lines", 0, "rate", default=10.0)
    if tax_total is None:
        tax_total = total_taxable * tax_rate / 100
        missing.append("tax_total (税额)")

    cac_tax = ET.SubElement(invoice, cac + "TaxTotal")
    ET.SubElement(cac_tax, cbc + "TaxAmount", currencyID=currency).text = f"{tax_total:.2f}"
    tax_sub = ET.SubElement(cac_tax, cac + "TaxSubtotal")
    ET.SubElement(tax_sub, cbc + "TaxableAmount", currencyID=currency).text = f"{total_taxable:.2f}"
    ET.SubElement(tax_sub, cbc + "TaxAmount", currencyID=currency).text = f"{tax_total:.2f}"
    tax_cat = ET.SubElement(tax_sub, cac + "TaxCategory")
    ET.SubElement(tax_cat, cbc + "ID").text = "S"
    ET.SubElement(tax_cat, cbc + "Percent").text = f"{float(tax_rate):.2f}"
    ET.SubElement(ET.SubElement(tax_cat, cac + "TaxScheme"), cbc + "ID").text = "GST"

    # ===== 总金额 =====
    total_amount = src.get("total") or total_taxable + tax_total
    ET.SubElement(ET.SubElement(invoice, cac + "LegalMonetaryTotal"), cbc + "PayableAmount", currencyID=currency).text = f"{float(total_amount):.2f}"

    # ===== 输出 =====
    xml_str = ET.tostring(invoice, encoding="utf-8")
    xml_output = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    summary = {
        "document_type": document_type,
        "document_title": document_title,
        "invoice_number": invoice_id,
        "reference_number": reference_number,
        "date": issue_date,
        "due_date": due_date,
        "currency_code": currency,
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{float(tax_total):.2f}",
        "total": f"{float(total_amount):.2f}",
        "country_code": country_code,
        "created_date": created_date or updated_date,
    }

    return {
        "xml": xml_output,
        "summary": summary,
        "missing_fields": missing,
        "warnings": warnings,
    }
