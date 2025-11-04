<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Upload, ArrowLeft, DocumentChecked, Plus, Delete, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const currentStep = ref(0)
const uploadFile = ref(null)
const fileList = ref([])
const ocrResult = ref(null)
const ocrFilename = ref('')
const isProcessing = ref(false)
const xmlContent = ref('')
const xmlFilename = ref('')
const recipientEmail = ref('')

// 表单引用
const formRef = ref(null)

// 表单数据
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

// 表单验证规则
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
      { pattern: /^[A-Z]{3}$/, message: 'Must be 3 uppercase letters (e.g., AUD)', trigger: 'blur' }
    ],
    buyer_reference: [
      { required: true, message: 'Buyer reference is required', trigger: 'blur' }
    ]
  },
  supplier: {
    name: [
      { required: true, message: 'Supplier name is required', trigger: 'blur' }
    ],
    street_name: [
      { required: true, message: 'Street name is required', trigger: 'blur' }
    ],
    city_name: [
      { required: true, message: 'City is required', trigger: 'blur' }
    ],
    postal_zone: [
      { required: true, message: 'Postal code is required', trigger: 'blur' }
    ],
    abn: [
      { required: true, message: 'ABN is required', trigger: 'blur' },
      { pattern: /^\d{11}$/, message: 'ABN must be 11 digits', trigger: 'blur' }
    ]
  },
  customer: {
    name: [
      { required: true, message: 'Customer name is required', trigger: 'blur' }
    ],
    street_name: [
      { required: true, message: 'Street name is required', trigger: 'blur' }
    ],
    city_name: [
      { required: true, message: 'City is required', trigger: 'blur' }
    ],
    postal_zone: [
      { required: true, message: 'Postal code is required', trigger: 'blur' }
    ],
    abn: [
      { required: true, message: 'ABN is required', trigger: 'blur' },
      { pattern: /^\d{11}$/, message: 'ABN must be 11 digits', trigger: 'blur' }
    ]
  }
}

// 验证单个商品行
const validateLineItem = (item) => {
  if (!item.name || item.name.trim() === '') {
    return 'Item name is required'
  }
  if (!item.quantity || item.quantity <= 0) {
    return 'Quantity must be greater than 0'
  }
  if (!item.unit_price || item.unit_price < 0) {
    return 'Unit price must be 0 or greater'
  }
  if (!item.line_total || item.line_total < 0) {
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

// 验证所有商品行
const validateAllLineItems = () => {
  for (let i = 0; i < invoiceForm.value.line_items.length; i++) {
    const error = validateLineItem(invoiceForm.value.line_items[i])
    if (error) {
      ElMessage.error(`Line item ${i + 1}: ${error}`)
      return false
    }
  }
  return true
}

const steps = [
  { title: 'Upload', description: 'Upload your invoice file' },
  { title: 'Review', description: 'Review and edit details' },
  { title: 'Generate', description: 'Generate XML' },
  { title: 'Send', description: 'Send via email' },
]

const unitOptions = ['EA', 'HUR', 'KGM', 'MTR', 'LTR', 'SET', 'BOX', 'PKG', 'DAY']

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

const beforeUpload = (file) => {
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg']
  const isAllowedType = allowedTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowedType) {
    ElMessage.error('Only PDF, JPG, and JPEG files are supported!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('File size cannot exceed 10MB!')
    return false
  }
  return true
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
  fileList.value = [file]
}

const handleRemove = () => {
  uploadFile.value = null
  fileList.value = []
}

const processOCR = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('Please upload a file first!')
    return
  }

  isProcessing.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)

    const response = await fetch('/api/ocr', {
      method: 'POST',
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
      const errorMsg = data.error || 'OCR processing failed'
      const details = data.details ? `\n${data.details}` : ''
      ElMessage.error({
        message: errorMsg + details,
        duration: 5000,
        showClose: true
      })
      return
    }

    if (data.success && data.extracted) {
      ocrResult.value = data
      ocrFilename.value = data.json_filename || ''
      
      invoiceForm.value = JSON.parse(JSON.stringify(data.extracted))
      
      ElMessage.success('Document processed successfully!')
      currentStep.value = 1
    } else {
      ElMessage.error('Unexpected response format')
    }
  } catch (error) {
    console.error('OCR Error:', error)
    ElMessage.error({
      message: `Failed to process document: ${error.message}`,
      duration: 5000,
      showClose: true
    })
  } finally {
    isProcessing.value = false
  }
}

