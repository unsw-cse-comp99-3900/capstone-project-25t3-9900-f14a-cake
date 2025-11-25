<script setup>
/**
 * LineItemsEditor component for managing invoice line items.
 * 
 * @component LineItemsEditor
 * @description Provides interface for adding, removing, and editing invoice line items.
 * Supports tax percentage selection, unit selection, and automatic line total calculation.
 * 
 * @props {Array} items - Array of line item objects
 * @props {Array} unitOptions - Available unit options (default: common units)
 * 
 * @emits {void} add - Emitted when a new line item should be added
 * @emits {number} remove - Emitted when a line item should be removed with item index
 * @emits {Object} update - Emitted when a line item is updated with updated item object
 */
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  items: {
    type: Array,
    required: true
  },
  unitOptions: {
    type: Array,
    default: () => ['EA', 'HUR', 'KGM', 'MTR', 'LTR', 'SET', 'BOX', 'PKG', 'DAY']
  }
})

const emit = defineEmits(['add', 'remove', 'update'])

const setTaxPercent = (item, percent) => {
  item.tax_percent = percent
  emit('update', item)
}

// Complete unit list (code + English full name)
const unitList = [
  { code: 'EA', name: 'Each', label: 'EA (Each)' },
  { code: 'HUR', name: 'Hour', label: 'HUR (Hour)' },
  { code: 'DAY', name: 'Day', label: 'DAY (Day)' },
  { code: 'MON', name: 'Month', label: 'MON (Month)' },
  { code: 'ANN', name: 'Year', label: 'ANN (Year)' },
  { code: 'KGM', name: 'Kilogram', label: 'KGM (Kilogram)' },
  { code: 'GRM', name: 'Gram', label: 'GRM (Gram)' },
  { code: 'LTR', name: 'Litre', label: 'LTR (Litre)' },
  { code: 'MLT', name: 'Millilitre', label: 'MLT (Millilitre)' },
  { code: 'MTR', name: 'Metre', label: 'MTR (Metre)' },
  { code: 'CMT', name: 'Centimetre', label: 'CMT (Centimetre)' },
  { code: 'MMT', name: 'Millimetre', label: 'MMT (Millimetre)' },
  { code: 'KMT', name: 'Kilometre', label: 'KMT (Kilometre)' },
  { code: 'M2', name: 'Square metre', label: 'M2 (Square metre)' },
  { code: 'M3', name: 'Cubic metre', label: 'M3 (Cubic metre)' },
  { code: 'TNE', name: 'Tonne (metric ton)', label: 'TNE (Tonne)' },
  { code: 'NAR', name: 'Number of articles', label: 'NAR (Number of articles)' },
  { code: 'SET', name: 'Set', label: 'SET (Set)' },
  { code: 'PK', name: 'Package', label: 'PK (Package)' },
  { code: 'PRS', name: 'Pairs', label: 'PRS (Pairs)' },
  { code: 'BOX', name: 'Box', label: 'BOX (Box)' },
  { code: 'ROL', name: 'Roll', label: 'ROL (Roll)' },
  { code: 'BAG', name: 'Bag', label: 'BAG (Bag)' },
  { code: 'PAL', name: 'Pallet', label: 'PAL (Pallet)' },
  { code: 'CMK', name: 'Square centimetre', label: 'CMK (Square centimetre)' },
  { code: 'MMK', name: 'Square millimetre', label: 'MMK (Square millimetre)' },
  { code: 'MIN', name: 'Minute', label: 'MIN (Minute)' },
  { code: 'SEC', name: 'Second', label: 'SEC (Second)' },
  { code: 'WEE', name: 'Week', label: 'WEE (Week)' },
  { code: 'C62', name: 'One (count)', label: 'C62 (One)' },
  { code: 'E48', name: 'Working day', label: 'E48 (Working day)' },
  { code: 'PR', name: 'Pair', label: 'PR (Pair)' },
  { code: 'CCT', name: 'Carat (metric)', label: 'CCT (Carat)' },
  { code: 'DZN', name: 'Dozen', label: 'DZN (Dozen)' }
]
</script>

