import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api",
});

export default {
  getZones() {
    return client.get("/zones").then((r) => r.data);
  },
  getSummary(zone) {
    return client.get("/summary", { params: { zone } }).then((r) => r.data);
  },
  getDailyRevenue(params) {
    return client.get("/revenue/daily", { params }).then((r) => r.data);
  },
  getRevenueByZone() {
    return client.get("/revenue/by-zone").then((r) => r.data);
  },
};
