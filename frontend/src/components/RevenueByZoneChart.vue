<template>
  <Bar v-if="chartData" :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from "chart.js";

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const props = defineProps({
  rows: { type: Array, default: () => [] }, // [{ pickup_zone, total_revenue }]
});

const chartData = computed(() => {
  if (!props.rows.length) return null;
  return {
    labels: props.rows.map((r) => r.pickup_zone),
    datasets: [
      {
        label: "Umsatz (\u20ac)",
        backgroundColor: "#2e5aac",
        data: props.rows.map((r) => r.total_revenue),
        borderRadius: 4,
      },
    ],
  };
});

const options = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } },
};
</script>