<template>
  <div class="form-section">
    <div class="section-header">
      <h3 class="section-heading">Line Items</h3>
      <el-button type="primary" :icon="Plus" size="small" @click="emit('add')">
        Add Item
      </el-button>
    </div>
    
    <div class="line-items-table">
      <div 
        v-for="(item, index) in items" 
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
            @click="emit('remove', index)"
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
                @change="emit('update', item)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="Unit" required>
              <el-select v-model="item.unit_code" style="width: 100%" filterable>
                <el-option 
                  v-for="unit in unitList" 
                  :key="unit.code"
                  :label="unit.label"
                  :value="unit.code"
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
                @change="emit('update', item)"
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
              <div class="tax-input-group">
                <el-input-number 
                  v-model="item.tax_percent" 
                  :min="0" 
                  :max="100"
                  :precision="2"
                  controls-position="right"
                  placeholder="Enter tax percentage"
                  class="tax-input"
                />
                <div class="tax-buttons">
                  <el-button 
                    size="small" 
                    class="tax-button tax-button-free"
                    :class="{ 'tax-button-active': item.tax_percent === 0 }"
                    @click="setTaxPercent(item, 0)"
                  >
                    Tax free
                  </el-button>
                  <el-button 
                    size="small" 
                    class="tax-button tax-button-ten"
                    :class="{ 'tax-button-active': item.tax_percent === 10 }"
                    @click="setTaxPercent(item, 10)"
                  >
                    10% Tax
                  </el-button>
                </div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--bg-section);
  border-radius: 12px;
  border: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
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
  color: var(--accent-primary);
  margin: 0;
  transition: color 0.3s ease;
}

.line-items-table {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.line-item-row {
  padding: 1rem;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.row-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.item-num {
  font-weight: 600;
  color: var(--accent-primary);
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.tax-input-group {
  display: flex;
  gap: 0.9rem;
  align-items: center;
}

.tax-input {
  flex: 1;
  min-width: 0;
}

.tax-input :deep(.el-input-number) {
  width: 100%;
}

.tax-buttons {
  display: flex;
  gap: 0.1rem;
  flex-shrink: 0;
}

.tax-button {
  white-space: nowrap;
  font-size: 0.85rem;
  padding: 0.4rem 0.75rem;
  transition: background-color 0.3s ease, 
              border-color 0.3s ease, 
              color 0.3s ease, 
              transform 0.3s ease, 
              box-shadow 0.3s ease,
              font-weight 0.3s ease;
  background-color: var(--bg-input) !important;
  border-color: var(--border-secondary) !important;
  color: var(--text-secondary) !important;
}

.tax-button:hover {
  background-color: rgba(16, 185, 129, 0.15) !important;
  border-color: rgba(16, 185, 129, 0.4) !important;
  color: var(--accent-primary) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.tax-button-active {
  background-color: rgba(16, 185, 129, 0.2) !important;
  border-color: var(--accent-primary) !important;
  color: var(--accent-primary) !important;
  font-weight: 600 !important;
  transition: background-color 0.3s ease, 
              border-color 0.3s ease, 
              color 0.3s ease, 
              transform 0.3s ease, 
              box-shadow 0.3s ease,
              font-weight 0.3s ease;
}

.tax-button-active:hover {
  background-color: rgba(16, 185, 129, 0.25) !important;
  border-color: #059669 !important;
  color: #059669 !important;
}

/* Light mode specific adjustments */
:root[data-theme="light"] .tax-button {
  background-color: #f1f5f9 !important;
  border-color: rgba(0, 0, 0, 0.12) !important;
  color: var(--text-secondary) !important;
  transition: background-color 0.3s ease, 
              border-color 0.3s ease, 
              color 0.3s ease, 
              transform 0.3s ease, 
              box-shadow 0.3s ease,
              font-weight 0.3s ease;
}

:root[data-theme="light"] .tax-button:hover {
  background-color: rgba(5, 150, 105, 0.1) !important;
  border-color: rgba(5, 150, 105, 0.3) !important;
  color: #059669 !important;
}

:root[data-theme="light"] .tax-button-active {
  background-color: rgba(5, 150, 105, 0.15) !important;
  border-color: #059669 !important;
  color: #059669 !important;
  transition: background-color 0.3s ease, 
              border-color 0.3s ease, 
              color 0.3s ease, 
              transform 0.3s ease, 
              box-shadow 0.3s ease,
              font-weight 0.3s ease;
}

:root[data-theme="light"] .tax-button-active:hover {
  background-color: rgba(5, 150, 105, 0.2) !important;
  border-color: #047857 !important;
  color: #047857 !important;
}
</style>

