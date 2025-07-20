<script setup>
import { ref } from 'vue'

const isRecording = ref(false)
const recognizedText = ref('')
let mediaRecorder = null
let audioChunks = []

const handleClick = async () => {
    if (isRecording.value) {
        mediaRecorder.stop()
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

            audioChunks = []
            mediaRecorder = new MediaRecorder(stream)

            mediaRecorder.ondataavailable = (e) => {
                audioChunks.push(e.data)
            }

            mediaRecorder.onstop = async () => {
                const blob = new Blob(audioChunks, { type: 'audio/webm' })
                const formData = new FormData()
                formData.append('audio', blob)

                const response = await fetch('/api/transcribe', {
                    method: 'POST',
                    body: formData
                })

                const result = await response.json()
                recognizedText.value = result.text || 'No text'
                isRecording.value = false
            }

            mediaRecorder.start()
            isRecording.value = true
        } catch (err) {
            console.error('Error accessing microphone:', err)
        }
    }
}
</script>

<template>
    <button @click="handleClick"
        class="rounded-radius p-1 text-on-surface/75 hover:bg-surface-dark/10 hover:text-on-surface focus:outline-hidden focus-visible:text-on-surface focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-primary active:bg-surface-dark/5 active:-outline-offset-2 dark:text-on-surface-dark/75 dark:hover:bg-surface/10 dark:hover:text-on-surface-dark dark:focus-visible:text-on-surface-dark dark:focus-visible:outline-primary-dark dark:active:bg-surface/5"
        title="Use Voice" aria-label="Use Voice">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="size-5"
            aria-hidden="true">
            <path d="M7 4a3 3 0 0 1 6 0v6a3 3 0 1 1-6 0V4Z" />
            <path
                d="M5.5 9.643a.75.75 0 0 0-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 0 0 0 1.5h4.5a.75.75 0 0 0 0-1.5h-1.5v-1.546A6.001 6.001 0 0 0 16 10v-.357a.75.75 0 0 0-1.5 0V10a4.5 4.5 0 0 1-9 0v-.357Z" />
        </svg>
    </button>

    <p v-if="recognizedText" class="mt-2 text-sm text-on-surface">
        Распознанный текст: <strong>{{ recognizedText }}</strong>
    </p>
</template>
