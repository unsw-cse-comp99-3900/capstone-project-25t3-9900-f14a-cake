<script setup>
/**
 * HistoryView component for viewing and managing invoice history.
 * 
 * @component HistoryView
 * @description Displays paginated list of user's invoices with search and filter capabilities.
 * Supports viewing invoice details, editing invoices, downloading XML, and deleting invoices.
 * Shows invoice status indicators and creation dates.
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Document, 
  Search, 
  Filter, 
  Download, 
  Edit,
  Refresh,
  CircleCheck,
  Clock,
  Warning,
  Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/axios'

const router = useRouter()

const invoices = ref([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const statusFilter = ref('')

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'OCR Completed', value: 'ocr_completed' },
  { label: 'Processed', value: 'processed' },
  { label: 'XML Generated', value: 'xml_generated' },
  { label: 'Validated', value: 'validated' },
  { label: 'Validation Failed', value: 'validation_failed' }
]

const statusBadgeMap = {
  'ocr_completed': { type: 'info', text: 'OCR Completed' },
  'processed': { type: 'warning', text: 'Processed' },
  'xml_generated': { type: 'primary', text: 'XML Generated' },
  'validated': { type: 'success', text: 'Validated' },
  'validation_failed': { type: 'danger', text: 'Validation Failed' }
}

const fetchInvoices = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }
    
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    const response = await api.get('/invoices', { params })
    
    if (response.data && response.data.data) {
      invoices.value = response.data.data.items || []
      // Get total from pagination object
      if (response.data.data.pagination) {
        total.value = response.data.data.pagination.total || 0
      } else {
        total.value = response.data.data.total || 0
      }
    } else {
      ElMessage.error('Failed to load invoices')
    }
  } catch (error) {
    console.error('Fetch invoices error:', error)
    ElMessage.error('Failed to load invoices')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchInvoices()
}

const handleStatusFilter = () => {
  currentPage.value = 1
  fetchInvoices()
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchInvoices()
}

const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchInvoices()
}

const editInvoice = (invoice) => {
  router.push(`/edit/${invoice.id}`)
}

const downloadJSON = async (invoice) => {
  try {
    if (!invoice.ocr_data) {
      ElMessage.warning('No OCR data available for this invoice')
      return
    }
    
    const dataStr = JSON.stringify(invoice.ocr_data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${invoice.original_filename || 'invoice'}_data.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('JSON file downloaded successfully')
  } catch (error) {
    console.error('Download JSON error:', error)
    ElMessage.error('Failed to download JSON file')
  }
}

const downloadXML = async (invoice) => {
  try {
    if (!invoice.xml_content) {
      ElMessage.warning('No XML content available for this invoice')
      return
    }
    
    const dataBlob = new Blob([invoice.xml_content], { type: 'application/xml' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${invoice.original_filename || 'invoice'}.xml`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('XML file downloaded successfully')
  } catch (error) {
    console.error('Download XML error:', error)
    ElMessage.error('Failed to download XML file')
  }
}

const deleteInvoice = async (invoice) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete invoice "${invoice.original_filename || `#${invoice.id}`}"? This action cannot be undone.`,
      'Delete Invoice',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await api.delete(`/invoices/${invoice.id}`)
    
    ElMessage.success('Invoice deleted successfully')
    
    // Refresh the invoice list
    await fetchInvoices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete invoice error:', error)
      const errorMessage = error.response?.data?.message || 'Failed to delete invoice'
      ElMessage.error(errorMessage)
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const filteredInvoices = computed(() => {
  if (!searchQuery.value) {
    return invoices.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return invoices.value.filter(invoice => {
    const filename = (invoice.original_filename || '').toLowerCase()
    return filename.includes(query)
  })
})

onMounted(() => {
  fetchInvoices()
})
</script>

<template>
  <div class="history-page">
    <div class="history-container">
      <div class="history-header">
        <h1 class="page-title">Invoice History</h1>
        <p class="page-subtitle">View and manage your invoice records</p>
      </div>

      <!-- Search and Filter Bar -->
      <div class="toolbar">
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="Search by filename..."
            size="large"
            clearable
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
            class="search-input"
          />
          <el-button
            type="primary"
            size="large"
            :icon="Search"
            @click="handleSearch"
          >
            Search
          </el-button>
        </div>

        <div class="filter-section">
          <el-select
            v-model="statusFilter"
            placeholder="Filter by status"
            size="large"
            clearable
            @change="handleStatusFilter"
            class="status-filter"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <el-button
            :icon="Refresh"
            size="large"
            @click="fetchInvoices"
            :loading="loading"
          >
            Refresh
          </el-button>
        </div>
      </div>

      <!-- Invoice Table -->
      <div class="table-container">
        <el-table
          :data="filteredInvoices"
          v-loading="loading"
          stripe
          style="width: 100%"
          :empty-text="'No invoices found'"
        >
          <el-table-column prop="id" label="ID" width="80" />
          
          <el-table-column prop="original_filename" label="Filename" min-width="200">
            <template #default="{ row }">
              <span class="filename-text">{{ row.original_filename || 'N/A' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="Status" width="160">
            <template #default="{ row }">
              <el-tag
                :type="statusBadgeMap[row.status]?.type || 'info'"
                size="small"
                :title="statusBadgeMap[row.status]?.text || row.status"
              >
                {{ statusBadgeMap[row.status]?.text || row.status }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="Created At" width="180">
            <template #default="{ row }">
              <span class="date-text">{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="updated_at" label="Updated At" width="180">
            <template #default="{ row }">
              <span class="date-text">{{ formatDate(row.updated_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="Actions" width="350" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                :icon="Edit"
                @click="editInvoice(row)"
              >
                Edit
              </el-button>
              <el-button
                type="success"
                size="small"
                :icon="Download"
                :disabled="!row.ocr_data"
                @click="downloadJSON(row)"
              >
                JSON
              </el-button>
              <el-button
                type="warning"
                size="small"
                :icon="Download"
                :disabled="!row.xml_content"
                @click="downloadXML(row)"
              >
                XML
              </el-button>
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                @click="deleteInvoice(row)"
              >
                Delete
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.history-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  padding: 2rem;
  transition: background 0.3s ease;
}

.history-container {
  max-width: 1400px;
  margin: 0 auto;
}

.history-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.page-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.search-section {
  display: flex;
  gap: 0.5rem;
  flex: 1;
  min-width: 300px;
}

.search-input {
  flex: 1;
}

.filter-section {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-filter {
  width: 180px;
}

.table-container {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: var(--shadow-md);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.pagination-container {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

.filename-text {
  color: var(--text-primary);
  font-weight: 500;
  transition: color 0.3s ease;
}

.date-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.invoice-detail {
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h3 {
  color: var(--accent-primary);
  margin-bottom: 1rem;
  font-size: 1.2rem;
  font-weight: 600;
  transition: color 0.3s ease;
}

.json-viewer,
.xml-viewer {
  background: var(--bg-section);
  padding: 1rem;
  border-radius: 8px;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0;
  overflow-x: auto;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.dialog-footer {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

/* Element Plus Overrides - Table and Pagination specific styles */
:deep(.el-table) {
  background-color: transparent !important;
  color: var(--text-primary) !important;
}

