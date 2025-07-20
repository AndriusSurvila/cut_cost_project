// useInspiration.js
import { ref } from 'vue'

const quotes = [
  "Believe you can and you're halfway there.",
  "Your limitation—it's only your imagination.",
  'Push yourself, because no one else is going to do it for you.',
  'Great things never come from comfort zones.',
  'Dream it. Wish it. Do it.',
  "Success doesn't just find you. You have to go out and get it.",
  "The harder you work for something, the greater you'll feel when you achieve it.",
  "Don't stop when you're tired. Stop when you're done.",
  'Wake up with determination. Go to bed with satisfaction.',
  'Do something today that your future self will thank you for.',
]

export function useInspiration() {
  function generateQuote() {
    const randomIndex = Math.floor(Math.random() * quotes.length)
    return quotes[randomIndex]
  }

  return {
    generateQuote,
  }
}
