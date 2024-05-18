<template>
  <form id="movieform" @submit.prevent="submitForm">
    <p>
      <label for="movieform">Movie Recommendations</label>
    </p>
    <input type="text" v-model="formData.title" placeholder="Title" />
    <input type="text" v-model="formData.genre" placeholder="Genre" />
    <button type="submit" @click="submitForm">Submit</button>
  </form>
</template>

<script setup>
import { reactive } from 'vue'

const formData = reactive({
  title: '',
  genre: ''
})

const submitForm = () => {
  // Handle form submission logic here
  console.log('Form submitted with data:', formData)
  alert(formData.title + ' ' + formData.genre)
}
</script>
