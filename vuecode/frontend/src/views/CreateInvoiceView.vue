<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Download, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInvoiceForm } from '@/composables/useInvoiceForm'
import { useFileUpload } from '@/composables/useFileUpload'
import { useXmlOperations } from '@/composables/useXmlOperations'
import FileUploader from '@/components/FileUploader.vue'
import LineItemsEditor from '@/components/LineItemsEditor.vue'
import XmlValidator from '@/components/XmlValidator.vue'
import SessionWarning from '@/components/SessionWarning.vue'
import EmailSender from '@/components/EmailSender.vue'

const router = useRouter()
const currentStep = ref(0)
const isProcessing = ref(false)
const emailSent = ref(false)
const formRef = ref(null)
const sessionWarningRef = ref(null)
const emailSenderRef = ref(null)

// 使用composables
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
  validateAllLineItems
} = useInvoiceForm()

const {
  uploadFile,
  fileList,
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

const steps = [
  { title: 'Upload', description: 'Upload your invoice file' },
  { title: 'Review', description: 'Review and edit details' },
  { title: 'Generate & Validate', description: 'Generate and validate XML' },
  { title: 'Send', description: 'Send via email' },
]

const unitOptions = ['EA', 'HUR', 'KGM', 'MTR', 'LTR', 'SET', 'BOX', 'PKG', 'DAY']

const goBack = () => {
  router.push('/')
}

const handleOCRSuccess = (extracted, fileCreatedAt) => {
  invoiceForm.value = JSON.parse(JSON.stringify(extracted))
  currentStep.value = 1
  
  // 设置文件创建时间（用于准确计算剩余时间）
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

const handleGenerateXML = async () => {
  isProcessing.value = true
  await generateXML(invoiceForm.value)
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
    const response = await fetch('/api/send-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        xml_filename: xmlFilename.value
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      if (response.status === 404) {
        ElMessage.error({
          message: data.message || 'XML file has been deleted. Please go back and regenerate the XML.',
          duration: 6000,
          showClose: true
        })
      } else if (data.error_info) {
        // 显示Mailgun详细错误信息
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

    if (data.success) {
      emailSent.value = true
      // 标记第四步为完成
      currentStep.value = 4
      ElMessage.success({
        message: data.message,
        duration: 5000,
        showClose: true
      })
    }
  } catch (error) {
    console.error('Email Error:', error)
    ElMessage.error(`Failed to send email: ${error.message}`)
  } finally {
    isProcessing.value = false
  }
}

const skipToManualEntry = () => {
  // 跳过上传，直接进入手动填写
  currentStep.value = 1
  
  // 使用默认空表单
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
}

const startOver = () => {
  // 重置所有状态
  currentStep.value = 0
  uploadFile.value = null
  fileList.value = []
  xmlContent.value = ''
  xmlFilename.value = ''
  validationResult.value = null
  emailSent.value = false
  
  // 重置表单
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
  
  // 重置会话计时器
  if (sessionWarningRef.value) {
    sessionWarningRef.value.reset()
  }
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    await handleProcessOCR()
  } else if (currentStep.value === 1) {
    if (!formRef.value) {
      ElMessage.error('Form reference not found')
      return
    }

    // 验证基础表单字段
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

    // 验证商品行
    if (!validateAllLineItems(ElMessage)) {
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
    if (!validationResult.value || !validationResult.value.success) {
      ElMessage.error('Please generate and validate the XML first. Both validation rules must pass.')
      return
    }
    currentStep.value = 3
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    
    // 如果返回到第二步，重置XML状态以允许重新生成
    if (currentStep.value === 1) {
      xmlContent.value = ''
      xmlFilename.value = ''
      validationResult.value = null
    }
  }
}
</script>

<template>
  <div class="create-page">
    <!-- Session Warning -->
    <SessionWarning ref="sessionWarningRef" />

    <header class="header">
      <div class="header-content">
        <h1 class="page-title">E-Invoice Creation</h1>
        <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">
          Back to Home
        </el-button>
      </div>
    </header>

    <main class="main-content">
      <!-- Progress Steps -->
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
          v-if="currentStep > 0 && currentStep < 3"
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
          :disabled="(!uploadFile && currentStep === 0) || (currentStep === 2 && (!validationResult || !validationResult.success))"
          @click="nextStep"
        >
          {{ currentStep === 0 ? 'Process Document' : currentStep === 2 ? 'Proceed to Send' : 'Next Step' }}
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
  padding-top: 0;
}

.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(15, 20, 25, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.25rem 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

.xml-preview-compact {
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

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>
