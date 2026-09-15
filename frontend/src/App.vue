<template>
  <div class="page">
    <header>
      <h1>Lakehouse Pipeline &ndash; Trip Analytics</h1>
      <p class="subtitle">Gold-Layer Dashboard &middot; Bronze &rarr; Silver &rarr; Gold (PySpark + Delta Lake)</p>
    </header>

    <div v-if="error" class="error-box">
      {{ error }}
      <div class="error-hint">
        Läuft die API? <code>uvicorn api.main:app --reload --port 8000</code><br />
        Wurde die Pipeline bereits ausgeführt? Siehe README &ndash; Bronze &rarr; Silver &rarr; Gold.
      </div>
    </div>

    <template v-else>
      <div class="toolbar">
        <ZoneFilter v-model="selectedZone" :zones="zones" />
        
      </div>

      <section class="kpi-row" v-if="summary">
        <KpiCard label="Fahrten gesamt" :value="summary.total_trips.toLocaleString('de-DE')" />
        <KpiCard label="Umsatz gesamt" :value="formatCurrency(summary.total_revenue)" />
        <KpiCard label="Trinkgeld gesamt" :value="formatCurrency(summary.total_tips)" />
        <KpiCard label="Ø Fahrtdauer" :value="summary.avg_trip_duration_minutes + ' min'" />
        <KpiCard label="Zeitraum" :value="`${summary.date_range_start} \u2013 ${summary.date_range_end}`" />
      </section>

      <section class="chart-grid">

        <div class="chart-card">
          <h2>Täglicher Umsatz</h2>
          <DailyRevenueChart :rows="dailyRevenue" />
        </div>
        <div class="chart-card">
          <h2>Umsatz nach Zone</h2>
          <RevenueByZoneChart :rows="revenueByZone" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import api from "./api";
import KpiCard from "./components/KpiCard.vue";
import ZoneFilter from "./components/ZoneFilter.vue";
import RevenueByZoneChart from "./components/RevenueByZoneChart.vue";
import DailyRevenueChart from "./components/DailyRevenueChart.vue";

const zones = ref([]);
const selectedZone = ref("");
const summary = ref(null);
const dailyRevenue = ref([]);
const revenueByZone = ref([]);
const error = ref("");

function formatCurrency(v) {
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(v);
}

async function loadAll() {
  error.value = "";
  try {
    const zone = selectedZone.value || undefined;
    const [s, daily, byZone] = await Promise.all([
      api.getSummary(zone),
      api.getDailyRevenue({ zone }),
      api.getRevenueByZone(),
    ]);
    summary.value = s;
    dailyRevenue.value = daily;
    revenueByZone.value = byZone;
  } catch (e) {
    error.value =
      e.response?.data?.detail || "Verbindung zur API fehlgeschlagen.";
  }
}

onMounted(async () => {
  try {
    zones.value = await api.getZones();
  } catch (e) {
    error.value = e.response?.data?.detail || "Verbindung zur API fehlgeschlagen.";
    return;
  }
  await loadAll();
});

watch(selectedZone, loadAll);
</script>

<style>
body {
  margin: 0;
  font-family: "Segoe UI", Roboto, sans-serif;
  background: #f4f6f9;
  color: #1f2937;
}
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}
header h1 {
  margin: 0;
  font-size: 26px;
  color: #1f3864;
}
.subtitle {
  color: #6b7280;
  margin-top: 4px;
}
.toolbar {
  margin: 24px 0 16px;
}
.kpi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 28px;
}
.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.chart-card {
  background: #fff;
  border: 1px solid #e2e5ea;
  border-radius: 10px;
  padding: 18px;
}
.chart-card h2 {
  font-size: 15px;
  color: #374151;
  margin: 0 0 12px;
}
.error-box {
  background: #fff5f5;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 16px 20px;
  border-radius: 10px;
  margin-top: 20px;
}
.error-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #7f1d1d;
}
code {
  background: #fee2e2;
  padding: 1px 6px;
  border-radius: 4px;
}
@media (max-width: 720px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