const downloadJSON = () => {
  if (!ocrFilename.value) {
    ElMessage.warning('No JSON file available')
    return
  }
  
  const url = `/api/download-json/${ocrFilename.value}`
  const a = document.createElement('a')
  a.href = url
  a.download = ocrFilename.value
  a.click()
  ElMessage.success('Downloading JSON file...')
}

const generateXML = async () => {
  isProcessing.value = true
  
  try {
    const response = await fetch('/api/generate-xml', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(invoiceForm.value),
    })

    const data = await response.json()

    if (!response.ok) {
      ElMessage.error(data.error || 'Failed to generate XML')
      return
    }

    if (data.success) {
      xmlContent.value = data.xml_content
      xmlFilename.value = data.filename
      ElMessage.success('XML generated successfully!')
      currentStep.value = 3
    }
  } catch (error) {
    console.error('XML Generation Error:', error)
    ElMessage.error(`Failed to generate XML: ${error.message}`)
  } finally {
    isProcessing.value = false
  }
}

const downloadXML = () => {
  if (!xmlContent.value) {
    ElMessage.warning('No XML content available')
    return
  }
  
  const blob = new Blob([xmlContent.value], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = xmlFilename.value || 'invoice.xml'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('XML downloaded!')
}

const sendEmail = async () => {
  if (!recipientEmail.value) {
    ElMessage.warning('Please enter an email address')
    return
  }
  
  if (!xmlFilename.value) {
    ElMessage.warning('Please generate XML first')
    return
  }
  
  isProcessing.value = true
  
  try {
    const response = await fetch('/api/send-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: recipientEmail.value,
        xml_filename: xmlFilename.value
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      ElMessage.error(data.error || 'Failed to send email')
      return
    }

    if (data.success) {
      ElMessage.success(data.message)
    }
  } catch (error) {
    console.error('Email Error:', error)
    ElMessage.error(`Failed to send email: ${error.message}`)
  } finally {
    isProcessing.value = false
  }
}

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

const removeLineItem = (index) => {
  if (invoiceForm.value.line_items.length <= 1) {
    ElMessage.warning('At least one line item is required')
    return
  }
  invoiceForm.value.line_items.splice(index, 1)
}

const updateLineTotal = (item) => {
  const qty = parseFloat(item.quantity) || 0
  const price = parseFloat(item.unit_price) || 0
  item.line_total = qty * price
}

const goBack = () => {
  router.push('/')
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    await processOCR()
  } else if (currentStep.value === 1) {
    // 验证表单
    if (!formRef.value) {
      ElMessage.error('Form reference not found')
      return
    }

    try {
      // 验证基础字段
      await formRef.value.validate()
    } catch {
      ElMessage.error('Please fill in all required fields correctly')
      return
    }

    // 验证商品行
    if (!validateAllLineItems()) {
      return
    }

    // 金额验证
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
    
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    await generateXML()
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}
</script>

<template>
  <div class="create-page">
    <header class="header">
      <div class="header-content">
        <h1 class="page-title">E-Invoice Creation</h1>
        <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">
          Back to Home
        </el-button>
      </div>
    </header>

    <main class="main-content">
      <div class="steps">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{ active: index === currentStep, completed: index < currentStep }"
        >
          <div class="step-indicator">
            <span v-if="index < currentStep">✓</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-info">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.description }}</div>
          </div>
        </div>
      </div>

      <div class="content-card">
        <!-- Step 0: Upload -->
        <div v-show="currentStep === 0" class="step-content">
          <div class="upload-area">
            <h2 class="section-title">Upload Invoice Document</h2>
            <p class="section-subtitle">Supported formats: PDF, JPG, JPEG (Max: 10MB)</p>
            
            <el-upload
              class="uploader"
              drag
              :before-upload="beforeUpload"
              :on-change="handleFileChange"
              :on-remove="handleRemove"
              :file-list="fileList"
              :auto-upload="false"
              :limit="1"
            >
              <el-icon class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">
                <div class="upload-title">Drop file here or click to upload</div>
                <div class="upload-hint">PDF, JPG, JPEG up to 10MB</div>
              </div>
            </el-upload>

            <div v-if="uploadFile" class="file-preview">
              <el-icon class="file-icon"><DocumentChecked /></el-icon>
              <div class="file-details">
                <div class="file-name">{{ uploadFile.name }}</div>
                <div class="file-size">{{ (uploadFile.size / 1024).toFixed(2) }} KB</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 1: Edit Form -->
        <div v-show="currentStep === 1" class="step-content form-step">
          <div class="section-header-with-action">
            <h2 class="section-title">Review & Edit Invoice Details</h2>
            <el-button 
              v-if="ocrFilename"
              :icon="Download" 
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
              <div v-if="invoiceForm.supplier.raw_address" class="extracted-info">
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
                    <el-input v-model="invoiceForm.supplier.street_name" placeholder="123 Main Street" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="City" prop="supplier.city_name">
                    <el-input v-model="invoiceForm.supplier.city_name" placeholder="Sydney" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Postal Code" prop="supplier.postal_zone">
                    <el-input v-model="invoiceForm.supplier.postal_zone" placeholder="2000" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Customer Info -->
            <div class="form-section">
              <h3 class="section-heading">Customer Information</h3>
              <div v-if="invoiceForm.customer.raw_address" class="extracted-info">
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
                    <el-input v-model="invoiceForm.customer.street_name" placeholder="456 Customer Road" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="City" prop="customer.city_name">
                    <el-input v-model="invoiceForm.customer.city_name" placeholder="Melbourne" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Postal Code" prop="customer.postal_zone">
                    <el-input v-model="invoiceForm.customer.postal_zone" placeholder="3000" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- Line Items -->
            <div class="form-section">
              <div class="section-header">
                <h3 class="section-heading">Line Items</h3>
                <el-button type="primary" :icon="Plus" size="small" @click="addLineItem">
                  Add Item
                </el-button>
              </div>
              
              <div class="line-items-table">
                <div 
                  v-for="(item, index) in invoiceForm.line_items" 
                  :key="index"
                  class="line-item-row"
                >
                  <div class="row-header">
                    <span class="item-num">#{{ index + 1 }}</span>
                    <el-button 
                      type="danger" 
                      :icon="Delete" 
                      size="small" 
                      text
                      @click="removeLineItem(index)"
                    />
                  </div>
                  <el-row :gutter="16">
                    <el-col :span="24">
                      <el-form-item label="Name" required>
                        <el-input v-model="item.name" placeholder="Product or service name" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="6">
                      <el-form-item label="Quantity" required>
                        <el-input-number 
                          v-model="item.quantity" 
                          :min="0.01" 
                          :precision="2"
                          controls-position="right"
                          style="width: 100%"
                          @change="updateLineTotal(item)"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="6">
                      <el-form-item label="Unit" required>
                        <el-select v-model="item.unit_code" style="width: 100%">
                          <el-option 
                            v-for="unit in unitOptions" 
                            :key="unit"
                            :label="unit"
                            :value="unit"
                          />
                        </el-select>
                      </el-form-item>
                    </el-col>
                    <el-col :span="6">
                      <el-form-item label="Unit Price" required>
                        <el-input-number 
                          v-model="item.unit_price" 
                          :min="0" 
                          :precision="2"
                          controls-position="right"
                          style="width: 100%"
                          @change="updateLineTotal(item)"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="6">
                      <el-form-item label="Line Total" required>
                        <el-input-number 
                          v-model="item.line_total" 
                          :min="0" 
                          :precision="2"
                          controls-position="right"
                          style="width: 100%"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="Tax %" required>
                        <el-input-number 
                          v-model="item.tax_percent" 
                          :min="0" 
                          :max="100"
                          :precision="2"
                          controls-position="right"
                          placeholder="Enter tax percentage"
                          style="width: 100%"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>
              </div>
            </div>

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

        <!-- Step 2: Preview XML -->
        <div v-show="currentStep === 2" class="step-content">
          <h2 class="section-title">Ready to Generate XML</h2>
          <p class="section-subtitle">Click the button below to generate a UBL-compliant XML invoice</p>
          <div class="preview-action">
            <el-button 
              type="primary" 
              size="large"
              :loading="isProcessing"
              @click="generateXML"
            >
              Generate XML
            </el-button>
          </div>
        </div>

        <!-- Step 3: Send Email -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="send-email-section">
            <h2 class="section-title">Send Invoice via Email</h2>
            <p class="section-subtitle">Enter the recipient's email address to send the XML invoice</p>
            
            <div class="xml-preview">
              <div class="preview-header">
                <span class="preview-title">Generated XML File</span>
                <el-button :icon="Download" size="small" @click="downloadXML">
                  Download XML
                </el-button>
              </div>
              <div class="preview-content">
                <pre>{{ xmlContent.slice(0, 500) }}...</pre>
              </div>
            </div>

            <div class="email-form">
              <el-form label-width="120px">
                <el-form-item label="Recipient Email">
                  <el-input 
                    v-model="recipientEmail" 
                    placeholder="example@email.com"
                    type="email"
                    size="large"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    size="large"
                    :loading="isProcessing"
                    :disabled="!recipientEmail"
                    @click="sendEmail"
                  >
                    Send Invoice
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <el-button 
          v-if="currentStep > 0 && currentStep < 3"
          size="large" 
          @click="prevStep"
        >
          Previous
        </el-button>
        <el-button 
          v-if="currentStep < 2"
          type="primary" 
          size="large" 
          :loading="isProcessing"
          :disabled="!uploadFile && currentStep === 0"
          @click="nextStep"
        >
          {{ currentStep === 0 ? 'Process Document' : 'Next Step' }}
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
}

