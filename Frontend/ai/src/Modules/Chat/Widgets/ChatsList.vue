<script setup>
import Chat from '../Features/ShowChat/Chat.vue';

defineProps({
    chats: {
        type: Object,
        required: true
    }
})
</script>
<template>
    <h1 class="text-on-surface dark:text-on-surface-dark">Chats</h1>

    <Chat v-for="chat in chats" :chat :key="chat.id" v-if="chats?.length > 0">
    </Chat>
    <div v-else>
        <p class="text-on-surface flex justify-center mt-40 dark:text-on-surface-dark">No chats</p>
    </div>
</template>