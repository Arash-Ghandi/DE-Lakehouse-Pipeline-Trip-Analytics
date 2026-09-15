<template>
  <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
    <option value="">Alle Zonen</option>
    <option v-for="zone in zones" :key="zone" :value="zone">{{ zone }}</option>
  </select>
</template>

<script setup>
defineProps({
  zones: { type: Array, required: true },
  modelValue: { type: String, default: "" },
});
defineEmits(["update:modelValue"]);
</script>

<style scoped>
select {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #d0d5dd;
  font-size: 14px;
  background: #fff;
  color: #1f2937;
}
</style>