.header {
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.25rem 2rem;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #10b981;
  margin: 0;
}

.back-btn {
  color: #9ca3af;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2.5rem 2rem;
}

.steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2.5rem;
  gap: 1rem;
}

.step {
  flex: 1;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  opacity: 0.5;
  transition: opacity 0.3s ease;
}

.step.active,
.step.completed {
  opacity: 1;
}

.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #6b7280;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.step.active .step-indicator {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
  color: #10b981;
}

.step.completed .step-indicator {
  background: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.25rem;
}

.step-desc {
  font-size: 0.8rem;
  color: #6b7280;
}

.content-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2.5rem;
  min-height: 400px;
}

.step-content {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.5rem;
  text-align: center;
}

.section-subtitle {
  font-size: 0.95rem;
  color: #9ca3af;
  text-align: center;
  margin-bottom: 2rem;
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

/* Upload Area */
.upload-area {
  max-width: 700px;
  margin: 0 auto;
}

:deep(.uploader) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background: rgba(16, 185, 129, 0.05);
  border: 2px dashed rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  padding: 3rem 2rem;
  width: 100%;
}

:deep(.el-upload-dragger:hover) {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.upload-icon {
  font-size: 48px;
  color: #10b981;
  margin-bottom: 1rem;
}

.upload-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 0.5rem;
}

