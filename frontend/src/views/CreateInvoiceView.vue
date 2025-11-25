<script setup>
/**
 * CreateInvoiceView component for creating and editing invoices.
 * 
 * @component CreateInvoiceView
 * @description Main view for creating new invoices or editing existing ones.
 * Supports multi-step workflow: upload/OCR, form filling, XML generation, validation, and email sending.
 * Can operate in create mode or edit mode (when invoice ID is provided in route).
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Download, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInvoiceForm } from '@/composables/useInvoiceForm'
import { useFileUpload } from '@/composables/useFileUpload'
import { useXmlOperations } from '@/composables/useXmlOperations'
import api from '@/utils/axios'
import FileUploader from '@/components/FileUploader.vue'
import LineItemsEditor from '@/components/LineItemsEditor.vue'
import XmlValidator from '@/components/XmlValidator.vue'
import SessionWarning from '@/components/SessionWarning.vue'
import EmailSender from '@/components/EmailSender.vue'

const router = useRouter()
const route = useRoute()

// Check if this is edit mode
const isEditMode = computed(() => !!route.params.id)
const invoiceId = ref(null)
const isLoadingInvoice = ref(false)

// Initialize invoiceId and currentStep based on route
if (route.params.id) {
  invoiceId.value = parseInt(route.params.id)
}

const currentStep = ref(route.params.id ? 1 : 0) // Start from Review step if editing
const isProcessing = ref(false)
const emailSent = ref(false)
const formRef = ref(null)
const sessionWarningRef = ref(null)
const emailSenderRef = ref(null)

// Store original form data to detect changes
const originalFormData = ref(null)

// Use composables
const {
  invoiceForm,
  formRules,
  calculatedSubtotal,
  calculatedTaxAmount,
  calculatedTotal,
  extractedTotal,
  amountMismatch,
  addLineItem,
  removeLineItem,
  updateLineTotal,
  validateAllLineItems,
  parseAndFillAddress
} = useInvoiceForm()

const {
  uploadFile,
  fileList,
  ocrResult,
  ocrFilename,
  beforeUpload,
  handleFileChange,
  handleRemove,
  processOCR,
  downloadJSON
} = useFileUpload()

const {
  xmlContent,
  xmlFilename,
  validationResult,
  isValidating,
  generateXML,
  downloadXML
} = useXmlOperations()

const steps = computed(() => {
  if (isEditMode.value) {
    return [
      { title: 'Review', description: 'Review and edit details' },
      { title: 'Generate & Validate', description: 'Generate and validate XML' },
      { title: 'Send', description: 'Send via email' },
    ]
  }
  return [
  { title: 'Upload', description: 'Upload your invoice file' },
  { title: 'Review', description: 'Review and edit details' },
  { title: 'Generate & Validate', description: 'Generate and validate XML' },
  { title: 'Send', description: 'Send via email' },
]
})

const unitOptions = ['EA', 'HUR', 'KGM', 'MTR', 'LTR', 'SET', 'BOX', 'PKG', 'DAY']

const goBack = () => {
  router.push('/')
}

const handleOCRSuccess = (extracted, fileCreatedAt, invoiceIdFromOCR) => {
  invoiceForm.value = JSON.parse(JSON.stringify(extracted))
  // Auto-parse and fill supplier address (using OCR's parsed_address)
  if (invoiceForm.value.supplier.parsed_address) {
    parseAndFillAddress(invoiceForm.value.supplier.parsed_address, invoiceForm.value.supplier)
  }
  
  // Auto-parse and fill customer address (using OCR's parsed_address)
  if (invoiceForm.value.customer.parsed_address) {
    parseAndFillAddress(invoiceForm.value.customer.parsed_address, invoiceForm.value.customer)
  }
  currentStep.value = 1
  
  // Save invoice_id returned from OCR (in create mode)
  if (invoiceIdFromOCR && !isEditMode.value) {
    invoiceId.value = invoiceIdFromOCR
  }
  
  // Set file creation time (for accurate remaining time calculation)
  if (sessionWarningRef.value && fileCreatedAt) {
    sessionWarningRef.value.setFileCreatedAt(fileCreatedAt)
  }
}

const handleProcessOCR = async () => {
  isProcessing.value = true
  const success = await processOCR(handleOCRSuccess)
  isProcessing.value = false
  return success
}

// Helper function to extract fields from raw OCR data (similar to backend extract_invoice_fields)
const extractFieldsFromRawOCR = (rawOcrData) => {
  try {
    // Check if data is already extracted (has invoice_info, supplier, customer)
    if (rawOcrData.invoice_info || rawOcrData.supplier || rawOcrData.customer) {
      // Already extracted, return as is
      return rawOcrData
    }
    
    // Extract from raw OCR data (Veryfi API format)
    const issueDate = rawOcrData.date || ''
    const issueDateOnly = issueDate && issueDate.includes(' ') ? issueDate.split(' ')[0] : issueDate
    
    const dueDate = rawOcrData.due_date || ''
    const dueDateOnly = dueDate && dueDate.includes(' ') ? dueDate.split(' ')[0] : dueDate
    
    const vendor = rawOcrData.vendor || {}
    const billTo = rawOcrData.bill_to || {}
    
    // Extract line items
    const lineItems = []
    const rawItems = rawOcrData.line_items || []
    for (const item of rawItems) {
      const description = item.full_description || item.description || ''
      // Skip tax/total lines
      if (description && ['GST', 'TAX', 'TOTAL'].some(keyword => description.toUpperCase().includes(keyword))) {
        continue
      }
      lineItems.push({
        name: description,
        quantity: parseFloat(item.quantity) || 1.0,
        unit_code: 'EA',
        unit_price: parseFloat(item.price) || 0.0,
        line_total: parseFloat(item.total) || 0.0,
        tax_percent: null
      })
    }
    
    if (lineItems.length === 0) {
      lineItems.push({
        name: '',
        quantity: 1,
        unit_code: 'EA',
        unit_price: 0,
        line_total: 0,
        tax_percent: null
      })
    }
    
    return {
      invoice_info: {
        invoice_number: rawOcrData.invoice_number || '',
        issue_date: issueDateOnly,
        due_date: dueDateOnly,
        currency_code: rawOcrData.currency_code || 'AUD',
        buyer_reference: 'N/A'
      },
      supplier: {
        name: vendor.raw_name || vendor.name || '',
        street_name: '',
        city_name: '',
        postal_zone: '',
        abn: '',
        raw_address: vendor.raw_address || vendor.address || '',
        parsed_address: vendor.parsed_address || null
      },
      customer: {
        name: billTo.name || '',
        street_name: '',
        city_name: '',
        postal_zone: '',
        abn: '',
        raw_address: billTo.address || '',
        parsed_address: billTo.parsed_address || null
      },
      line_items: lineItems,
      summary: {
        subtotal: parseFloat(rawOcrData.subtotal) || 0,
        tax_amount: parseFloat(rawOcrData.tax) || 0,
        total: parseFloat(rawOcrData.total) || 0
      }
    }
  } catch (error) {
    console.error('Error extracting fields from OCR data:', error)
    // Return default structure on error
    return {
      invoice_info: { invoice_number: '', issue_date: '', due_date: '', currency_code: 'AUD', buyer_reference: 'N/A' },
      supplier: { name: '', street_name: '', city_name: '', postal_zone: '', abn: '', raw_address: '' },
      customer: { name: '', street_name: '', city_name: '', postal_zone: '', abn: '', raw_address: '' },
      line_items: [{ name: '', quantity: 1, unit_code: 'EA', unit_price: 0, line_total: 0, tax_percent: null }],
      summary: { subtotal: 0, tax_amount: 0, total: 0 }
    }
  }
}

// Helper function to parse fields from XML content
const parseFieldsFromXML = (xmlContent) => {
  try {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlContent, 'text/xml')
    
    // Check for parsing errors
    const parserError = xmlDoc.querySelector('parsererror')
    if (parserError) {
      console.error('XML parsing error:', parserError.textContent)
      return null
    }
    
    // Namespaces
    const NS_CBC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    const NS_CAC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    
    const getText = (element, tagName) => {
      const elem = element?.getElementsByTagNameNS(NS_CBC, tagName)?.[0] || element?.getElementsByTagNameNS(null, tagName)?.[0]
      return elem?.textContent?.trim() || ''
    }
    
    const getTextNS = (element, ns, tagName) => {
      const elem = element?.getElementsByTagNameNS(ns, tagName)?.[0]
      return elem?.textContent?.trim() || ''
    }
    
    // Invoice info
    const invoiceNumber = getText(xmlDoc, 'ID')
    const issueDate = getText(xmlDoc, 'IssueDate')
    const dueDate = getText(xmlDoc, 'DueDate')
    const currencyCode = getText(xmlDoc, 'DocumentCurrencyCode')
    const buyerReference = getText(xmlDoc, 'BuyerReference')
    
    // Supplier info
    const supplierParty = xmlDoc.getElementsByTagNameNS(NS_CAC, 'AccountingSupplierParty')?.[0]?.getElementsByTagNameNS(NS_CAC, 'Party')?.[0]
    const supplierEndpointID = supplierParty?.getElementsByTagNameNS(NS_CBC, 'EndpointID')?.[0]?.textContent?.trim() || ''
    const supplierName = supplierParty?.getElementsByTagNameNS(NS_CAC, 'PartyName')?.[0]?.getElementsByTagNameNS(NS_CBC, 'Name')?.[0]?.textContent?.trim() || ''
    const supplierAddress = supplierParty?.getElementsByTagNameNS(NS_CAC, 'PostalAddress')?.[0]
    const supplierStreetName = supplierAddress ? getText(supplierAddress, 'StreetName') : ''
    const supplierCityName = supplierAddress ? getText(supplierAddress, 'CityName') : ''
    const supplierPostalZone = supplierAddress ? getText(supplierAddress, 'PostalZone') : ''
    
    // Customer info
    const customerParty = xmlDoc.getElementsByTagNameNS(NS_CAC, 'AccountingCustomerParty')?.[0]?.getElementsByTagNameNS(NS_CAC, 'Party')?.[0]
    const customerEndpointID = customerParty?.getElementsByTagNameNS(NS_CBC, 'EndpointID')?.[0]?.textContent?.trim() || ''
    const customerName = customerParty?.getElementsByTagNameNS(NS_CAC, 'PartyName')?.[0]?.getElementsByTagNameNS(NS_CBC, 'Name')?.[0]?.textContent?.trim() || ''
    const customerAddress = customerParty?.getElementsByTagNameNS(NS_CAC, 'PostalAddress')?.[0]
    const customerStreetName = customerAddress ? getText(customerAddress, 'StreetName') : ''
    const customerCityName = customerAddress ? getText(customerAddress, 'CityName') : ''
    const customerPostalZone = customerAddress ? getText(customerAddress, 'PostalZone') : ''
    
    // Line items
    const lineItems = []
    const invoiceLines = xmlDoc.getElementsByTagNameNS(NS_CAC, 'InvoiceLine')
    for (let i = 0; i < invoiceLines.length; i++) {
      const line = invoiceLines[i]
      const itemName = line.getElementsByTagNameNS(NS_CAC, 'Item')?.[0]?.getElementsByTagNameNS(NS_CBC, 'Name')?.[0]?.textContent?.trim() || ''
      const quantity = parseFloat(getText(line, 'InvoicedQuantity')) || 1
      const unitCode = line.getElementsByTagNameNS(NS_CBC, 'InvoicedQuantity')?.[0]?.getAttribute('unitCode') || 'EA'
      const lineExtensionAmount = parseFloat(getText(line, 'LineExtensionAmount')) || 0
      const priceAmount = parseFloat(line.getElementsByTagNameNS(NS_CAC, 'Price')?.[0]?.getElementsByTagNameNS(NS_CBC, 'PriceAmount')?.[0]?.textContent?.trim()) || 0
      const taxPercent = parseFloat(line.getElementsByTagNameNS(NS_CAC, 'ClassifiedTaxCategory')?.[0]?.getElementsByTagNameNS(NS_CBC, 'Percent')?.[0]?.textContent?.trim()) || 0
      
      lineItems.push({
        name: itemName,
        quantity: quantity,
        unit_code: unitCode,
        unit_price: priceAmount,
        line_total: lineExtensionAmount,
        tax_percent: taxPercent || null
      })
    }
    
    if (lineItems.length === 0) {
      lineItems.push({
        name: '',
        quantity: 1,
        unit_code: 'EA',
        unit_price: 0,
        line_total: 0,
        tax_percent: null
      })
    }
    
    // Summary
    const monetaryTotal = xmlDoc.getElementsByTagNameNS(NS_CAC, 'LegalMonetaryTotal')?.[0]
    const subtotal = parseFloat(monetaryTotal ? getText(monetaryTotal, 'LineExtensionAmount') : '0') || 0
    const taxTotal = xmlDoc.getElementsByTagNameNS(NS_CAC, 'TaxTotal')?.[0]
    const taxAmount = parseFloat(taxTotal ? getText(taxTotal, 'TaxAmount') : '0') || 0
    const total = parseFloat(monetaryTotal ? getText(monetaryTotal, 'PayableAmount') : '0') || 0
    
    return {
      invoice_info: {
        invoice_number: invoiceNumber,
        issue_date: issueDate,
        due_date: dueDate,
        currency_code: currencyCode || 'AUD',
        buyer_reference: buyerReference || 'N/A'
      },
      supplier: {
        name: supplierName,
        street_name: supplierStreetName,
        city_name: supplierCityName,
        postal_zone: supplierPostalZone,
        abn: supplierEndpointID.replace(/\s/g, ''),
        raw_address: `${supplierStreetName}, ${supplierCityName} ${supplierPostalZone}`.trim()
      },
      customer: {
        name: customerName,
        street_name: customerStreetName,
        city_name: customerCityName,
        postal_zone: customerPostalZone,
        abn: customerEndpointID.replace(/\s/g, ''),
        raw_address: `${customerStreetName}, ${customerCityName} ${customerPostalZone}`.trim()
      },
      line_items: lineItems,
      summary: {
        subtotal: subtotal,
        tax_amount: taxAmount,
        total: total
      }
    }
  } catch (error) {
    console.error('Error parsing XML:', error)
    return null
  }
}

const loadInvoice = async () => {
  if (!invoiceId.value) {
    ElMessage.error('Invoice ID is required')
    router.push('/history')
    return
  }

  isLoadingInvoice.value = true
  try {
    const response = await api.get(`/invoices/${invoiceId.value}`)
    
    if (response.data && response.data.data && response.data.data.invoice) {
      const invoice = response.data.data.invoice
      
      let extractedData = null
      
      // If invoice is validated, parse from XML
      if (invoice.status === 'validated' && invoice.xml_content) {
        extractedData = parseFieldsFromXML(invoice.xml_content)
        
        if (!extractedData) {
          ElMessage.warning('Failed to parse XML, falling back to OCR data')
          // Fall back to OCR data if XML parsing fails
          if (invoice.ocr_data) {
            const rawOcrData = JSON.parse(JSON.stringify(invoice.ocr_data))
            extractedData = extractFieldsFromRawOCR(rawOcrData)
          }
        }
      } else {
        // For other statuses (OCR completed, processed, etc.), use OCR data
        if (invoice.ocr_data) {
          const rawOcrData = JSON.parse(JSON.stringify(invoice.ocr_data))
          extractedData = extractFieldsFromRawOCR(rawOcrData)
        } else {
          ElMessage.error('No OCR data found for this invoice')
          router.push('/history')
          return
        }
      }
      
      if (!extractedData) {
        ElMessage.error('Failed to extract invoice data')
        router.push('/history')
        return
      }
      
      // Ensure all required fields exist with defaults
      invoiceForm.value = {
        invoice_info: {
          invoice_number: extractedData.invoice_info?.invoice_number || '',
          issue_date: extractedData.invoice_info?.issue_date || '',
          due_date: extractedData.invoice_info?.due_date || '',
          currency_code: extractedData.invoice_info?.currency_code || 'AUD',
          buyer_reference: extractedData.invoice_info?.buyer_reference || 'N/A'
        },
        supplier: {
          name: extractedData.supplier?.name || '',
          street_name: extractedData.supplier?.street_name || '',
          city_name: extractedData.supplier?.city_name || '',
          postal_zone: extractedData.supplier?.postal_zone || '',
          abn: extractedData.supplier?.abn || '',
          raw_address: extractedData.supplier?.raw_address || ''
        },
        customer: {
          name: extractedData.customer?.name || '',
          street_name: extractedData.customer?.street_name || '',
          city_name: extractedData.customer?.city_name || '',
          postal_zone: extractedData.customer?.postal_zone || '',
          abn: extractedData.customer?.abn || '',
          raw_address: extractedData.customer?.raw_address || ''
        },
        line_items: extractedData.line_items && extractedData.line_items.length > 0 
          ? extractedData.line_items 
          : [{
              name: '',
              quantity: 1,
              unit_code: 'EA',
              unit_price: 0,
              line_total: 0,
              tax_percent: null
            }],
        summary: {
          subtotal: extractedData.summary?.subtotal || 0,
          tax_amount: extractedData.summary?.tax_amount || 0,
          total: extractedData.summary?.total || 0
        }
      }
      
      // If status is not validated, auto-fill address from parsed_address (like create mode)
      if (invoice.status !== 'validated') {
        const rawOcrData = invoice.ocr_data ? JSON.parse(JSON.stringify(invoice.ocr_data)) : null
        if (rawOcrData) {
          const vendor = rawOcrData.vendor || {}
          const billTo = rawOcrData.bill_to || {}
          
          // Auto-fill supplier address from parsed_address
          if (vendor.parsed_address && invoiceForm.value.supplier) {
            parseAndFillAddress(vendor.parsed_address, invoiceForm.value.supplier)
          }
          
          // Auto-fill customer address from parsed_address
          if (billTo.parsed_address && invoiceForm.value.customer) {
            parseAndFillAddress(billTo.parsed_address, invoiceForm.value.customer)
          }
        }
      }
      
      // If XML already exists, load it
      if (invoice.xml_content) {
        xmlContent.value = invoice.xml_content
        // Extract filename from invoice
        xmlFilename.value = invoice.filename ? invoice.filename.replace('.json', '.xml') : 'invoice.xml'
      }
      
      // If validation result exists, load it
      if (invoice.validation_result) {
        validationResult.value = invoice.validation_result
      }
      
      // Save original form data snapshot for change detection
      originalFormData.value = JSON.parse(JSON.stringify(invoiceForm.value))
    } else {
      ElMessage.error('Failed to load invoice')
      router.push('/history')
    }
  } catch (error) {
    console.error('Load invoice error:', error)
    ElMessage.error('Failed to load invoice')
    router.push('/history')
  } finally {
    isLoadingInvoice.value = false
  }
}

// Check if form data has been modified
const hasFormChanged = () => {
  if (!originalFormData.value) return true // If no original data, assume changed
  
  const current = JSON.stringify(invoiceForm.value)
  const original = JSON.stringify(originalFormData.value)
  
  return current !== original
}

const saveInvoice = async () => {
  if (!invoiceId.value) return true // Not in edit mode, skip save
  
  if (!formRef.value) {
    ElMessage.error('Form reference not found')
    return false
  }

  // In edit mode, only validate line items and amounts, don't force validation of all required fields
  // because user may be in the process of editing
  // Validate line items
  if (!validateAllLineItems(ElMessage)) {
    return false
  }

  // Amount validation
  if (amountMismatch.value) {
    try {
      await ElMessageBox.confirm(
        'The calculated amounts do not match the entered amounts. Do you want to continue?',
        'Amount Mismatch',
        {
          confirmButtonText: 'Continue',
          cancelButtonText: 'Review',
          type: 'warning',
        }
      )
    } catch {
      return false
    }
  }

  isProcessing.value = true
  try {
    // Check if form was modified to determine if we should preserve status
    const formChanged = hasFormChanged()
    
    const response = await api.put(`/invoices/${invoiceId.value}`, {
      ocr_data: invoiceForm.value,
      preserve_status: !formChanged // Preserve status if form was not changed
    })

    if (response.data && response.data.data) {
      ElMessage.success('Invoice updated successfully')
      // Update original form data snapshot after successful save
      originalFormData.value = JSON.parse(JSON.stringify(invoiceForm.value))
      return true
    } else {
      ElMessage.error('Failed to update invoice')
      return false
    }
  } catch (error) {
    console.error('Save invoice error:', error)
    ElMessage.error('Failed to update invoice')
    return false
  } finally {
    isProcessing.value = false
  }
}

const handleGenerateXML = async () => {
  isProcessing.value = true
  // Pass invoice_id if available (both edit mode and create mode after OCR)
  const invoiceData = invoiceId.value
    ? { ...invoiceForm.value, invoice_id: invoiceId.value }
    : invoiceForm.value
  await generateXML(invoiceData)
  isProcessing.value = false
}

const sendEmail = async (email) => {
  if (!email) {
    ElMessage.warning('Please enter an email address')
    return
  }
  
  if (!xmlFilename.value) {
    ElMessage.warning('Please generate XML first')
    return
  }
  
  isProcessing.value = true
  
  try {
    const requestData = {
      email: email,
      xml_filename: xmlFilename.value
    }
    
    // Include invoice_id if available (for edit mode)
    if (invoiceId.value) {
      requestData.invoice_id = invoiceId.value
    }
    
    const response = await api.post('/send-email', requestData)

    const data = response.data

    // Check if there's an error field (backend returns { message, error } on failure)
    if (data.error) {
      if (response.status === 404) {
        ElMessage.error({
          message: data.message || 'XML file has been deleted. Please go back and regenerate the XML.',
          duration: 6000,
          showClose: true
        })
      } else if (data.error_info) {
        // Display Mailgun detailed error information
        ElMessageBox.alert(
          `<div style="line-height: 1.6;">
            <p><strong>${data.error_info.title}</strong></p>
            <p style="margin: 1rem 0;">${data.error_info.message}</p>
            <p style="color: #9ca3af; font-size: 0.9em;">${data.error_info.details}</p>
          </div>`,
          'Email Sending Failed',
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: 'OK',
            type: 'error'
          }
        )
      } else {
        ElMessage.error({
          message: data.message || data.error || 'Failed to send email',
          duration: 5000,
          showClose: true
        })
      }
      return
    }

    // Success: no error field and status 200
    emailSent.value = true
    // Mark step 4 as completed
    currentStep.value = 4
    ElMessage.success({
      message: data.message || 'Email sent successfully!',
      duration: 5000,
      showClose: true
    })
  } catch (error) {
    console.error('Email Error:', error)
    ElMessage.error(`Failed to send email: ${error.message}`)
  } finally {
    isProcessing.value = false
  }
}

const skipToManualEntry = async () => {
  // Skip upload, go directly to manual entry
  currentStep.value = 1
  
  // Clear OCR-related state
  ocrFilename.value = ''
  ocrResult.value = null
  
  // Reset session timer
  if (sessionWarningRef.value) {
    sessionWarningRef.value.reset()
  }
  
  // Use default empty form
  invoiceForm.value = {
    invoice_info: {
      invoice_number: '',
      issue_date: '',
      due_date: '',
      currency_code: 'AUD',
      buyer_reference: 'N/A'
    },
    supplier: {
      name: '',
      street_name: '',
      city_name: '',
      postal_zone: '',
      abn: '',
      raw_address: ''
    },
    customer: {
      name: '',
      street_name: '',
      city_name: '',
      postal_zone: '',
      abn: '',
      raw_address: ''
    },
    line_items: [{
      name: '',
      quantity: 1,
      unit_code: 'EA',
      unit_price: 0,
      line_total: 0,
      tax_percent: null
    }],
    summary: {
      subtotal: 0,
      tax_amount: 0,
      total: 0
    }
  }
  
  // Create invoice record in database for manual entry
  isProcessing.value = true
  try {
    const response = await api.post('/invoices/manual', {
      invoice_data: invoiceForm.value
    })
    
    if (response.data && response.data.data && response.data.data.invoice) {
      invoiceId.value = response.data.data.invoice.id
      ElMessage.success('Manual invoice created. You can now enter data.')
    } else {
      ElMessage.warning('Failed to create invoice record, but you can continue.')
    }
  } catch (error) {
    console.error('Create manual invoice error:', error)
    ElMessage.warning('Failed to create invoice record, but you can continue.')
  } finally {
    isProcessing.value = false
  }
}

const startOver = () => {
  // Reset all state
  currentStep.value = 0
  uploadFile.value = null
  fileList.value = []
  xmlContent.value = ''
  xmlFilename.value = ''
  validationResult.value = null
  emailSent.value = false
  
  // Reset form
  invoiceForm.value = {
    invoice_info: {
      invoice_number: '',
      issue_date: '',
      due_date: '',
      currency_code: 'AUD',
      buyer_reference: 'N/A'
    },
    supplier: {
      name: '',
      street_name: '',
      city_name: '',
      postal_zone: '',
      abn: '',
      raw_address: ''
    },
    customer: {
      name: '',
      street_name: '',
      city_name: '',
      postal_zone: '',
      abn: '',
      raw_address: ''
    },
    line_items: [{
      name: '',
      quantity: 1,
      unit_code: 'EA',
      unit_price: 0,
      line_total: 0,
      tax_percent: null
    }],
    summary: {
      subtotal: 0,
      tax_amount: 0,
      total: 0
    }
  }
  
  // Reset session timer
  if (sessionWarningRef.value) {
    sessionWarningRef.value.reset()
  }
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    await handleProcessOCR()
  } else if (currentStep.value === 1) {
    // In edit mode, save invoice first (without strict form validation)
    if (isEditMode.value) {
      // Check if form was modified BEFORE saving
      const formChanged = hasFormChanged()
      
      const saved = await saveInvoice()
      if (!saved) {
        return
      }
      
      if (formChanged) {
        // Form was modified, clear XML and validation to force regeneration
        xmlContent.value = ''
        xmlFilename.value = ''
        validationResult.value = null
        ElMessage.info('Form data has been modified. XML will be regenerated.')
      } else {
        // Form was not modified, reload XML and validation from database
        try {
          const response = await api.get(`/invoices/${invoiceId.value}`)
          if (response.data && response.data.data && response.data.data.invoice) {
            const invoice = response.data.data.invoice
            
            if (invoice.xml_content) {
              xmlContent.value = invoice.xml_content
              xmlFilename.value = invoice.filename ? invoice.filename.replace('.json', '.xml') : 'invoice.xml'
            }
            
            if (invoice.validation_result) {
              validationResult.value = invoice.validation_result
            }
            
            if (invoice.xml_content && invoice.validation_result) {
              ElMessage.success('Using existing XML and validation results.')
            }
          }
        } catch (error) {
          console.error('Failed to reload XML from database:', error)
          // If reload fails, clear XML to force regeneration
          xmlContent.value = ''
          xmlFilename.value = ''
          validationResult.value = null
        }
      }
    } else {
      // In create mode, validate form
      if (!formRef.value) {
        ElMessage.error('Form reference not found')
        return
      }

      // Validate basic form fields
      try {
        await formRef.value.validate()
      } catch (validationError) {
        console.log('Form validation failed:', validationError)
        ElMessage.error({
          message: 'Please fill in all required fields correctly',
          duration: 4000,
          showClose: true
        })
        return
      }

      // Validate line items
      if (!validateAllLineItems(ElMessage)) {
        return
      }

      // Amount validation
      if (amountMismatch.value) {
        try {
          await ElMessageBox.confirm(
            'The calculated amounts do not match the entered amounts. Do you want to continue?',
            'Amount Mismatch',
            {
              confirmButtonText: 'Continue',
              cancelButtonText: 'Review',
              type: 'warning',
            }
          )
        } catch {
          return
        }
      }
      
      // If invoiceId exists (from manual entry), save the invoice
      if (invoiceId.value) {
        const saved = await saveInvoice()
        if (!saved) {
          return
        }
      }
    }
    
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    // Check validation result - allow proceeding if validation passed
    if (!validationResult.value) {
      ElMessage.error('Please generate and validate the XML first.')
      return
    }
    
    // Check if validation was successful
    if (validationResult.value.success !== true) {
      ElMessage.error('XML validation failed. Please fix the errors before proceeding.')
      return
    }
    
    // Check if all validation rules passed
    if (validationResult.value.results) {
      const results = validationResult.value.results
      const allPassed = Object.values(results).every(result => result.successful === true)
      if (!allPassed) {
        ElMessage.error('Some validation rules failed. Please fix the errors before proceeding.')
        return
      }
    }
    
    currentStep.value = 3
  }
}

const prevStep = () => {
  const minStep = isEditMode.value ? 1 : 0
  if (currentStep.value > minStep) {
    currentStep.value--
    
    // If returning to step 2, reset XML state to allow regeneration
    if (currentStep.value === 1) {
      xmlContent.value = ''
      xmlFilename.value = ''
      validationResult.value = null
    }
  }
}

// Load invoice data if in edit mode
onMounted(() => {
  if (isEditMode.value) {
    loadInvoice()
  }
})
</script>

<template>
  <div class="create-page">
    <!-- Session Warning -->
    <SessionWarning ref="sessionWarningRef" />

    <main class="main-content">
      <!-- Progress Steps -->
      <div class="steps">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{ active: index === (isEditMode ? currentStep - 1 : currentStep), completed: index < (isEditMode ? currentStep - 1 : currentStep) }"
        >
          <div class="step-indicator">
            <span v-if="index < (isEditMode ? currentStep - 1 : currentStep)">✓</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-info">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.description }}</div>
          </div>
        </div>
      </div>

      <div v-loading="isLoadingInvoice" class="content-card">
        <!-- Step 0: Upload (only in create mode) -->
        <div v-show="currentStep === 0 && !isEditMode" class="step-content">
          <FileUploader
            :upload-file="uploadFile"
            :file-list="fileList"
            @before-upload="beforeUpload"
            @change="handleFileChange"
            @remove="handleRemove"
            @skip-to-manual="skipToManualEntry"
          />
        </div>

        <!-- Step 1: Edit Form -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="section-header-with-action">
            <h2 class="section-title">Review & Edit Invoice Details</h2>
            <el-button 
              v-if="ocrFilename"
              type="success"
              plain
              @click="downloadJSON"
            >
              Download JSON
            </el-button>
          </div>

          <el-form 
            ref="formRef" 
            :model="invoiceForm" 
            :rules="formRules" 
            label-width="120px"
            class="invoice-form"
          >
            <!-- Basic Info -->
            <div class="form-section">
              <h3 class="section-heading">Basic Information</h3>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="Invoice No." prop="invoice_info.invoice_number">
                    <el-input v-model="invoiceForm.invoice_info.invoice_number" placeholder="INV-001" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="Issue Date" prop="invoice_info.issue_date">
                    <el-input v-model="invoiceForm.invoice_info.issue_date" placeholder="2024-01-01" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="Due Date" prop="invoice_info.due_date">
                    <el-input v-model="invoiceForm.invoice_info.due_date" placeholder="2024-01-31" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Currency" prop="invoice_info.currency_code">
                    <el-input v-model="invoiceForm.invoice_info.currency_code" placeholder="AUD" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Buyer Ref." prop="invoice_info.buyer_reference">
                    <el-input v-model="invoiceForm.invoice_info.buyer_reference" placeholder="N/A" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Supplier Info -->
            <div class="form-section">
              <h3 class="section-heading">Supplier Information</h3>
              <div v-if="invoiceForm.supplier && invoiceForm.supplier.raw_address" class="extracted-info">
                <label class="extracted-label">Extracted Address:</label>
                <div class="extracted-content">{{ invoiceForm.supplier.raw_address }}</div>
              </div>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Name" prop="supplier.name">
                    <el-input v-model="invoiceForm.supplier.name" placeholder="Company Name" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="ABN" prop="supplier.abn">
                    <el-input v-model="invoiceForm.supplier.abn" placeholder="12345678901" maxlength="11" />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="Street Name" prop="supplier.street_name">
                    <el-input v-model="invoiceForm.supplier.street_name" placeholder="123 Main Street" maxlength="100"/>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="City" prop="supplier.city_name">
                    <el-input v-model="invoiceForm.supplier.city_name" placeholder="Sydney" maxlength="50"/>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Postal Code" prop="supplier.postal_zone">
                    <el-input v-model="invoiceForm.supplier.postal_zone" placeholder="2000" maxlength="50"/>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Customer Info -->
            <div class="form-section">
              <h3 class="section-heading">Customer Information</h3>
              <div v-if="invoiceForm.customer && invoiceForm.customer.raw_address" class="extracted-info">
                <label class="extracted-label">Extracted Address:</label>
                <div class="extracted-content">{{ invoiceForm.customer.raw_address }}</div>
              </div>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Name" prop="customer.name">
                    <el-input v-model="invoiceForm.customer.name" placeholder="Customer Name" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="ABN" prop="customer.abn">
                    <el-input v-model="invoiceForm.customer.abn" placeholder="12345678901" maxlength="11" />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="Street Name" prop="customer.street_name">
                    <el-input v-model="invoiceForm.customer.street_name" placeholder="456 Customer Road" maxlength="100"/>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="City" prop="customer.city_name">
                    <el-input v-model="invoiceForm.customer.city_name" placeholder="Melbourne" maxlength="50"/>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Postal Code" prop="customer.postal_zone">
                    <el-input v-model="invoiceForm.customer.postal_zone" placeholder="3000" maxlength="50"/>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Line Items -->
            <LineItemsEditor
              :items="invoiceForm.line_items"
              :unit-options="unitOptions"
              @add="addLineItem"
              @remove="(index) => removeLineItem(index, ElMessage)"
              @update="updateLineTotal"
            />

            <!-- Summary -->
            <div class="form-section summary-section">
              <h3 class="section-heading">Summary</h3>
              <div class="summary-info">
                <div class="summary-row">
                  <label>Subtotal (from line items):</label>
                  <span class="amount">${{ calculatedSubtotal.toFixed(2) }}</span>
                </div>
                <div class="summary-row">
                  <label>Tax (based on your tax %):</label>
                  <span class="amount">${{ calculatedTaxAmount.toFixed(2) }}</span>
                </div>
                <div class="summary-row total-row">
                  <label>Calculated Total:</label>
                  <span class="amount">${{ calculatedTotal.toFixed(2) }}</span>
                </div>
                <div class="summary-row extracted-row">
                  <label>Extracted Total (from OCR):</label>
                  <span class="amount">${{ extractedTotal.toFixed(2) }}</span>
                </div>
              </div>
              
              <el-alert 
                v-if="amountMismatch" 
                type="warning" 
                :closable="false"
                show-icon
                class="mismatch-alert"
              >
                The calculated total (${{ calculatedTotal.toFixed(2) }}) differs from the extracted total (${{ extractedTotal.toFixed(2) }}). 
                Please verify the line items and tax percentages.
              </el-alert>
              <el-alert 
                v-else
                type="success" 
                :closable="false"
                show-icon
                class="match-alert"
              >
                Amounts match! Ready to proceed.
              </el-alert>
            </div>
          </el-form>
        </div>

        <!-- Step 2: Generate & Validate XML -->
        <div v-show="currentStep === 2" class="step-content">
          <XmlValidator
            :xml-content="xmlContent"
            :xml-filename="xmlFilename"
            :validation-result="validationResult"
            :is-validating="isValidating"
            @generate="handleGenerateXML"
            @download="downloadXML"
          />
        </div>

        <!-- Step 3: Send Email -->
        <div v-show="currentStep === 3 || currentStep === 4" class="step-content">
          <EmailSender
            ref="emailSenderRef"
            :xml-filename="xmlFilename"
            :email-sent="emailSent"
            :is-loading="isProcessing"
            @download="downloadXML"
            @send="sendEmail"
            @start-over="startOver"
          />
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!emailSent" class="actions">
        <el-button 
          v-if="currentStep > (isEditMode ? 1 : 0) && currentStep < 3"
          size="large" 
          @click="prevStep"
        >
          Previous
        </el-button>
        <el-button 
          v-if="currentStep < 3"
          type="primary" 
          size="large" 
          :loading="isProcessing"
          :disabled="(!isEditMode && !uploadFile && currentStep === 0) || (currentStep === 2 && (!validationResult || !validationResult.success))"
          @click="nextStep"
        >
          {{ currentStep === 0 ? 'Process Document' : currentStep === 1 ? (isEditMode ? 'Save & Continue' : 'Next Step') : currentStep === 2 ? 'Proceed to Send' : 'Next Step' }}
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  padding-top: 0;
  transition: background 0.3s ease;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2.5rem 2rem;
}

.section-header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-header-with-action .section-title {
  text-align: left;
  margin: 0;
}

.invoice-form {
  margin-top: 2rem;
}

.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--bg-section);
  border-radius: 12px;
  border: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.section-heading {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--accent-primary);
  margin: 0 0 1.5rem 0;
  transition: color 0.3s ease;
}

.extracted-info {
  margin-bottom: 1.5rem;
  padding: 0.75rem;
  background: var(--bg-hover);
  border: 1px solid var(--border-accent);
  border-radius: 8px;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.extracted-label {
  display: block;
  font-size: 0.85rem;
  color: var(--accent-secondary);
  margin-bottom: 0.5rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.extracted-content {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  transition: color 0.3s ease;
}

/* Element Plus styles - ensure they work correctly in both themes */
:deep(.el-input__wrapper) {
  background-color: var(--bg-input) !important;
  box-shadow: 0 0 0 1px var(--border-secondary) inset !important;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--border-focus) inset !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
  transition: color 0.3s ease;
}

