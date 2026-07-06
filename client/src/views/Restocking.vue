<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-controls">
          <div class="budget-slider-wrap">
            <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
            <input
              id="budget-slider"
              v-model.number="budget"
              type="range"
              class="budget-slider"
              :min="0"
              :max="sliderMax"
              :step="sliderStep"
            />
          </div>
          <div class="budget-stats">
            <div class="budget-stat">
              <div class="stat-label">{{ t('restocking.budget') }}</div>
              <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
            </div>
            <div class="budget-stat">
              <div class="stat-label">{{ t('restocking.selectedCost') }}</div>
              <div class="stat-value">{{ currencySymbol }}{{ selectedCost.toLocaleString() }}</div>
            </div>
            <div class="budget-stat">
              <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
              <div class="stat-value">{{ selectedItems.length }} / {{ recommendations.length }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="selectedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.included') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="rec in recommendations"
                :key="rec.sku"
                :class="{ excluded: !rec.included }"
              >
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>
                  <span :class="['badge', trendClass(rec.trend)]">
                    {{ t(`trends.${rec.trend}`) }}
                  </span>
                </td>
                <td>{{ rec.currentDemand.toLocaleString() }}</td>
                <td>{{ rec.forecastedDemand.toLocaleString() }}</td>
                <td><strong>{{ rec.quantity.toLocaleString() }}</strong></td>
                <td>{{ currencySymbol }}{{ rec.unitCost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.lineCost.toLocaleString() }}</strong></td>
                <td>
                  <span :class="['badge', rec.included ? 'success' : 'danger']">
                    {{ rec.included ? t('restocking.withinBudget') : t('restocking.overBudget') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

// Trend weights bias the urgency ranking toward items whose demand is growing.
const TREND_WEIGHT = { increasing: 1.5, stable: 1.0, decreasing: 0.5 }
// Items already below their reorder point get an extra urgency boost.
const LOW_STOCK_BOOST = 1.5

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventory = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref('')

    // Join forecasts to inventory and rank by urgency score. Only items with a
    // positive demand gap and a matching inventory record can be recommended.
    const rankedItems = computed(() => {
      const inventoryBySku = new Map(inventory.value.map(item => [item.sku, item]))
      return forecasts.value
        .map(forecast => {
          const inv = inventoryBySku.get(forecast.item_sku)
          const gap = forecast.forecasted_demand - forecast.current_demand
          if (!inv || gap <= 0) return null
          const lowStock = inv.quantity_on_hand < inv.reorder_point
          // Urgency = demand gap scaled by trend direction and low-stock pressure
          const score = gap * (TREND_WEIGHT[forecast.trend] || 1.0) * (lowStock ? LOW_STOCK_BOOST : 1.0)
          return {
            sku: inv.sku,
            name: inv.name,
            trend: forecast.trend,
            currentDemand: forecast.current_demand,
            forecastedDemand: forecast.forecasted_demand,
            quantity: gap,
            unitCost: inv.unit_cost,
            lineCost: Math.round(gap * inv.unit_cost * 100) / 100,
            score
          }
        })
        .filter(Boolean)
        .sort((a, b) => b.score - a.score)
    })

    // Greedy fill: walk items in urgency order, including each one that still
    // fits in the remaining budget (skipped items don't block cheaper ones).
    const recommendations = computed(() => {
      let remaining = budget.value
      return rankedItems.value.map(item => {
        const included = item.lineCost <= remaining
        if (included) remaining -= item.lineCost
        return { ...item, included }
      })
    })

    const selectedItems = computed(() => recommendations.value.filter(r => r.included))
    const selectedCost = computed(() =>
      Math.round(selectedItems.value.reduce((sum, r) => sum + r.lineCost, 0) * 100) / 100
    )

    const totalCost = computed(() =>
      rankedItems.value.reduce((sum, r) => sum + r.lineCost, 0)
    )
    // Slider spans $0..(cost of restocking everything), rounded up to a clean step
    const sliderStep = 500
    const sliderMax = computed(() => Math.ceil(totalCost.value / sliderStep) * sliderStep)

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [demandData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = demandData
        inventory.value = inventoryData
        // Default the slider to half the full restock cost
        budget.value = Math.round(sliderMax.value / 2 / sliderStep) * sliderStep
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      try {
        submitting.value = true
        submitError.value = null
        successMessage.value = ''
        const order = await api.submitRestockOrder({
          items: selectedItems.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_cost: r.unitCost
          })),
          budget: budget.value
        })
        successMessage.value = t('restocking.orderPlaced', { orderNumber: order.order_number })
      } catch (err) {
        submitError.value = t('restocking.orderFailed') + ': ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    const trendClass = (trend) => {
      const map = { increasing: 'danger', stable: 'info', decreasing: 'success' }
      return map[trend] || 'info'
    }

    onMounted(loadData)

    return {
      t,
      translateProductName,
      currencySymbol,
      loading,
      error,
      budget,
      sliderMax,
      sliderStep,
      recommendations,
      selectedItems,
      selectedCost,
      submitting,
      submitError,
      successMessage,
      placeOrder,
      trendClass
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.budget-slider-wrap {
  flex: 1;
  min-width: 260px;
}

.budget-label {
  display: block;
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
  cursor: pointer;
}

.budget-stats {
  display: flex;
  gap: 2rem;
}

.budget-stat .stat-label {
  font-size: 0.813rem;
  color: #64748b;
}

.budget-stat .stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #dcfce7;
  border: 1px solid #16a34a;
  color: #166534;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-weight: 500;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

/* Rows that don't fit in the current budget stay visible but dimmed */
tr.excluded {
  opacity: 0.45;
}
</style>
