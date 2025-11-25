<script setup>
/**
 * AdminView component for administrative dashboard.
 * 
 * @component AdminView
 * @description Admin-only view for managing users and viewing system statistics.
 * Provides user management (activate/deactivate), invoice statistics, and user search/filter.
 * Displays system-wide statistics including user counts and invoice status breakdowns.
 */
import { ref, onMounted, computed } from 'vue'
import { 
  User, 
  UserFilled,
  Document,
  Search, 
  Filter, 
  Refresh,
  Switch,
  DataAnalysis
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/axios'

// Statistics
const stats = ref({
  users: {
    total: 0,
    active: 0,
    admin: 0,
    regular: 0
  },
  invoices: {
    total: 0,
    by_status: {},
    recent_7_days: 0
  }
})
const statsLoading = ref(false)

// Users
const users = ref([])
const usersLoading = ref(false)
const totalUsers = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

const roleOptions = [
  { label: 'All', value: '' },
  { label: 'Admin', value: 'admin' },
  { label: 'User', value: 'user' }
]

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Active', value: 'true' },
  { label: 'Inactive', value: 'false' }
]

const fetchStats = async () => {
  statsLoading.value = true
  try {
    const response = await api.get('/admin/stats')
    
    if (response.data && response.data.data) {
      stats.value = response.data.data
    } else {
      ElMessage.error('Failed to load statistics')
    }
  } catch (error) {
    console.error('Fetch stats error:', error)
    ElMessage.error('Failed to load statistics')
  } finally {
    statsLoading.value = false
  }
}

const fetchUsers = async () => {
  usersLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    
    if (roleFilter.value) {
      params.role = roleFilter.value
    }
    
    if (statusFilter.value) {
      params.is_active = statusFilter.value
    }
    
    const response = await api.get('/admin/users', { params })
    
    if (response.data && response.data.data) {
      users.value = response.data.data.items || []
      if (response.data.data.pagination) {
        totalUsers.value = response.data.data.pagination.total || 0
      } else {
        totalUsers.value = response.data.data.total || 0
      }
    } else {
      ElMessage.error('Failed to load users')
    }
  } catch (error) {
    console.error('Fetch users error:', error)
    ElMessage.error('Failed to load users')
  } finally {
    usersLoading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleRoleFilter = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleStatusFilter = () => {
  currentPage.value = 1
  fetchUsers()
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchUsers()
}

const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers()
}

const handleSortChange = ({ prop, order }) => {
  if (prop) {
    sortBy.value = prop
    sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
    currentPage.value = 1
    fetchUsers()
  }
}