:deep(.el-form-item__label) {
  color: var(--text-primary) !important;
  font-weight: 500;
  transition: color 0.3s ease;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--accent-danger) inset !important;
}

:deep(.el-form-item__error) {
  color: var(--accent-danger);
}

:deep(.el-select .el-input__wrapper) {
  background-color: var(--bg-input) !important;
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: var(--bg-input) !important;
}

/* Fix browser autofill background color */
:deep(.el-input__inner:-webkit-autofill),
:deep(.el-input__inner:-webkit-autofill:hover),
:deep(.el-input__inner:-webkit-autofill:focus),
:deep(.el-input__inner:-webkit-autofill:active) {
  -webkit-text-fill-color: var(--text-primary) !important;
  transition: background-color 5000s ease-in-out 0s;
  caret-color: var(--text-primary) !important;
}

.summary-section {
  background: var(--bg-active);
  border-color: var(--border-accent);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

/* Light mode specific styles for summary section */
:root[data-theme="light"] .summary-section {
  background: linear-gradient(135deg, rgba(5, 150, 105, 0.05) 0%, rgba(5, 150, 105, 0.02) 100%);
  border-color: rgba(5, 150, 105, 0.2);
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.08);
}

.summary-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--bg-section);
  border-radius: 8px;
  transition: background-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
}