:deep(.el-table th) {
  background-color: var(--bg-section) !important;
  color: var(--text-primary) !important;
  border-bottom-color: var(--border-primary) !important;
}

:deep(.el-table th.el-table-fixed-column--right) {
  background-color: var(--bg-section) !important;
  color: var(--text-primary) !important;
}

:deep(.el-table td) {
  background-color: transparent !important;
  border-bottom-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-table td.el-table-fixed-column--right) {
  background-color: transparent !important;
  border-bottom-color: var(--border-primary) !important;
}

:deep(.el-table tr) {
  background-color: transparent !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: var(--bg-section) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table-fixed-column--right) {
  background-color: var(--bg-section) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td.el-table-fixed-column--right) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table__body tr:hover > td) {
  background-color: var(--bg-hover) !important;
}

:deep(.el-table__body tr:hover > td.el-table-fixed-column--right) {
  background-color: var(--bg-hover) !important;
}

/* Pagination Styles */
:deep(.el-pagination) {
  color: var(--text-primary) !important;
}

:deep(.el-pagination .el-pagination__total) {
  color: var(--text-secondary) !important;
}

:deep(.el-pagination button) {
  color: var(--text-secondary) !important;
  background-color: var(--bg-input) !important;
  border-color: var(--border-primary) !important;
}