const toggleUserStatus = async (user) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to ${user.is_active ? 'disable' : 'enable'} user "${user.username}"?`,
      'Confirm Action',
      {
        confirmButtonText: user.is_active ? 'Disable' : 'Enable',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: user.is_active ? 'el-button--danger' : 'el-button--success'
      }
    )
    
    const response = await api.put(`/admin/users/${user.id}/toggle`)
    
    if (response.data && response.data.data) {
      ElMessage.success(response.data.message || `User ${user.is_active ? 'disabled' : 'enabled'} successfully`)
      await fetchUsers()
      await fetchStats()
    } else {
      ElMessage.error('Failed to update user status')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Toggle user status error:', error)
      const errorMessage = error.response?.data?.message || 'Failed to update user status'
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

const filteredUsers = computed(() => {
  if (!searchQuery.value) {
    return users.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => {
    const username = (user.username || '').toLowerCase()
    const email = (user.email || '').toLowerCase()
    return username.includes(query) || email.includes(query)
  })
})

onMounted(() => {
  fetchStats()
  fetchUsers()
})
</script>

<template>
  <div class="admin-page">
    <div class="admin-container">
      <div class="admin-header">
        <h1 class="page-title">Admin Dashboard</h1>
        <p class="page-subtitle">Manage users and view system statistics</p>
      </div>

      <!-- Statistics Dashboard -->
      <div class="stats-section">
        <div class="stats-header">
          <h2 class="section-title">
            <el-icon><DataAnalysis /></el-icon>
            System Statistics
          </h2>
          <el-button
            :icon="Refresh"
            size="small"
            @click="fetchStats"
            :loading="statsLoading"
          >
            Refresh
          </el-button>
        </div>

        <div class="stats-grid">
          <!-- User Statistics -->
          <div class="stat-card">
            <div class="stat-icon users">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.users.total }}</div>
              <div class="stat-label">Total Users</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.users.active }}</div>
              <div class="stat-label">Active Users</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon admin">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.users.admin }}</div>
              <div class="stat-label">Admin Users</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon regular">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.users.regular }}</div>
              <div class="stat-label">Regular Users</div>
            </div>
          </div>

          <!-- Invoice Statistics -->
          <div class="stat-card">
            <div class="stat-icon invoices">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.invoices.total }}</div>
              <div class="stat-label">Total Invoices</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon recent">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.invoices.recent_7_days }}</div>
              <div class="stat-label">Recent (7 days)</div>
            </div>
          </div>
        </div>
      </div>

      <!-- User Management -->
      <div class="users-section">
        <div class="users-header">
          <h2 class="section-title">
            <el-icon><UserFilled /></el-icon>
            User Management
          </h2>
        </div>

        <!-- Search and Filter Bar -->
        <div class="toolbar">
          <div class="search-section">
            <el-input
              v-model="searchQuery"
              placeholder="Search by username or email..."
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
              v-model="roleFilter"
              placeholder="Filter by role"
              size="large"
              clearable
              @change="handleRoleFilter"
              class="role-filter"
            >
              <el-option
                v-for="option in roleOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>

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
              @click="fetchUsers"
              :loading="usersLoading"
            >
              Refresh
            </el-button>
          </div>
        </div>

        <!-- Users Table -->
        <div class="table-container">
          <el-table
            :data="filteredUsers"
            v-loading="usersLoading"
            stripe
            style="width: 100%"
            :empty-text="'No users found'"
            @sort-change="handleSortChange"
            :default-sort="{ prop: sortBy, order: sortOrder === 'asc' ? 'ascending' : 'descending' }"
          >
            <el-table-column prop="id" label="ID" width="80" />
            
            <el-table-column 
              prop="username" 
              label="Username" 
              min-width="150"
              sortable="custom"
            >
              <template #default="{ row }">
                <span class="username-text">{{ row.username || 'N/A' }}</span>
              </template>
            </el-table-column>

            <el-table-column 
              prop="email" 
              label="Email" 
              min-width="200"
              sortable="custom"
            >
              <template #default="{ row }">
                <span class="email-text">{{ row.email || 'N/A' }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="role" label="Role" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="row.role === 'admin' ? 'danger' : 'primary'"
                  size="small"
                >
                  {{ row.role === 'admin' ? 'Admin' : 'User' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column 
              prop="invoice_count" 
              label="Invoices" 
              width="120"
              sortable="custom"
              align="center"
            >
              <template #default="{ row }">
                <span class="invoice-count-text">{{ row.invoice_count || 0 }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="is_active" label="Status" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="row.is_active ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.is_active ? 'Active' : 'Inactive' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column 
              prop="created_at" 
              label="Created At" 
              width="180"
              sortable="custom"
            >
              <template #default="{ row }">
                <span class="date-text">{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>

            <el-table-column label="Actions" width="150" fixed="right">
              <template #default="{ row }">
                <el-button
                  :type="row.is_active ? 'danger' : 'success'"
                  size="small"
                  :icon="Switch"
                  @click="toggleUserStatus(row)"
                >
                  {{ row.is_active ? 'Disable' : 'Enable' }}
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
              :total="totalUsers"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  padding: 2rem;
  transition: background 0.3s ease;
}

.admin-container {
  max-width: 1400px;
  margin: 0 auto;
}

.admin-header {
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

.stats-section,
.users-section {
  margin-bottom: 3rem;
}

.stats-header,
.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.3s ease;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-md);
}

.stat-card:hover {
  border-color: var(--border-accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.stat-icon.users {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
}

.stat-icon.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.stat-icon.admin {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.stat-icon.regular {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.stat-icon.invoices {
  background: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.stat-icon.recent {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
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

.role-filter,
.status-filter {
  width: 150px;
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

.username-text,
.email-text {
  color: var(--text-primary);
  font-weight: 500;
  transition: color 0.3s ease;
}

.date-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.invoice-count-text {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 1rem;
  transition: color 0.3s ease;
}

/* Element Plus Overrides - Most styles are handled in global element-plus-theme.css */

/* Table Styles - Ensure correct background colors in dark mode */
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

:deep(.el-button--danger) {
  background-color: #ef4444;
  border-color: #ef4444;
}

:deep(.el-button--danger:hover) {
  background-color: #dc2626;
  border-color: #dc2626;
}

:deep(.el-pagination) {
  color: var(--text-primary) !important;
}

:deep(.el-pagination .el-pagination__total),
:deep(.el-pagination .el-pager li) {
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

:deep(.el-pagination .el-select .el-select__wrapper) {
  background-color: var(--bg-input) !important;
  border-color: var(--border-primary) !important;
}

:deep(.el-pagination .el-select .el-select__wrapper:hover) {
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

:deep(.el-pagination .el-pagination__jump .el-pagination__editor) {
  background-color: var(--bg-input) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
  -webkit-box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
  box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
}

:deep(.el-pagination .el-pagination__jump .el-pagination__editor:focus) {
  border-color: var(--border-focus) !important;
  background-color: var(--bg-input) !important;
  -webkit-box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
  box-shadow: 0 0 0 1000px var(--bg-input) inset !important;
}

:deep(.el-pagination .el-pagination__jump .el-pagination__editor::placeholder) {
  color: var(--text-tertiary) !important;
}

/* Message box styles are handled in global element-plus-theme.css */

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
  background-color: transparent !important;
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

:deep(.el-select__wrapper) {
  background-color: var(--bg-input) !important;
}

:deep(.el-select__wrapper.el-tooltip__trigger) {
  background-color: var(--bg-input) !important;
}

:deep(.el-select__wrapper.el-tooltip__trigger.el-tooltip__trigger) {
  background-color: var(--bg-input) !important;
}

:deep(.el-select .el-input__inner) {
  color: var(--text-primary) !important;
  background-color: transparent !important;
}

:deep(.el-select__selected-item) {
  color: var(--text-primary) !important;
  background-color: transparent !important;
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

/* Search Input - Ensure light gray background in dark mode */
:deep(.search-input .el-input__wrapper) {
  background-color: var(--bg-input) !important;
}

:deep(.search-input .el-input__inner) {
  background-color: transparent !important;
}

/* Filter Selects - Ensure light gray background in dark mode */
:deep(.role-filter .el-select__wrapper),
:deep(.role-filter .el-select .el-input__wrapper),
:deep(.role-filter .el-select__wrapper.el-tooltip__trigger),
:deep(.status-filter .el-select__wrapper),
:deep(.status-filter .el-select .el-input__wrapper),
:deep(.status-filter .el-select__wrapper.el-tooltip__trigger) {
  background-color: var(--bg-input) !important;
}

:deep(.role-filter .el-select__selected-item),
:deep(.status-filter .el-select__selected-item) {
  background-color: transparent !important;
}
</style>

