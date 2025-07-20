<script setup>

import Message from '../Features/ShowChat/Message.vue';

defineProps({
    chat: {
        type: Object,
        required: true
    }
});

</script>
<template>
    <div class="flex flex-col gap-4 h-full overflow-y-auto w-full">
        <div v-for="message in chat.messages" :key="message.id">
            <Message :message="message" />
        </div>
    </div>
</template>