.upload-hint {
  font-size: 0.9rem;
  color: #6b7280;
}

.file-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 32px;
  color: #10b981;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 0.95rem;
  color: #ffffff;
  margin-bottom: 0.25rem;
}

.file-size {
  font-size: 0.85rem;
  color: #6b7280;
}

/* Form */
.form-step {
  max-width: 100%;
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
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

:deep(.el-form-item__label) {
  color: #9ca3af !important;
  font-weight: 500;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset !important;
}

:deep(.el-form-item__error) {
  color: #f56c6c;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #10b981 inset !important;
}

:deep(.el-input__inner) {
  color: #ffffff !important;
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05) !important;
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05) !important;
}

.line-items-table {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.line-item-row {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.item-num {
  font-weight: 600;
  color: #10b981;
  font-size: 0.9rem;
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

.summary-row label {
  color: #9ca3af;
  font-weight: 500;
  font-size: 0.95rem;
}

.summary-row .amount {
  color: #10b981;
  font-weight: 600;
  font-size: 1.2rem;
}

.summary-row.total-row {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.summary-row.total-row .amount {
  font-size: 1.4rem;
}

.summary-row.extracted-row {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.summary-row.extracted-row .amount {
  color: #60a5fa;
}

.mismatch-alert,
.match-alert {
  margin-top: 0;
}

/* Step 2 */
.preview-action {
  display: flex;
  justify-content: center;
  margin-top: 3rem;
}

/* Step 3 */
.send-email-section {
  max-width: 800px;
  margin: 0 auto;
}

.xml-preview {
  margin: 2rem 0;
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
}

.preview-title {
  font-weight: 600;
  color: #10b981;
}

.preview-content {
  padding: 1rem;
  background: rgba(0, 0, 0, 0.3);
  max-height: 300px;
  overflow-y: auto;
}

.preview-content pre {
  color: #9ca3af;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
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

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>
