<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInvoiceForm } from '@/composables/useInvoiceForm'
import { useFileUpload } from '@/composables/useFileUpload'
import { useXmlOperations } from '@/composables/useXmlOperations'
import FileUploader from '@/components/FileUploader.vue'
import InvoiceForm from '@/components/InvoiceForm.vue'
import LineItemsEditor from '@/components/LineItemsEditor.vue'
import XmlValidator from '@/components/XmlValidator.vue'

const router = useRouter()
const currentStep = ref(0)
const isProcessing = ref(false)
const recipientEmail = ref('')
const formRef = ref(null)

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

const handleOCRSuccess = (extracted) => {
  invoiceForm.value = JSON.parse(JSON.stringify(extracted))
  currentStep.value = 1
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

const nextStep = async () => {
  if (currentStep.value === 0) {
    await handleProcessOCR()
  } else if (currentStep.value === 1) {
    if (!formRef.value) {
      ElMessage.error('Form reference not found')
      return
    }

    try {
      await formRef.value.validate()
    } catch {
      ElMessage.error('Please fill in all required fields correctly')
      return
    }

    if (!validateAllLineItems(ElMessage)) {
      return
    }

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
          />
        </div>

        <!-- Step 1: Edit Form -->
        <div v-show="currentStep === 1" class="step-content">
          <el-form ref="formRef" :model="invoiceForm" :rules="formRules" label-width="120px">
            <InvoiceForm
              v-model="invoiceForm"
              :form-rules="formRules"
              :calculated-subtotal="calculatedSubtotal"
              :calculated-tax-amount="calculatedTaxAmount"
              :calculated-total="calculatedTotal"
              :extracted-total="extractedTotal"
              :amount-mismatch="amountMismatch"
              :ocr-filename="ocrFilename"
              :unit-options="unitOptions"
              @download-j-s-o-n="downloadJSON"
            >
              <template #line-items>
                <LineItemsEditor
                  :items="invoiceForm.line_items"
                  :unit-options="unitOptions"
                  @add="addLineItem"
                  @remove="(index) => removeLineItem(index, ElMessage)"
                  @update="updateLineTotal"
                />
              </template>
            </InvoiceForm>
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
        <div v-show="currentStep === 3" class="step-content">
          <div class="send-email-section">
            <h2 class="section-title">Send Invoice via Email</h2>
            <p class="section-subtitle">Enter the recipient's email address</p>
            
            <div class="xml-preview-compact">
              <div class="preview-header">
                <span class="preview-title">{{ xmlFilename }}</span>
                <el-button size="small" @click="downloadXML">Download XML</el-button>
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