/* Light mode specific styles for summary rows */
:root[data-theme="light"] .summary-row {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

:root[data-theme="light"] .summary-row:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.summary-row label { 
  color: var(--text-primary); 
  font-weight: 500; 
  font-size: 0.95rem; 
  transition: color 0.3s ease;
}

.summary-row .amount { 
  color: var(--accent-primary); 
  font-weight: 600; 
  font-size: 1.2rem; 
  transition: color 0.3s ease;
}

.summary-row.total-row {
  background: var(--bg-active);
  border: 1px solid var(--border-accent);
  transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
}

/* Light mode specific styles for total row */
:root[data-theme="light"] .summary-row.total-row {
  background: linear-gradient(135deg, rgba(5, 150, 105, 0.12) 0%, rgba(5, 150, 105, 0.08) 100%);
  border: 2px solid rgba(5, 150, 105, 0.3);
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.15);
  font-weight: 600;
}

:root[data-theme="light"] .summary-row.total-row:hover {
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2);
  transform: translateY(-2px);
}

.summary-row.total-row .amount { 
  font-size: 1.4rem; 
}

.summary-row.extracted-row {
  background: var(--bg-hover);
  border: 1px solid var(--border-accent);
  transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
}

/* Light mode specific styles for extracted row */
:root[data-theme="light"] .summary-row.extracted-row {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0.04) 100%);
  border: 1px solid rgba(37, 99, 235, 0.2);
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.1);
}

