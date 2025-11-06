"""UBL XML generation service"""
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_ubl_xml(data):
    """生成UBL格式的XML"""
    # 命名空间
    NS_INVOICE = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
    NS_CAC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    NS_CBC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    
    # 注册命名空间
    ET.register_namespace('', NS_INVOICE)
    ET.register_namespace('cac', NS_CAC)
    ET.register_namespace('cbc', NS_CBC)
    
    cbc = '{' + NS_CBC + '}'
    cac = '{' + NS_CAC + '}'
    
    # 创建根元素
    invoice = ET.Element('{' + NS_INVOICE + '}Invoice')
    
    # 发票头部（固定值）
    ET.SubElement(invoice, cbc + 'CustomizationID').text = 'urn:cen.eu:en16931:2017#conformant#urn:fdc:peppol.eu:2017:poacc:billing:international:aunz:3.0'
    ET.SubElement(invoice, cbc + 'ProfileID').text = 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0'
    
    # 基本信息
    info = data.get('invoice_info', {})
    ET.SubElement(invoice, cbc + 'ID').text = info.get('invoice_number', 'INV-000')
    ET.SubElement(invoice, cbc + 'IssueDate').text = info.get('issue_date', '')
    ET.SubElement(invoice, cbc + 'DueDate').text = info.get('due_date', '')
    ET.SubElement(invoice, cbc + 'InvoiceTypeCode').text = '380'
    ET.SubElement(invoice, cbc + 'DocumentCurrencyCode').text = info.get('currency_code', 'AUD')
    ET.SubElement(invoice, cbc + 'BuyerReference').text = info.get('buyer_reference', 'N/A')
    
    # 供应商信息
    supplier = data.get('supplier', {})
    supplier_party = ET.SubElement(invoice, cac + 'AccountingSupplierParty')
    supplier_party_elem = ET.SubElement(supplier_party, cac + 'Party')
    
    supplier_abn = supplier.get('abn', '').replace(' ', '')
    ET.SubElement(supplier_party_elem, cbc + 'EndpointID', schemeID='0151').text = supplier_abn
    
    supplier_name_elem = ET.SubElement(supplier_party_elem, cac + 'PartyName')
    ET.SubElement(supplier_name_elem, cbc + 'Name').text = supplier.get('name', '')
    
    supplier_address = ET.SubElement(supplier_party_elem, cac + 'PostalAddress')
    ET.SubElement(supplier_address, cbc + 'StreetName').text = supplier.get('street_name', '')
    ET.SubElement(supplier_address, cbc + 'CityName').text = supplier.get('city_name', '')
    ET.SubElement(supplier_address, cbc + 'PostalZone').text = supplier.get('postal_zone', '')
    supplier_country = ET.SubElement(supplier_address, cac + 'Country')
    ET.SubElement(supplier_country, cbc + 'IdentificationCode').text = 'AU'
    
    supplier_legal = ET.SubElement(supplier_party_elem, cac + 'PartyLegalEntity')
    ET.SubElement(supplier_legal, cbc + 'RegistrationName').text = supplier.get('name', '')
    ET.SubElement(supplier_legal, cbc + 'CompanyID', schemeID='0151').text = supplier_abn
    
    # 客户信息
    customer = data.get('customer', {})
    customer_party = ET.SubElement(invoice, cac + 'AccountingCustomerParty')
    customer_party_elem = ET.SubElement(customer_party, cac + 'Party')
    
    customer_abn = customer.get('abn', '').replace(' ', '')
    ET.SubElement(customer_party_elem, cbc + 'EndpointID', schemeID='0151').text = customer_abn
    
    customer_name_elem = ET.SubElement(customer_party_elem, cac + 'PartyName')
    ET.SubElement(customer_name_elem, cbc + 'Name').text = customer.get('name', '')
    
    customer_address = ET.SubElement(customer_party_elem, cac + 'PostalAddress')
    ET.SubElement(customer_address, cbc + 'StreetName').text = customer.get('street_name', '')
    ET.SubElement(customer_address, cbc + 'CityName').text = customer.get('city_name', '')
    ET.SubElement(customer_address, cbc + 'PostalZone').text = customer.get('postal_zone', '')
    customer_country = ET.SubElement(customer_address, cac + 'Country')
    ET.SubElement(customer_country, cbc + 'IdentificationCode').text = 'AU'
    
    customer_legal = ET.SubElement(customer_party_elem, cac + 'PartyLegalEntity')
    ET.SubElement(customer_legal, cbc + 'RegistrationName').text = customer.get('name', '')
    ET.SubElement(customer_legal, cbc + 'CompanyID', schemeID='0151').text = customer_abn
    
    # 计算税额（按税率分组）
    line_items = data.get('line_items', [])
    currency = info.get('currency_code', 'AUD')
    
    # 按税率分组计算
    tax_groups = {}
    total_line_extension = 0.0
    
    for item in line_items:
        line_total = float(item.get('line_total', 0))
        tax_percent = float(item.get('tax_percent', 0))
        
        total_line_extension += line_total
        
        if tax_percent not in tax_groups:
            tax_groups[tax_percent] = {'taxable': 0.0, 'tax': 0.0}
        
        tax_groups[tax_percent]['taxable'] += line_total
        tax_groups[tax_percent]['tax'] += line_total * tax_percent / 100
    
    # 税额汇总
    total_tax_amount = sum(group['tax'] for group in tax_groups.values())
    
    tax_total = ET.SubElement(invoice, cac + 'TaxTotal')
    ET.SubElement(tax_total, cbc + 'TaxAmount', currencyID=currency).text = f'{total_tax_amount:.2f}'
    
    for tax_percent, amounts in sorted(tax_groups.items(), reverse=True):
        tax_subtotal = ET.SubElement(tax_total, cac + 'TaxSubtotal')
        ET.SubElement(tax_subtotal, cbc + 'TaxableAmount', currencyID=currency).text = f"{amounts['taxable']:.2f}"
        ET.SubElement(tax_subtotal, cbc + 'TaxAmount', currencyID=currency).text = f"{amounts['tax']:.2f}"
        
        tax_category = ET.SubElement(tax_subtotal, cac + 'TaxCategory')
        ET.SubElement(tax_category, cbc + 'ID').text = 'S'
        ET.SubElement(tax_category, cbc + 'Percent').text = f'{tax_percent:.2f}'
        
        tax_scheme = ET.SubElement(tax_category, cac + 'TaxScheme')
        ET.SubElement(tax_scheme, cbc + 'ID').text = 'GST'
    
    # 金额汇总
    total_with_tax = total_line_extension + total_tax_amount
    
    monetary_total = ET.SubElement(invoice, cac + 'LegalMonetaryTotal')
    ET.SubElement(monetary_total, cbc + 'LineExtensionAmount', currencyID=currency).text = f'{total_line_extension:.2f}'
    ET.SubElement(monetary_total, cbc + 'TaxExclusiveAmount', currencyID=currency).text = f'{total_line_extension:.2f}'
    ET.SubElement(monetary_total, cbc + 'TaxInclusiveAmount', currencyID=currency).text = f'{total_with_tax:.2f}'
    ET.SubElement(monetary_total, cbc + 'PayableAmount', currencyID=currency).text = f'{total_with_tax:.2f}'
    
    # 商品明细
    for idx, item in enumerate(line_items, 1):
        invoice_line = ET.SubElement(invoice, cac + 'InvoiceLine')
        ET.SubElement(invoice_line, cbc + 'ID').text = str(idx)
        
        quantity = float(item.get('quantity', 1))
        unit_code = item.get('unit_code', 'EA')
        ET.SubElement(invoice_line, cbc + 'InvoicedQuantity', unitCode=unit_code).text = f'{quantity:.0f}'
        
        line_total = float(item.get('line_total', 0))
        ET.SubElement(invoice_line, cbc + 'LineExtensionAmount', currencyID=currency).text = f'{line_total:.2f}'
        
        item_elem = ET.SubElement(invoice_line, cac + 'Item')
        ET.SubElement(item_elem, cbc + 'Name').text = item.get('name', '')
        
        tax_percent = float(item.get('tax_percent', 0))
        classified_tax = ET.SubElement(item_elem, cac + 'ClassifiedTaxCategory')
        ET.SubElement(classified_tax, cbc + 'ID').text = 'S'
        ET.SubElement(classified_tax, cbc + 'Percent').text = f'{tax_percent:.2f}'
        
        tax_scheme = ET.SubElement(classified_tax, cac + 'TaxScheme')
        ET.SubElement(tax_scheme, cbc + 'ID').text = 'GST'
        
        price_elem = ET.SubElement(invoice_line, cac + 'Price')
        unit_price = float(item.get('unit_price', 0))
        ET.SubElement(price_elem, cbc + 'PriceAmount', currencyID=currency).text = f'{unit_price:.2f}'
    
    # 格式化输出
    xml_str = ET.tostring(invoice, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

