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

    <article>
      Lucifer and Ariel from their perches extended far along the broad shoulders of Dr. Rachel as
      she observed her morning session.<br /><br />
      (The scene is set in a quiet office, with a single spotlight shining down on Dr. Rachel, a
      renowned stage and relationship psychiatrist and hypnotherapist. Standing at her shoulders, id
      and ego are personified by two characters: Lucifer, or Luci the devil, and Ariel, or Aries the
      Seraph Sprite) <br /><br />
      Luci: Ahahahaha! Come on, Doc. You know what sells tickets – and I'm not just talking about
      your entrancing stage shows. Your clients are eating up the drama of on stage S&M, the thrill
      of physical intimacy, and the excitement of exploring their desires. It's like a wild ride,
      and they can't get enough!
      <br /><br />
      Ariel: But, Rachel, don't you see? By catering to those desires, you're sometimes perpetuating
      the very problems you claim to help fix. The more people focus on the thrill of new
      connections, the less they prioritize real emotional intimacy and commitment.
      <br /><br />
      Dr. Rachel: (sighing) Oh, Ariel, I know what you're saying. But honestly, it's about balance.
      My clients want excitement, yes... but they also crave connection. And with non-monogamy, it
      can be a beautiful way to explore those desires in a safe and consensual manner.
      <br /><br />
      Luci: Exactly! And the more they open up, the more they learn about themselves – and each
      other. It's like peeling back layers of an onion; the drama, the passion... it all contributes
      to a deeper understanding of what they want from life.
      <br /><br />
      Ariel: But at what cost? You're often focusing on the external aspects of relationships:
      physical attraction, social status, and the thrill of conquest. Meanwhile, you're neglecting
      the true foundation of any successful partnership – trust, communication, and shared values.
      <br /><br />
      Dr. Rachel: (smiling wryly) Ah, Ariel, always so quick to remind me of the importance of heart
      over hormones. You're right, those are crucial components of any healthy relationship. But
      what about when people come to see me with issues? What about the ones who've been hurt or
      feel lost?
      <br /><br />
      Luci: (grinning mischievously) Ah, now we get to the fun part! When people let go of their
      inhibitions and explore their desires, they often discover new aspects of themselves. And with
      your guidance, Doc... well, it's like watching a flower bloom!
      <br /><br />
      Ariel: (shaking her head) That may be true, but what about when those petals get bruised? The
      trauma, the pain... that's where the real work begins. And not just on an individual level,
      either – couples and communities are affected too.
      <br /><br />
      Dr. Rachel: (nodding thoughtfully) You're right, Ariel. As a hypnotherapist, I see both sides
      of the coin. It's about finding balance between excitement and intimacy, between exploration
      and commitment.
      <br /><br />
      (Lucifer looks at Ariel with a hint of frustration.)
      <br /><br />
      Luci: Fine. Play it safe, Doc. See how that works out for you. (he disappears in a puff of
      smoke)
      <br /><br />
      (Ariel smiles warmly at Dr. Rachel.)
      <br /><br />
      Ariel: Remember, Rachel – your work is valuable because you help people grow and learn about
      themselves. Don't let the thrill of excitement overshadow the importance of true intimacy and
      commitment.
      <br /><br />
      (Dr. Rachel takes a deep breath, nodding in understanding.)
      <br /><br />
      Dr. Rachel: I'll keep that in mind, Ariel. After all, it's not just about selling tickets –
      it's about helping people find their way to genuine connection and happiness.
      <br /><br />
      (The scene is set in a cozy, upscale living room. Dr. Rachel sits comfortably between two
      couples: Michael and Mike (MM) and Emily and Sarah (FF). The atmosphere is relaxed, with
      dimmed lights and soothing background music.)
      <br /><br />
      Dr. Rachel: Good evening, everyone. I'm glad you're here to work through some challenges
      together. Can we start by each of you sharing a little about what's been going on?
      <br /><br />
      Michael: We've been having issues with trust since Mike started using that dating app again.
      <br /><br />
      Emily: Yeah, and it feels like Sarah is always getting distracted by her phone during dinner.
      <br /><br />
      Sarah: I'm just trying to unwind after work, but they get mad at me for being on my phone.
      <br /><br />
      Mike: It's not just about the phone; we've been having trust issues since we started exploring
      non-monogamy together.
      <br /><br />
      Dr. Rachel: Okay, let's take a step back and look at this from all angles. Michael and Mike,
      can you tell me more about what happens when Mike uses that dating app? And Emily and Sarah,
      how do you feel when Sarah is on her phone during dinner?
      <br /><br />
      (Each couple shares their concerns and feelings, with Dr. Rachel actively listening and asking
      clarifying questions.)
      <br /><br />
      Dr. Rachel: I see. It sounds like there are some misunderstandings and fears here. Michael and
      Mike, have you talked to each other about what you're comfortable with in terms of
      non-monogamy? And Emily and Sarah, have you communicated your boundaries around phone use
      during dinner?
      <br /><br />
      (Each couple reflects on their conversations and realizes they haven't had open discussions
      about these issues.)
      <br /><br />
      Dr. Rachel: That's a great starting point for us tonight. Let's work together to establish
      some ground rules for communication and trust.
      <br /><br />
      (The couples engage in a constructive conversation, with Dr. Rachel facilitating the
      discussion and offering guidance.)
      <br /><br />
      (The scene shifts to a crowded nightclub or stage show. Dr. Rachel is now dressed in a
      provocative outfit, with bold makeup and a confident smile.)
      <br /><br />
      Dr. Rachel: (with a sultry tone) Alright, my lovely volunteers! Tonight we're going to get
      real, get raw, and get raunchy! Who's ready to unleash their inner desires and let go of their
      inhibitions?
      <br /><br />
      (The crowd cheers as Dr. Rachel invites two volunteers on stage.)
      <br /><br />
      Dr. Rachel: Now, I want you both to take a few deep breaths, relax, and let your baser selves
      shine through.
      <br /><br />
      (She guides the first volunteer, Alex, into a trance-like state.)
      <br /><br />
      Dr. Rachel: (whispering hypnotically) Imagine yourself in a crowded nightclub... the music is
      pumping, and the energy is electric. Feel the excitement building inside you...
      <br /><br />
      (Alex starts to sway, his eyes glazed over as Dr. Rachel continues to guide him deeper into
      the trance.)
      <br /><br />
      Dr. Rachel: Now, I want you to imagine that you're surrounded by people who are eager to
      satisfy your deepest desires... they're touching you, caressing you, making you feel alive!
      <br /><br />
      (The crowd gasps as Alex's body language becomes more expressive and sensual.)
      <br /><br />
      Dr. Rachel: And remember, this is all about consent and communication... but for now, let's
      just enjoy the thrill of the moment.
      <br /><br />
      (Alex starts to moan softly as Dr. Rachel continues to guide him through the trance.)
      <br /><br />
      (The scene shifts back to the nightclub, with the crowd fully engaged in the show.)
      <br /><br />
      Dr. Rachel: (with a sly smile) Now, let's take it up a notch! Who's ready for some real fun?
      <br /><br />
      (She invites another volunteer, Jamie, onto the stage.)
      <br /><br />
      Dr. Rachel: Imagine yourself in a private room... the lights are low, and the atmosphere is
      intimate. You're about to experience something that will blow your mind!
      <br /><br />
      (Jamie starts to giggle as Dr. Rachel guides him into a trance-like state.)
      <br /><br />
      Dr. Rachel: (whispering hypnotically) Feel the excitement building inside you... the
      anticipation of pleasure... the thrill of surrender...
      <br /><br />
      (The crowd gasps again as Jamie's body language becomes more expressive and sensual.)
      <br /><br />
      Dr. Rachel: And remember, this is all about exploration and communication... but for now,
      let's just enjoy the thrill of the moment.
      <br /><br />
      (Jamie starts to moan softly as Dr. Rachel continues to guide him through the trance.)
      <br /><br />
      (The scene fades to black as the crowd cheers and whistles, with Dr. Rachel smiling
      triumphantly.)
      <br /><br />
      Dr. Rachel is working with a new couple, Alex and Maddie, who have come in for hypnosis
      therapy. They're both curious about exploring their desires and fantasies, but are hesitant to
      take the leap.
      <br /><br />
      (The scene shifts to Dr. Rachel's shoulder, where the Devil is whispering in her ear.)
      <br /><br />
      Luci: Ahahahaha! Come on, Doc! These two are just waiting for you to show them the ropes!
      They're eager to explore their kinks and desires... don't hold back!
      <br /><br />
      Dr. Rachel (thinking): Hmm, I could suggest that they try having a threesome with another
      couple... or maybe even exploring some more exotic fantasies...
      <br /><br />
      (The scene shifts to Dr. Rachel's other shoulder, where Ariel is whispering in her ear.)
      <br /><br />
      Angel: Rachel, be careful! These two are just starting out on this journey... make sure you
      guide them gently and with compassion.
      <br /><br />
      Dr. Rachel (thinking): Ah, yes... I don't want to overwhelm them or push them into something
      they're not ready for. Maybe we can start with some smaller, more manageable steps...
      <br /><br />
      (Back in the hypnosis session)
      <br /><br />
      Dr. Rachel: Okay, Alex and Maddie, let's take a deep breath together and visualize yourselves
      exploring your desires... Imagine that you've met another couple who share your kinks and are
      eager to explore them with you.
      <br /><br />
      Alex: (whispering) Oh, wow... I'm imagining us all together, sharing a romantic dinner...
      <br /><br />
      Maddie: (giggling) And then maybe we could try something more...
      <br /><br />
      Dr. Rachel: (smiling) Yes! What do you think that might be?
      <br /><br />
      Alex and Maddie: (in unison) Oh...
      <br /><br />
      (The scene shifts back to Dr. Rachel's shoulder, where the Devil is whispering in her ear.)
      <br /><br />
      Luci: Ahahahaha! Come on, Doc! You've got them right where you want them... suggest that they
      get the party going, last person in the pool has to sub in the orgy.
      <br /><br />
      Dr. Rachel (thinking): Hmm, maybe I should push the boundaries just a little bit...
      <br /><br />
      (The scene shifts to Dr. Rachel's other shoulder, where the Angel is whispering in her ear.)
      <br /><br />
      Angel: Rachel, no! Don't do it! These two are not ready for that level of complexity... guide
      them gently and with compassion!
      <br /><br />
      Dr. Rachel (thinking): Ah, yes... you're right. I don't want to overwhelm them or push them
      into something they're not ready for...
      <br /><br />
      (Back in the hypnosis session)
      <br /><br />
      Dr. Rachel: Okay, Alex and Maddie, let's take it one step at a time... maybe we can start with
      some smaller, more manageable steps towards exploring your desires together.
      <br /><br />
      Alex and Maddie: (in unison) Yes! We want to do this!
      <br /><br />
      (The scene fades to black as Dr. Rachel continues to guide the couple through their hypnosis
      session, weighing her options between the Devil's suggestion and the Angel's guidance.)
      <br /><br />
      As the patient, Alex, says this, he unknowingly activates the magical amulet, which starts to
      glow with an otherworldly energy. The room begins to feel charged with a strange, almost
      palpable excitement.
      <br /><br />
      Dr. Rachel: (startled) Ah, Alex! What have you done?
      <br /><br />
      Alex: (still in a trance-like state) I-I just wanted everyone's hormones to be as... elevated
      as mine are right now!
      <br /><br />
      (The others in the room start to feel the effects of the amulet's magic. Their bodies begin to
      respond with increased heart rates, sweating, and a general feeling of arousal.)
      <br /><br />
      Maddie: (giggling) Oh my gosh, this is amazing! I feel so... turned on!
      <br /><br />
      Mike: (laughing) Yeah, me too! It's like our hormones are on steroids or something!
      <br /><br />
      Emily: (breathlessly) Wait, what's happening? This feels really intense...
      <br /><br />
      Dr. Rachel: (trying to regain control of the situation) Okay, everyone, let's just take a deep
      breath and try to calm down. We can work through this together.
      <br /><br />
      As the others continue to feel the effects of the amulet's magic, they start to act out in
      ways that are not entirely their own. Mike begins to make suggestive comments to Emily, while
      Maddie starts to flirt shamelessly with Alex.
      <br /><br />
      Dr. Rachel: (getting increasingly flustered) Okay, okay! Let's just... try to focus on our
      therapy session, shall we?
      <br /><br />
      (The others continue to act out, with the amulet's magic causing them to become more and more
      uninhibited.)
      <br /><br />
      Alex: (still holding the amulet) I think I'm going to have a little fun, Doc!
      <br /><br />
      (He starts to make out with Maddie, while Mike and Emily get increasingly raunchy in their
      interactions.)
      <br /><br />
      Dr. Rachel: (trying to regain control of the situation) Okay, that's enough! We need to stop
      this right now!
      <br /><br />
      (The scene ends with Dr. Rachel trying to break up the amulet-induced chaos, while the others
      continue to act out under its influence.)
      <br /><br />
      As Dr. Rachel wrestles hold of the amulet, its magic is suddenly extinguished, and the
      patients stop in their tracks. They look at each other, confused and disoriented.
      <br /><br />
      Dr. Rachel: (exhausted) Ah... thank goodness...
      <br /><br />
      (Suddenly, all of the patients' eyes cross, and they fall to their knees as if drawn by an
      unseen force. They lean forward, their bodies stiffening, and then they disappear through the
      floor, leaving Dr. Rachel stunned and bewildered.)
      <br /><br />
      Dr. Rachel: (stunned) What... what just happened?
      <br /><br />
      (She looks around the room, seeing only empty space where her patients had been. She stands
      up, still trying to make sense of what has occurred.)
      <br /><br />
      As she looks down at the floor, Dr. Rachel sees a shimmering light that seems to be pulling
      her in. Without thinking, she swims and her strokes take her through the floor, following the
      slipstream left by her patients.
      <br /><br />
      (When she emerges on the other side, she finds herself in a world that is just. The air is
      filled with a sweet, musical hum, and the sky is a deep shade of purple.)
      <br /><br />
      Dr. Rachel: (awestruck) What is this place?
      <br /><br />
      (She looks around, seeing people from all walks of life living their lives in a world where
      all of their desires have been fulfilled. People are laughing, smiling, and embracing each
      other with open arms.)
      <br /><br />
      As she wanders through this parallel reality, Dr. Rachel sees that the patients' wishes have
      come true. Mike is standing on stage, leading a triumphant procession of people cheering for
      him as he holds up his latest award. Emily and Sarah are walking hand in hand, their love
      shining brightly for all to see.
      <br /><br />
      Alex and Maddie are sitting on a couch, holding hands and smiling at each other, surrounded by
      candles and flowers. They look like the perfect couple, with no signs of stress or anxiety
      between them.
      <br /><br />
      Dr. Rachel: (tearfully) Oh... they've found happiness here...
      <br /><br />
      (She realizes that the amulet's magic has created a reality where all of their deepest desires
      have been fulfilled. The patients' wishes have come true, and they are living in a world where
      love, joy, and acceptance reign supreme.)
      <br /><br />
      As Dr. Rachel looks around this new reality, she sees a world that is full of wonder, magic,
      and possibility. She realizes that the amulet's power has created a place where anything can
      happen, and where people are free to live their lives as they see fit.
      <br /><br />
      Dr. Rachel: (smiling) Maybe... just maybe... I'll join them here...
      <br /><br />
      (She takes a deep breath, feeling the excitement of this new reality coursing through her
      veins. With a newfound sense of purpose, she steps forward into this parallel world, ready to
      embark on a new journey with her patients.)
      <br /><br />
      (The scene fades to black as Dr. Rachel disappears into the unknown, leaving behind our world
      and entering the magical realm where all desires are fulfilled.)
      <br /><br />
      As soon as Dr. Rachel makes her unconscious wish, the magic of the amulet kicks in, and she
      feels a strange sensation wash over her.
      <br /><br />
      Suddenly, Emily, Mike, Maddie, Alex, and Sarah all start to change before her eyes. Their
      bodies begin to transform, taking on the perfect hourglass shape that Dr. Rachel had wished
      for.
      <br /><br />
      Their figures become more curvaceous, with narrow waists and full hips. Their breasts become
      larger and more prominent, and their skin takes on a radiant glow.
      <br /><br />
      Dr. Rachel: (stunned) Oh my... what's happening?
      <br /><br />
      (The patients look at themselves in shock and amazement, marveling at the new bodies they now
      inhabit.)
      <br /><br />
      Emily: (gasping) I feel like a supermodel!
      <br /><br />
      Mike: (whistling) Whoa, Doc! You've got some magic skills!
      <br /><br />
      Maddie: (giggling) I feel so confident and sexy!
      <br /><br />
      Alex: (awed) This is incredible!
      <br /><br />
      Sarah: (breathlessly) I never felt this way about my body before...
      <br /><br />
      Dr. Rachel: (still in shock) I...I didn't mean for this to happen...
      <br /><br />
      (The patients all start to admire themselves in the mirror, admiring their new figures and
      feeling a newfound sense of confidence and self-assurance.)
      <br /><br />
      As they gaze at their reflections, Dr. Rachel realizes that they have been transported to a
      new reality where their wishes have come true.
      <br /><br />
      In this world, everyone has the perfect body, with no flaws or imperfections. The air is
      filled with an intoxicating scent of perfume and desire, and the sky is a deep shade of blue.
      <br /><br />
      Dr. Rachel: (whispering) Welcome to our new reality...
    </article>
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
