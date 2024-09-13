<template>
  <div class="movie-recommender">
    <h2>Movie Recommendations</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="movie-title">Movie Title:</label>
        <input
          id="movie-title"
          v-model="formData.title"
          @input="searchMovies"
          type="text"
          placeholder="Enter a movie title"
        />
        <ul v-if="suggestions.length" class="suggestions">
          <li v-for="movie in suggestions" :key="movie.imdbID" @click="selectMovie(movie)">
            {{ movie.Title }} ({{ movie.Year }})
          </li>
        </ul>
      </div>
      <div class="form-group">
        <label for="movie-genre">Preferred Genre:</label>
        <select id="movie-genre" v-model="formData.genre">
          <option value="">Select a genre</option>
          <option value="action">Action</option>
          <option value="comedy">Comedy</option>
          <option value="drama">Drama</option>
          <option value="scifi">Sci-Fi</option>
        </select>
      </div>
      <div class="form-group">
        <label for="movie-mood">Current Mood:</label>
        <select id="movie-mood" v-model="formData.mood">
          <option value="">Select your mood</option>
          <option value="happy">Happy</option>
          <option value="sad">Sad</option>
          <option value="excited">Excited</option>
          <option value="relaxed">Relaxed</option>
        </select>
      </div>
      <button type="submit">Get Recommendation</button>
    </form>

    <div v-if="recommendation" class="recommendation">
      <h3>Recommended Movie:</h3>
      <p>{{ recommendation }}</p>
    </div>

    <div v-if="showDecisionTree" class="decision-tree">
      <h3>Decision Process:</h3>
      <ul>
        <li>
          Genre: {{ formData.genre }}
          <ul>
            <li>
              Mood: {{ formData.mood }}
              <ul>
                <li>Recommended: {{ recommendation }}</li>
              </ul>
            </li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const API_KEY = '56ccd58a'

const formData = reactive({
  title: '',
  genre: '',
  mood: ''
})

const suggestions = ref([])
const recommendation = ref('')
const showDecisionTree = ref(false)

const searchMovies = async () => {
  if (formData.title.length > 2) {
    try {
      const response = await fetch(`http://www.omdbapi.com/?apikey=${API_KEY}&s=${formData.title}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      suggestions.value = data.Search || []
    } catch (error) {
      console.error('Error fetching movie suggestions:', error)
    }
  } else {
    suggestions.value = []
  }
}
const selectMovie = (movie) => {
  formData.title = movie.Title
  suggestions.value = []
}

const getRecommendation = () => {
  // This is a simple decision tree. In a real application, this would be more complex.
  if (formData.genre === 'action') {
    if (formData.mood === 'excited') return 'Mad Max: Fury Road'
    if (formData.mood === 'relaxed') return 'Indiana Jones and the Raiders of the Lost Ark'
  } else if (formData.genre === 'comedy') {
    if (formData.mood === 'happy') return 'The Grand Budapest Hotel'
    if (formData.mood === 'sad') return 'Bridesmaids'
  } else if (formData.genre === 'drama') {
    if (formData.mood === 'sad') return 'The Shawshank Redemption'
    if (formData.mood === 'excited') return 'Whiplash'
  } else if (formData.genre === 'scifi') {
    if (formData.mood === 'relaxed') return 'Arrival'
    if (formData.mood === 'excited') return 'Inception'
  }
  return 'The Godfather' // Default recommendation
}

const submitForm = () => {
  recommendation.value = getRecommendation()
  showDecisionTree.value = true
}
</script>

<style scoped>
.movie-recommender {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: black;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
}

input,
select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  background-color: #4caf50;
  color: white;
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

.suggestions {
  list-style-type: none;
  padding: 0;
  margin: 0;
  background-color: white;
  border: 1px solid #ddd;
  border-top: none;
}

.suggestions li {
  padding: 10px;
  cursor: pointer;
}

.suggestions li:hover {
  background-color: #f1f1f1;
}

.recommendation,
.decision-tree {
  margin-top: 20px;
  padding: 15px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
