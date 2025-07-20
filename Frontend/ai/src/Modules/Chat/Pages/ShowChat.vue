<script setup>
import ChatContainer from '../Widgets/ChatContainer.vue';
import Input from '../Widgets/Input.vue';
import { onMounted } from 'vue';
import { useChatStore } from '../Stores/chat-store';
import { chatsApi } from '../Api/chats-api';
import { useInspiration } from '../Composables/useInspiration';
import { useRoute } from 'vue-router'

const { generateQuote } = useInspiration();
const route = useRoute()
const api = chatsApi();
const chatStore = useChatStore();

onMounted(async () => {
    chatStore.chats = await api.getChats();
    if (route.name === 'chat') {
        chatStore.chat = await api.getChat(route.params.id);
    } else {
        chatStore.chat = {};
    }
});

</script>
<template>
    <div class="flex flex-col h-screen chat-container  overflow-visible">
        <section class="flex flex-col flex-grow overflow-auto">
            <ChatContainer :chat="chatStore.chat" v-if="chatStore.chat?.name" />
            <div class="flex items-center justify-center h-screen w-full" v-else>
                <h1 class="text-3xl text-outline">
                    {{ generateQuote() }}
                </h1>
            </div>

        </section>
        <section class="sticky bottom-0 flex z-10">
            <Input />
        </section>
    </div>

</template>