:root[data-theme="light"] .summary-row.extracted-row:hover {
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
  transform: translateY(-1px);
}

.summary-row.extracted-row .amount { 
  color: var(--accent-secondary); 
  transition: color 0.3s ease;
}

.mismatch-alert,
.match-alert { 
  margin-top: 0;
  transition: all 0.3s ease;
}

/* Increase alert font sizes for all themes */
.match-alert :deep(.el-alert__title),
.mismatch-alert :deep(.el-alert__title) {
  font-size: 1.1rem !important;
}

.match-alert :deep(.el-alert__description),
.mismatch-alert :deep(.el-alert__description) {
  font-size: 1rem !important;
}

.match-alert :deep(.el-alert__icon),
.mismatch-alert :deep(.el-alert__icon) {
  font-size: 1.3rem !important;
}

/* Light mode specific styles for success alert (match-alert) */
:root[data-theme="light"] .match-alert {
  background: linear-gradient(135deg, rgba(5, 150, 105, 0.12) 0%, rgba(5, 150, 105, 0.08) 100%) !important;
  border: 1px solid rgba(5, 150, 105, 0.3) !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.12) !important;
}

:root[data-theme="light"] .match-alert :deep(.el-alert__content) {
  color: #065f46 !important;
}

:root[data-theme="light"] .match-alert :deep(.el-alert__title) {
  color: #065f46 !important;
  font-weight: 600 !important;
  font-size: 1.1rem !important;
}

