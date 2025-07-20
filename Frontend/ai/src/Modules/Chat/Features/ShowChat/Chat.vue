<script setup>
import { computed } from 'vue';

const props = defineProps({
    chat: {
        type: Object,
        required: true,
    },
});

const chatName = computed(() => {
    return props.chat.name;
});
</script>

<template>
    <RouterLink :to="{ name: 'chat', params: { id: chat.id } }"
        class="block p-2 rounded-radius border border-outline-dark bg-surface-dark hover:bg-primary-dark/10 transition">
        <div class="chat__header">
            <h3 class="text-on-surface-dark-strong font-semibold ">
                {{ chatName }}
            </h3>
        </div>
    </RouterLink>
</template>
