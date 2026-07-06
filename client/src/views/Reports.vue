<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterlyPerformance.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterlyPerformance.table.quarter') }}</th>
                <th>{{ t('reports.quarterlyPerformance.table.totalOrders') }}</th>
                <th>{{ t('reports.quarterlyPerformance.table.totalRevenue') }}</th>
                <th>{{ t('reports.quarterlyPerformance.table.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterlyPerformance.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ currencySymbol }}{{ q.total_revenue.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ q.avg_order_value.toLocaleString() }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="currencySymbol + month.revenue.toLocaleString()"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.table.month') }}</th>
                <th>{{ t('reports.monthOverMonth.table.orders') }}</th>
                <th>{{ t('reports.monthOverMonth.table.revenue') }}</th>
                <th>{{ t('reports.monthOverMonth.table.change') }}</th>
                <th>{{ t('reports.monthOverMonth.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, idx) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ currencySymbol }}{{ month.revenue.toLocaleString() }}</td>
                <td>
                  <span v-if="idx > 0" :class="getChangeClass(month.revenue, monthlyData[idx - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[idx - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="idx > 0" :class="getChangeClass(month.revenue, monthlyData[idx - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[idx - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalRevenueYTD') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalRevenue.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ avgMonthlyRevenue.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrdersYTD') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()

        const [fetchedQuarterly, fetchedMonthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])

        quarterlyData.value = fetchedQuarterly
        monthlyData.value = fetchedMonthly
      } catch (err) {
        error.value = 'Failed to load reports: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    // Derived summary stats, computed once from the loaded data
    const totalRevenue = computed(() => {
      return monthlyData.value.reduce((sum, month) => sum + month.revenue, 0)
    })

    const avgMonthlyRevenue = computed(() => {
      return monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    })

    const totalOrders = computed(() => {
      return monthlyData.value.reduce((sum, month) => sum + month.order_count, 0)
    })

    const bestQuarter = computed(() => {
      if (quarterlyData.value.length === 0) return t('reports.notAvailable')
      const topQuarter = quarterlyData.value.reduce((leader, q) => (
        q.total_revenue > leader.total_revenue ? q : leader
      ), quarterlyData.value[0])
      return topQuarter.quarter
    })

    const maxMonthlyRevenue = computed(() => {
      if (monthlyData.value.length === 0) return 0
      return Math.max(...monthlyData.value.map(month => month.revenue))
    })

    const getBarHeight = (revenue) => {
      if (maxMonthlyRevenue.value === 0) return 0
      return (revenue / maxMonthlyRevenue.value) * 200
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      const symbol = currencySymbol.value
      if (change > 0) return `+${symbol}${change.toLocaleString()}`
      if (change < 0) return `-${symbol}${Math.abs(change).toLocaleString()}`
      return `${symbol}0`
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return t('reports.notAvailable')
      const rate = ((current - previous) / previous) * 100
      const sign = rate > 0 ? '+' : ''
      return `${sign}${rate.toFixed(1)}%`
    }

    // Convert a YYYY-MM string to a localized month/year label
    const formatMonth = (monthStr) => {
      if (!monthStr || typeof monthStr !== 'string') return t('reports.notAvailable')
      const parts = monthStr.split('-')
      if (parts.length !== 2) return t('reports.notAvailable')

      const year = parseInt(parts[0], 10)
      const monthIndex = parseInt(parts[1], 10) - 1
      const date = new Date(year, monthIndex, 1)

      if (isNaN(date.getTime())) return t('reports.notAvailable')

      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short' })
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      currencySymbol,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      getChangeValue,
      getChangeClass,
      getGrowthRate,
      formatMonth
    }
  }
}
</script>

<style scoped>
.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #2563eb, #3b82f6);
}

.bar-label {
  margin-top: 1.5rem;
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.positive-change {
  color: #16a34a;
  font-weight: 600;
}

.negative-change {
  color: #dc2626;
  font-weight: 600;
}
</style>