:root[data-theme="light"] .match-alert :deep(.el-alert__icon) {
  color: #059669 !important;
  font-size: 1.3rem !important;
}

:root[data-theme="light"] .match-alert :deep(.el-alert__description) {
  color: #065f46 !important;
  font-weight: 500 !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
}

/* Light mode specific styles for warning alert (mismatch-alert) */
:root[data-theme="light"] .mismatch-alert {
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.12) 0%, rgba(217, 119, 6, 0.08) 100%) !important;
  border: 1px solid rgba(217, 119, 6, 0.3) !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.12) !important;
}

:root[data-theme="light"] .mismatch-alert :deep(.el-alert__content) {
  color: #92400e !important;
}

:root[data-theme="light"] .mismatch-alert :deep(.el-alert__title) {
  color: #92400e !important;
  font-weight: 600 !important;
  font-size: 1.1rem !important;
}

:root[data-theme="light"] .mismatch-alert :deep(.el-alert__icon) {
  color: #d97706 !important;
  font-size: 1.3rem !important;
}

:root[data-theme="light"] .mismatch-alert :deep(.el-alert__description) {
  color: #92400e !important;
  font-weight: 500 !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
}

.steps {
  display: flex;
  justify-content: center;
  margin-bottom: 2.5rem;
  gap: 2rem;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
}