:deep(.el-pagination button:hover) {
  color: var(--accent-primary) !important;
  background-color: var(--bg-hover) !important;
}

:deep(.el-pagination button:disabled) {
  color: var(--text-tertiary) !important;
  background-color: var(--bg-input) !important;
  opacity: 0.5;
}

:deep(.el-pagination .el-pager li) {
  background-color: var(--bg-input) !important;
  color: var(--text-secondary) !important;
  border-color: var(--border-primary) !important;
}

:deep(.el-pagination .el-pager li:hover) {
  color: var(--accent-primary) !important;
  background-color: var(--bg-hover) !important;
}

:deep(.el-pagination .el-pager li.is-active) {
  background-color: var(--accent-primary) !important;
  color: #ffffff !important;
  border-color: var(--accent-primary) !important;
}

/* Pagination Select Dropdown */
:deep(.el-pagination .el-select .el-input__wrapper) {
  background-color: var(--bg-input) !important;
  border-color: var(--border-primary) !important;
}

:deep(.el-pagination .el-select .el-input__wrapper:hover) {
  border-color: var(--border-focus) !important;
}

:deep(.el-pagination .el-select .el-select__placeholder),
:deep(.el-pagination .el-select .el-select__selected-item) {
  color: var(--text-secondary) !important;
}

:deep(.el-pagination .el-select .el-select__caret) {
  color: var(--text-secondary) !important;
}

:deep(.el-pagination .el-select .el-select__wrapper:hover .el-select__caret) {
  color: var(--accent-primary) !important;
}

/* Pagination Input (Go to) */
:deep(.el-pagination .el-pagination__jump .el-pagination__editor) {
  background-color: var(--bg-input) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-pagination .el-pagination__jump .el-pagination__editor:focus) {
  border-color: var(--border-focus) !important;
}

:deep(.el-pagination .el-pagination__jump .el-pagination__editor::placeholder) {
  color: var(--text-tertiary) !important;
}

/* Tag Styles - Improve contrast for status tags */
:deep(.el-tag) {
  font-weight: 500;
}

:deep(.el-tag.el-tag--info) {
  background-color: var(--bg-section) !important;
  border-color: var(--border-secondary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-tag.el-tag--success) {
  color: var(--accent-success) !important;
}

:deep(.el-tag.el-tag--warning) {
  color: var(--accent-warning) !important;
}

:deep(.el-tag.el-tag--danger) {
  color: var(--accent-danger) !important;
}

:deep(.el-tag.el-tag--primary) {
  color: var(--accent-primary) !important;
}

/* Descriptions Table */
:deep(.el-descriptions__table td),
:deep(.el-descriptions__table th) {
  border-color: var(--border-primary) !important;
}

/* Search Input - Ensure light gray background in dark mode */
:deep(.search-input .el-input__wrapper) {
  background-color: var(--bg-input) !important;
}

:deep(.search-input .el-input__inner) {
  background-color: transparent !important;
}

/* Status Filter Select - Ensure light gray background in dark mode */
:deep(.status-filter .el-select__wrapper),
:deep(.status-filter .el-select .el-input__wrapper),
:deep(.status-filter .el-select__wrapper.el-tooltip__trigger) {
  background-color: var(--bg-input) !important;
}

:deep(.status-filter .el-select__selected-item) {
  background-color: transparent !important;
}

/* Pagination Select Dropdown - Ensure light gray background in dark mode */
:deep(.el-pagination .el-select__wrapper),
:deep(.el-pagination .el-select__wrapper.el-tooltip__trigger),
:deep(.el-pagination .el-select__wrapper.el-tooltip__trigger.el-tooltip__trigger) {
  background-color: var(--bg-input) !important;
}

/* Pagination Go to Input - Ensure light gray background in dark mode */
:deep(.el-pagination .el-pagination__jump .el-pagination__editor) {
  background-color: var(--bg-input) !important;
  -webkit-box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
  box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
}

:deep(.el-pagination .el-pagination__jump .el-pagination__editor:focus) {
  background-color: var(--bg-input) !important;
  -webkit-box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
  box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
}
</style>

