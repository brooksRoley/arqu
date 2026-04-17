<script setup lang="ts">
// Static text-only page. No state, no animations.
</script>

<template>
  <main class="about">
    <header class="about-head">
      <h1>About ChannelZero</h1>
    </header>

    <section class="block">
      <p>
        ChannelZero is an Enfractionation platform — a small set of tools that
        work together to make a person more receptive to suggestion. It combines
        brainwave entrainment (binaural and isochronic audio), trance induction
        through visual fixation and pacing, and reading-assisted suggestion via a
        phrase-paced text reader.
      </p>
      <p>
        Each tool can be used on its own. Used together, they layer: a steady
        binaural carrier, a slow visual rhythm, and language delivered at the
        edge of attention.
      </p>
    </section>

    <section class="block">
      <h2>How to use this site</h2>
      <ul>
        <li>Start with <RouterLink to="/learn">Learn</RouterLink> to understand the concepts before opening a session.</li>
        <li>Use <RouterLink to="/sessions">Sessions</RouterLink> to access the tools directly when you know what you want.</li>
        <li>Take the poll on the <RouterLink to="/">home page</RouterLink> for a recommended session matched to your current state.</li>
      </ul>
    </section>

    <section class="block disclaimer">
      <h2>This is not medical advice</h2>
      <p>
        ChannelZero is not a medical device and does not diagnose, treat, or cure
        any condition. Do not use binaural audio, strobing visuals, or trance
        sessions if you have epilepsy, a seizure disorder, or any condition that
        could be aggravated by altered states. Do not use while driving or
        operating machinery. If something here makes you feel unwell, stop.
      </p>
    </section>
  </main>
</template>

<style scoped>
.about {
  min-height: 100vh;
  background: #1a1a1a;
  color: #e2e8f0;
  padding: 3rem 1.25rem 4rem;
  max-width: 720px;
  margin: 0 auto;
  font-family: inherit;
  line-height: 1.65;
}

.about-head {
  margin-bottom: 2rem;
}

.about-head h1 {
  font-size: 2rem;
  font-weight: 500;
  margin: 0;
  letter-spacing: 0.01em;
}

.block {
  margin-bottom: 2.25rem;
}

.block h2 {
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #64748b;
  margin: 0 0 0.75rem;
}

.block p {
  margin: 0 0 1rem;
  color: #cbd5e1;
  font-size: 0.95rem;
}

.block p:last-child {
  margin-bottom: 0;
}

.block ul {
  margin: 0;
  padding-left: 1.1rem;
  color: #cbd5e1;
  font-size: 0.95rem;
}

.block li {
  margin-bottom: 0.5rem;
}

.block li:last-child {
  margin-bottom: 0;
}

.block a {
  color: #a5b4fc;
  text-decoration: none;
  border-bottom: 1px solid rgba(165, 180, 252, 0.3);
  transition: color 0.15s ease, border-color 0.15s ease;
}

.block a:hover {
  color: #c7d2fe;
  border-bottom-color: rgba(199, 210, 254, 0.6);
}

.disclaimer p {
  color: #94a3b8;
  font-size: 0.875rem;
}
</style>