.step {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  opacity: 0.5;
  transition: opacity 0.3s ease;
  min-width: 250px;
}

.step.active,
.step.completed {
  opacity: 1;
}

.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--text-tertiary);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.step.active .step-indicator {
  background: var(--bg-active);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.step.completed .step-indicator {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #ffffff;
  transition: all 0.3s ease;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  transition: color 0.3s ease;
}

.step-desc {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  transition: color 0.3s ease;
}

.content-card {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2.5rem;
  min-height: 400px;
  box-shadow: var(--shadow-md);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.step-content {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.send-email-section {
  max-width: 800px;
  margin: 0 auto;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  text-align: center;
  transition: color 0.3s ease;
}

.section-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 2rem;
  transition: color 0.3s ease;
}

.xml-preview-compact {
  margin: 2rem 0;
  border: 1px solid var(--border-accent);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-hover);
  transition: background-color 0.3s ease;
}

.preview-title {
  font-weight: 600;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.email-form {
  margin-top: 2rem;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

/* Increase button font size */
.actions :deep(.el-button) {
  font-size: 1.1rem !important;
  font-weight: 500 !important;
  padding: 0.75rem 1.5rem !important;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .steps {
    flex-direction: column;
  }

  .content-card {
    padding: 1.5rem;
  }

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>
