import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from datetime import datetime, timedelta


# ================= 工具函数 =================

def safe_get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def get_any(data, candidates, default=None):
    """尝试多个路径"""
    for path in candidates:
        v = safe_get(data, *path, default=None)
        if v not in (None, ""):
            return v
    return default


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
    return "53004085616"  # 测试 ABN


def parse_date_any(s: str) -> str:
    """多格式日期解析"""
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


# ================= 主函数 =================

def json_to_ubl_invoice(data: dict) -> str:
    """从 Veryfi JSON 生成完整合规的 UBL 发票 XML（带缺失检测与自动补齐）"""
    src = data.get("fields", {}) or data
    warnings, missing = [], []

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

    # ======= 基本信息 =======
    invoice_id = get_any(src, [("invoice_number",), ("invoice_number", "value")])
    if not invoice_id:
        missing.append("invoice_number (发票号)")
        invoice_id = "INV-000"

    issue_date = parse_date_any(get_any(src, [("date",), ("date", "value")]))
    if not issue_date:
        missing.append("issue_date (开票日期)")
        issue_date = datetime.today().strftime("%Y-%m-%d")

    due_date = parse_date_any(get_any(src, [("due_date",), ("due_date", "value")]))
    if not due_date:
        missing.append("due_date (到期日)")
        due_date = (datetime.strptime(issue_date, "%Y-%m-%d") + timedelta(days=14)).strftime("%Y-%m-%d")

    currency = get_any(src, [("currency_code",), ("locale", "fields", "currency", "value")])
    if not currency:
        missing.append("currency_code (币种)")
        currency = "AUD"

    # ======= Header =======
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

    # ======= Supplier =======
    supplier_name = get_any(src, [("supplier_name","value"), ("vendor","name")])
    if not supplier_name:
        missing.append("supplier_name (供应商名称)")
        supplier_name = "Unknown Supplier"

    supplier_abn = normalize_abn(get_any(src, [
        ("supplier_company_registration","items",0,"fields","number","value"),
        ("vendor","abn_number"), ("vendor","vat_number")
    ]))
    if supplier_abn == "53004085616":
        warnings.append("⚠️ supplier ABN 缺失或不合法，已自动补为测试 ABN")

    cac_sup = ET.SubElement(invoice, cac + "AccountingSupplierParty")
    sup_party = ET.SubElement(cac_sup, cac + "Party")
    ET.SubElement(sup_party, cbc + "EndpointID", schemeID="0151").text = supplier_abn
    sup_name = ET.SubElement(sup_party, cac + "PartyName")
    ET.SubElement(sup_name, cbc + "Name").text = supplier_name

    # ======= Customer =======
    customer_name = get_any(src, [("customer_name","value"), ("bill_to","name")])
    if not customer_name:
        missing.append("customer_name (客户名称)")
        customer_name = "Unknown Customer"

    customer_abn = normalize_abn(get_any(src, [
        ("customer_company_registration","items",0,"fields","number","value"),
        ("bill_to","vat_number")
    ]))
    customer_address = get_any(src, [("bill_to","address")])
    if not customer_address:
        missing.append("customer_address (客户地址)")
        customer_address = "Address Not Provided"
    customer_postcode = get_any(src, [("customer_address","fields","postal_code","value")], default="0000")

    cac_cust = ET.SubElement(invoice, cac + "AccountingCustomerParty")
    cust_party = ET.SubElement(cac_cust, cac + "Party")
    ET.SubElement(cust_party, cbc + "EndpointID", schemeID="0151").text = customer_abn
    cname = ET.SubElement(cust_party, cac + "PartyName")
    ET.SubElement(cname, cbc + "Name").text = customer_name

    caddr = ET.SubElement(cust_party, cac + "PostalAddress")
    ET.SubElement(caddr, cbc + "StreetName").text = customer_address.split("\n")[0]
    ET.SubElement(caddr, cbc + "PostalZone").text = customer_postcode

    # ======= Buyer Reference (R003) =======
    ET.SubElement(invoice, cbc + "BuyerReference").text = customer_name

    # ======= 明细行 =======
    line_items = get_any(src, [("line_items",), ("line_items","items")], default=[])
    total_taxable = 0.0
    if not line_items:
        missing.append("line_items (明细行)")

    for i, raw in enumerate(line_items, start=1):
        it = raw.get("fields", raw)
        desc = get_any(it, [("description","value"), ("description",)], default="Item")
        qty = float(get_any(it, [("quantity","value"), ("quantity",)], default=1))
        price = float(get_any(it, [("unit_price","value"), ("price",)], default=0.0))
        total = float(get_any(it, [("total_price","value"), ("total",)], default=price * qty))
        total_taxable += total

        line = ET.SubElement(invoice, cac + "InvoiceLine")
        ET.SubElement(line, cbc + "ID").text = str(i)
        ET.SubElement(line, cbc + "InvoicedQuantity").text = str(int(qty))
        ET.SubElement(line, cbc + "LineExtensionAmount", currencyID=currency).text = f"{total:.2f}"
        item_tag = ET.SubElement(line, cac + "Item")
        ET.SubElement(item_tag, cbc + "Description").text = desc
        price_tag = ET.SubElement(line, cac + "Price")
        ET.SubElement(price_tag, cbc + "PriceAmount", currencyID=currency).text = f"{price:.3f}"

    # ======= Tax =======
    tax_total = get_any(src, [("tax",), ("tax_lines",0,"total")], default=None)
    tax_rate = get_any(src, [("tax_lines",0,"rate")], default=10.0)

    if tax_total is None:
        missing.append("tax_total (税额)")
        tax_total = total_taxable * float(tax_rate) / 100

    cac_tax = ET.SubElement(invoice, cac + "TaxTotal")
    ET.SubElement(cac_tax, cbc + "TaxAmount", currencyID=currency).text = f"{float(tax_total):.2f}"
    tax_sub = ET.SubElement(cac_tax, cac + "TaxSubtotal")
    ET.SubElement(tax_sub, cbc + "TaxableAmount", currencyID=currency).text = f"{total_taxable:.2f}"
    ET.SubElement(tax_sub, cbc + "TaxAmount", currencyID=currency).text = f"{float(tax_total):.2f}"
    tax_cat = ET.SubElement(tax_sub, cac + "TaxCategory")
    ET.SubElement(tax_cat, cbc + "ID").text = "S"
    ET.SubElement(tax_cat, cbc + "Percent").text = f"{float(tax_rate):.2f}"
    tax_scheme = ET.SubElement(tax_cat, cac + "TaxScheme")
    ET.SubElement(tax_scheme, cbc + "ID").text = "GST"

    # ======= 合计 =======
    total_amount = get_any(src, [("total_amount","value"), ("total",)], default=None)
    if total_amount is None:
        missing.append("total_amount (总金额)")
        total_amount = total_taxable + float(tax_total)

    cac_total = ET.SubElement(invoice, cac + "LegalMonetaryTotal")
    ET.SubElement(cac_total, cbc + "PayableAmount", currencyID=currency).text = f"{float(total_amount):.2f}"

    # ======= 打印缺失报告 =======
    print("\n==== 🧾 发票检查报告 ====")
    if missing:
        print("以下字段缺失并已自动补全：")
        for field in missing:
            print(f"  - {field}")
    else:
        print("✅ 未发现关键字段缺失")

    if warnings:
        print("\n额外警告：")
        for w in warnings:
            print(" ", w)
    print("========================\n")

    # 输出 XML
    xml_str = ET.tostring(invoice, encoding="utf-8")
    return minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


# ========== 主入口 ==========
if __name__ == "__main__":
    with open("3page_result.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    xml_output = json_to_ubl_invoice(data)
    with open("invoice.xml", "w", encoding="utf-8") as f:
        f.write(xml_output)

    print("✅ UBL 发票 XML 已生成: invoice.xml")
