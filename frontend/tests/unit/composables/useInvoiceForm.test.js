/**
 * Tests for useInvoiceForm composable.
 * 
 * @module tests/unit/composables/useInvoiceForm
 */

import { describe, it, expect, beforeEach } from '@jest/globals'
import { useInvoiceForm } from '@/composables/useInvoiceForm'

describe('useInvoiceForm', () => {
  let form

  beforeEach(() => {
    form = useInvoiceForm()
  })

  describe('Initial state', () => {
    it('should initialize with default form structure', () => {
      expect(form.invoiceForm.value).toBeDefined()
      expect(form.invoiceForm.value.invoice_info).toBeDefined()
      expect(form.invoiceForm.value.supplier).toBeDefined()
      expect(form.invoiceForm.value.customer).toBeDefined()
      expect(form.invoiceForm.value.line_items).toBeDefined()
      expect(form.invoiceForm.value.summary).toBeDefined()
    })

    it('should have default currency code as AUD', () => {
      expect(form.invoiceForm.value.invoice_info.currency_code).toBe('AUD')
    })

    it('should have at least one line item', () => {
      expect(form.invoiceForm.value.line_items.length).toBeGreaterThan(0)
    })
  })

  describe('Line items management', () => {
    it('should add a new line item', () => {
      const initialCount = form.invoiceForm.value.line_items.length
      form.addLineItem()
      expect(form.invoiceForm.value.line_items.length).toBe(initialCount + 1)
    })

    it('should not remove the last line item', () => {
      const mockMessage = { warning: jest.fn() }
      const result = form.removeLineItem(0, mockMessage)
      expect(result).toBe(false)
      expect(mockMessage.warning).toHaveBeenCalledWith('At least one line item is required')
      expect(form.invoiceForm.value.line_items.length).toBeGreaterThan(0)
    })

    it('should remove line item when multiple items exist', () => {
      form.addLineItem()
      const initialCount = form.invoiceForm.value.line_items.length
      const result = form.removeLineItem(0, null)
      expect(result).toBe(true)
      expect(form.invoiceForm.value.line_items.length).toBe(initialCount - 1)
    })

    it('should update line total when quantity and price change', () => {
      const item = form.invoiceForm.value.line_items[0]
      item.quantity = 2
      item.unit_price = 10
      form.updateLineTotal(item)
      expect(item.line_total).toBe(20)
    })
  })

  describe('Calculations', () => {
    it('should calculate subtotal from line items', () => {
      const item = form.invoiceForm.value.line_items[0]
      item.line_total = 100
      expect(form.calculatedSubtotal.value).toBe(100)
    })

    it('should calculate tax amount from line items', () => {
      const item = form.invoiceForm.value.line_items[0]
      item.line_total = 100
      item.tax_percent = 10
      expect(form.calculatedTaxAmount.value).toBe(10)
    })

    it('should calculate total as subtotal plus tax', () => {
      const item = form.invoiceForm.value.line_items[0]
      item.line_total = 100
      item.tax_percent = 10
      expect(form.calculatedTotal.value).toBe(110)
    })

    it('should detect amount mismatch when calculated and extracted totals differ', () => {
      form.invoiceForm.value.summary.total = 200
      const item = form.invoiceForm.value.line_items[0]
      item.line_total = 100
      item.tax_percent = 10
      expect(form.amountMismatch.value).toBe(true)
    })
  })

  describe('Validation', () => {
    it('should validate line item with all required fields', () => {
      const item = {
        name: 'Test Item',
        quantity: 1,
        unit_price: 10,
        line_total: 10,
        tax_percent: 10
      }
      const error = form.validateLineItem(item)
      expect(error).toBeNull()
    })

    it('should return error if item name is missing', () => {
      const item = {
        name: '',
        quantity: 1,
        unit_price: 10,
        line_total: 10,
        tax_percent: 10
      }
      const error = form.validateLineItem(item)
      expect(error).toBe('Item name is required')
    })

    it('should return error if quantity is invalid', () => {
      const item = {
        name: 'Test Item',
        quantity: 0,
        unit_price: 10,
        line_total: 10,
        tax_percent: 10
      }
      const error = form.validateLineItem(item)
      expect(error).toBe('Quantity must be greater than 0')
    })

    it('should return error if tax percent is out of range', () => {
      const item = {
        name: 'Test Item',
        quantity: 1,
        unit_price: 10,
        line_total: 10,
        tax_percent: 101
      }
      const error = form.validateLineItem(item)
      expect(error).toBe('Tax percentage must be between 0 and 100')
    })

    it('should validate all line items', () => {
      const mockMessage = { error: jest.fn() }
      const item = form.invoiceForm.value.line_items[0]
      item.name = 'Test Item'
      item.quantity = 1
      item.unit_price = 10
      item.line_total = 10
      item.tax_percent = 10
      
      const result = form.validateAllLineItems(mockMessage)
      expect(result).toBe(true)
      expect(mockMessage.error).not.toHaveBeenCalled()
    })
  })

  describe('Address parsing', () => {
    it('should parse and fill address from OCR data', () => {
      const targetObj = {
        street_name: '',
        city_name: '',
        postal_zone: ''
      }
      const parsedAddress = {
        unit: 'Unit 1',
        house_number: '123',
        road: 'Main St',
        city: 'Sydney',
        postcode: '2000'
      }
      
      form.parseAndFillAddress(parsedAddress, targetObj)
      expect(targetObj.street_name).toContain('123')
      expect(targetObj.street_name).toContain('Main St')
      expect(targetObj.city_name).toBe('Sydney')
      expect(targetObj.postal_zone).toBe('2000')
    })

    it('should handle missing address fields gracefully', () => {
      const targetObj = {
        street_name: '',
        city_name: '',
        postal_zone: ''
      }
      const parsedAddress = {
        city: 'Sydney'
      }
      
      form.parseAndFillAddress(parsedAddress, targetObj)
      expect(targetObj.city_name).toBe('Sydney')
    })

    it('should not modify target if parsedAddress is null', () => {
      const targetObj = {
        street_name: 'Original',
        city_name: 'Original',
        postal_zone: 'Original'
      }
      
      form.parseAndFillAddress(null, targetObj)
      expect(targetObj.street_name).toBe('Original')
    })
  })
})

