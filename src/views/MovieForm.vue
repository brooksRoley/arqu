<template>
  <form @submit.prevent="submitForm">
    <input type="text" v-model="formData.username" placeholder="Username" />
    <input type="password" v-model="formData.password" placeholder="Password" />
    <button type="submit" @click="submitForm">Submit</button>
  </form>
</template>

<script setup>
import { reactive } from 'vue'

const formData = reactive({
  username: '',
  password: ''
})

const submitForm = () => {
  // Handle form submission logic here
  console.log('Form submitted with data:', formData)
  alert(formData)
}
</script>
