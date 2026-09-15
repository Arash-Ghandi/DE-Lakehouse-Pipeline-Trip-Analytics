<template>
  <Line v-if="chartData" :data="chartData" :options="options" />
</template>

<script setup>
import { computed } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
} from "chart.js";


ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale);

const props = defineProps({
  rows: { type: Array, default: () => [] }, // [{ trip_date, total_fare_revenue }]
});

const chartData = computed(() => {
  if (!props.rows.length) return null;

  // aggregate across zones per day, in case "all zones" is selected
  const byDate = {};
  for (const r of props.rows) {
    const d = r.trip_date.slice(0, 10);
    byDate[d] = (byDate[d] || 0) + r.total_fare_revenue;
  }
  const labels = Object.keys(byDate).sort();

  return {
    labels,
    datasets: [
      {
        label: "T\u00e4glicher Umsatz (\u20ac)",
        borderColor: "#2e5aac",
        backgroundColor: "rgba(46,90,172,0.15)",
        data: labels.map((d) => Math.round(byDate[d] * 100) / 100),
        tension: 0.25,
        fill: true,
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
