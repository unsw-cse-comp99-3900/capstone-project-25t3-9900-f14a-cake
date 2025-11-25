/**
 * Invoice form composable for managing invoice data and validation.
 * 
 * @module composables/useInvoiceForm
 */

import { ref, computed } from 'vue'

/**
 * Composable for managing invoice form state and operations.
 * 
 * @returns {Object} Object containing form state, validation rules, and methods
 */
export function useInvoiceForm() {
  const invoiceForm = ref({
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
  })

  const formRules = {
    invoice_info: {
      invoice_number: [
        { required: true, message: 'Invoice number is required', trigger: 'blur' }
      ],
      issue_date: [
        { required: true, message: 'Issue date is required', trigger: 'blur' },
        { pattern: /^\d{4}-\d{2}-\d{2}$/, message: 'Format: YYYY-MM-DD', trigger: 'blur' }
      ],
      due_date: [
        { required: true, message: 'Due date is required', trigger: 'blur' },
        { pattern: /^\d{4}-\d{2}-\d{2}$/, message: 'Format: YYYY-MM-DD', trigger: 'blur' }
      ],
      currency_code: [
        { required: true, message: 'Currency code is required', trigger: 'blur' },
        { pattern: /^[A-Z]{3}$/, message: 'Must be 3 uppercase letters', trigger: 'blur' }
      ],
      buyer_reference: [
        { required: true, message: 'Buyer reference is required', trigger: 'blur' }
      ]
    },
    supplier: {
      name: [{ required: true, message: 'Supplier name is required', trigger: 'blur' }],
      street_name: [
        { required: true, message: 'Street name is required', trigger: 'blur' },
        { max: 100, message: 'Street name cannot exceed 100 characters', trigger: 'blur' }
      ],
      city_name: [
        { required: true, message: 'City is required', trigger: 'blur' },
        { max: 50, message: 'City name cannot exceed 50 characters', trigger: 'blur' }
      ],
      postal_zone: [
        { required: true, message: 'Postal code is required', trigger: 'blur' },
        { max: 50, message: 'Postal code cannot exceed 50 characters', trigger: 'blur' }
      ],
      abn: [
        { required: true, message: 'ABN is required', trigger: 'blur' },
        { pattern: /^\d{11}$/, message: 'ABN must be 11 digits', trigger: 'blur' }
      ]
    },
    customer: {
      name: [{ required: true, message: 'Customer name is required', trigger: 'blur' }],
      street_name: [
        { required: true, message: 'Street name is required', trigger: 'blur' },
        { max: 100, message: 'Street name cannot exceed 100 characters', trigger: 'blur' }
      ],
      city_name: [
        { required: true, message: 'City is required', trigger: 'blur' },
        { max: 50, message: 'City name cannot exceed 50 characters', trigger: 'blur' }
      ],
      postal_zone: [
        { required: true, message: 'Postal code is required', trigger: 'blur' },
        { max: 50, message: 'Postal code cannot exceed 50 characters', trigger: 'blur' }
      ],
      abn: [
        { required: true, message: 'ABN is required', trigger: 'blur' },
        { pattern: /^\d{11}$/, message: 'ABN must be 11 digits', trigger: 'blur' }
      ]
    }
  }

  const calculatedSubtotal = computed(() => {
    return invoiceForm.value.line_items.reduce((sum, item) => {
      return sum + (parseFloat(item.line_total) || 0)
    }, 0)
  })

  const calculatedTaxAmount = computed(() => {
    return invoiceForm.value.line_items.reduce((sum, item) => {
      const lineTotal = parseFloat(item.line_total) || 0
      const taxPercent = parseFloat(item.tax_percent) || 0
      return sum + (lineTotal * taxPercent / 100)
    }, 0)
  })

  const calculatedTotal = computed(() => {
    return calculatedSubtotal.value + calculatedTaxAmount.value
  })

  const extractedTotal = computed(() => {
    return parseFloat(invoiceForm.value.summary.total) || 0
  })

  const amountMismatch = computed(() => {
    const diff = Math.abs(calculatedTotal.value - extractedTotal.value)
    return diff > 0.01
  })

  const addLineItem = () => {
    invoiceForm.value.line_items.push({
      name: '',
      quantity: 1,
      unit_code: 'EA',
      unit_price: 0,
      line_total: 0,
      tax_percent: null
    })
  }

  const removeLineItem = (index, showMessage) => {
    if (invoiceForm.value.line_items.length <= 1) {
      if (showMessage) {
        showMessage.warning('At least one line item is required')
      }
      return false
    }
    invoiceForm.value.line_items.splice(index, 1)
    return true
  }

  const updateLineTotal = (item) => {
    const qty = parseFloat(item.quantity) || 0
    const price = parseFloat(item.unit_price) || 0
    item.line_total = qty * price
  }

  const validateLineItem = (item) => {
    if (!item.name || item.name.trim() === '') {
      return 'Item name is required'
    }
    if (!item.quantity || item.quantity <= 0) {
      return 'Quantity must be greater than 0'
    }
    if (item.unit_price === null || item.unit_price === undefined || item.unit_price < 0) {
      return 'Unit price must be 0 or greater'
    }
    if (item.line_total === null || item.line_total === undefined || item.line_total < 0) {
      return 'Line total must be 0 or greater'
    }
    if (item.tax_percent === null || item.tax_percent === undefined || item.tax_percent === '') {
      return 'Tax percentage is required'
    }
    if (item.tax_percent < 0 || item.tax_percent > 100) {
      return 'Tax percentage must be between 0 and 100'
    }
    return null
  }

  const validateAllLineItems = (showMessage) => {
    for (let i = 0; i < invoiceForm.value.line_items.length; i++) {
      const error = validateLineItem(invoiceForm.value.line_items[i])
      if (error) {
        if (showMessage) {
          showMessage.error(`Line item ${i + 1}: ${error}`)
        }
        return false
      }
    }
    return true
  }
  
  /**
   * Extract and fill address fields from OCR parsed_address.
   * 
   * @param {Object|null} parsedAddress - Parsed address object from OCR
   * @param {Object} targetObj - Target object to fill address fields into
   */
  const parseAndFillAddress = (parsedAddress, targetObj) => {
    if (!parsedAddress || typeof parsedAddress !== 'object') {
      return
    }
    
    try {
      // Extract street_name: includes unit (if present) + house_number + road
      const streetParts = []
      if (parsedAddress.unit) {
        streetParts.push(parsedAddress.unit)
      }
      if (parsedAddress.house_number) {
        streetParts.push(parsedAddress.house_number)
      }
      if (parsedAddress.road) {
        streetParts.push(parsedAddress.road)
      }
      // If none of the above, try using street_address
      if (streetParts.length === 0 && parsedAddress.street_address) {
        streetParts.push(parsedAddress.street_address)
      }
      
      const streetName = streetParts.join(' ').substring(0, 100) // Limit to 100 characters
      const cityName = (parsedAddress.city || '').substring(0, 50) // Limit to 50 characters
      const postalZone = (parsedAddress.postcode || '').substring(0, 50) // Limit to 50 characters
      
      // Fill target object
      if (streetName) targetObj.street_name = streetName
      if (cityName) targetObj.city_name = cityName
      if (postalZone) targetObj.postal_zone = postalZone
    } catch (error) {
      console.error('Address parsing error:', error)
      // On parsing failure, do nothing and keep original values
    }
  }

  return {
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
    validateLineItem,
    validateAllLineItems,
    parseAndFillAddress
  }
}

