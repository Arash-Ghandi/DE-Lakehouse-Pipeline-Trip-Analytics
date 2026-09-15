<template>
  <div class="kpi-card">
    <div class="kpi-label">{{ label }}</div>
    <div class="kpi-value">{{ value }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
});
</script>

<style scoped>
.kpi-card {
  background: #ffffff;
  border: 1px solid #e2e5ea;
  border-radius: 10px;
  padding: 18px 20px;
  min-width: 160px;
}
.kpi-label {
  font-size: 13px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 6px;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: #1f3864;
}
</style>
