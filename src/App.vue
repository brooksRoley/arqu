<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <img
      alt="Zero logo"
      class="logo"
      src="@/assets/BRLogoTransparent.png"
      width="200"
      height="200"
    />

    <div class="wrapper m-4">
      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        <RouterLink to="/elora">Mountain</RouterLink>
        <RouterLink to="/Koming">Koming</RouterLink>
        <RouterLink to="/nature">Nature</RouterLink>
        <RouterLink to="/multi">Puppy</RouterLink>
        <RouterLink to="/supplicant">Supplicant</RouterLink>
        <RouterLink to="/descent">Shapeshifter:Descent</RouterLink>
        <RouterLink to="/therapy">DevilsWager:Therapy</RouterLink>
      </nav>
      <img src="@/assets/zero.jpg" alt="Supplicant Logo" />
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}
</style>
