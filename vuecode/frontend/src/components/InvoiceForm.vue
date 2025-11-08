<script setup>
import { Download } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  formRules: {
    type: Object,
    required: true
  },
  calculatedSubtotal: Number,
  calculatedTaxAmount: Number,
  calculatedTotal: Number,
  extractedTotal: Number,
  amountMismatch: Boolean,
  ocrFilename: String,
  unitOptions: Array
})

const emit = defineEmits(['update:modelValue', 'addLineItem', 'removeLineItem', 'updateLineTotal', 'downloadJSON'])

const form = defineModel()
</script>

<template>
  <div>
    <div class="section-header-with-action">
      <h2 class="section-title">Review & Edit Invoice Details</h2>
      <el-button 
        v-if="ocrFilename"
        :icon="Download" 
        type="success"
        plain
        @click="emit('downloadJSON')"
      >
        Download JSON
      </el-button>
    </div>
    
    <el-form 
      :model="modelValue" 
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
              <el-input v-model="modelValue.invoice_info.invoice_number" placeholder="INV-001" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Issue Date" prop="invoice_info.issue_date">
              <el-input v-model="modelValue.invoice_info.issue_date" placeholder="2024-01-01" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Due Date" prop="invoice_info.due_date">
              <el-input v-model="modelValue.invoice_info.due_date" placeholder="2024-01-31" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Currency" prop="invoice_info.currency_code">
              <el-input v-model="modelValue.invoice_info.currency_code" placeholder="AUD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Buyer Ref." prop="invoice_info.buyer_reference">
              <el-input v-model="modelValue.invoice_info.buyer_reference" placeholder="N/A" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- Supplier Info -->
      <div class="form-section">
        <h3 class="section-heading">Supplier Information</h3>
        <div v-if="modelValue.supplier.raw_address" class="extracted-info">
          <label class="extracted-label">Extracted Address:</label>
          <div class="extracted-content">{{ modelValue.supplier.raw_address }}</div>
        </div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Name" prop="supplier.name">
              <el-input v-model="modelValue.supplier.name" placeholder="Company Name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ABN" prop="supplier.abn">
              <el-input v-model="modelValue.supplier.abn" placeholder="12345678901" maxlength="11" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="Street Name" prop="supplier.street_name">
              <el-input v-model="modelValue.supplier.street_name" placeholder="123 Main Street" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="City" prop="supplier.city_name">
              <el-input v-model="modelValue.supplier.city_name" placeholder="Sydney" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Postal Code" prop="supplier.postal_zone">
              <el-input v-model="modelValue.supplier.postal_zone" placeholder="2000" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- Customer Info -->
      <div class="form-section">
        <h3 class="section-heading">Customer Information</h3>
        <div v-if="modelValue.customer.raw_address" class="extracted-info">
          <label class="extracted-label">Extracted Address:</label>
          <div class="extracted-content">{{ modelValue.customer.raw_address }}</div>
        </div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Name" prop="customer.name">
              <el-input v-model="modelValue.customer.name" placeholder="Customer Name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ABN" prop="customer.abn">
              <el-input v-model="modelValue.customer.abn" placeholder="12345678901" maxlength="11" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="Street Name" prop="customer.street_name">
              <el-input v-model="modelValue.customer.street_name" placeholder="456 Customer Road" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="City" prop="customer.city_name">
              <el-input v-model="modelValue.customer.city_name" placeholder="Melbourne" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Postal Code" prop="customer.postal_zone">
              <el-input v-model="modelValue.customer.postal_zone" placeholder="3000" />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- Line Items -->
      <slot name="line-items"></slot>

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
</template>

<style scoped>
.section-header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  text-align: left;
  margin: 0;
}

.invoice-form {
  margin-top: 2rem;
}

.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.section-heading {
  font-size: 1.1rem;
  font-weight: 600;
  color: #10b981;
  margin: 0 0 1.5rem 0;
}

.extracted-info {
  margin-bottom: 1.5rem;
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

.extracted-label {
  display: block;
  font-size: 0.85rem;
  color: #60a5fa;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.extracted-content {
  color: #9ca3af;
  font-size: 0.9rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
}

.summary-section {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
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
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.summary-row label { color: #9ca3af; font-weight: 500; font-size: 0.95rem; }
.summary-row .amount { color: #10b981; font-weight: 600; font-size: 1.2rem; }

.summary-row.total-row {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.summary-row.total-row .amount { font-size: 1.4rem; }

.summary-row.extracted-row {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.summary-row.extracted-row .amount { color: #60a5fa; }

.mismatch-alert,
.match-alert { margin-top: 0; }
</style>

