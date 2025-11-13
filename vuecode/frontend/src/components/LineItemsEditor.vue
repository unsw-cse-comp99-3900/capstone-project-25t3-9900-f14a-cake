<script setup>
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

// 完整的单位列表（代码 + 英文全称）
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
</template>

<style scoped>
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
  margin: 0;
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
</style>

