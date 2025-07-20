<script setup>
import { PhAirplane, PhBuildings, PhCurrencyEur, PhGear, PhMagnifyingGlass, PhPlus } from '@phosphor-icons/vue';
import AsideButton from '../Features/Sidebar/AsideButton.vue';
import { ChatsList } from '@m/Chat';
import { useChatStore } from '@m/Chat';
import { RouterLink } from 'vue-router';
import { computed, ref } from 'vue';
import { globalStore } from '../Stores/global-store';

const chatStore = useChatStore();
const search = ref('');
const global = globalStore();

const chats = computed(() => chatStore.chats.filter(chat =>
    chat.name.toLowerCase().includes(search.value.toLowerCase())));

</script>
<template>
    <div x-data="{ showSidebar: false }" class="relative flex w-full flex-col md:flex-row">
        <!-- This allows screen readers to skip the sidebar and go directly to the main content. -->
        <a class="sr-only" href="#main-content">skip to the main content</a>

        <!-- dark overlay for when the sidebar is open on smaller screens  -->
        <div x-cloak x-show="showSidebar" class="fixed inset-0 z-10 bg-surface-dark/10 backdrop-blur-xs md:hidden"
            aria-hidden="true" x-on:click="showSidebar = false" x-transition.opacity></div>

        <nav x-cloak
            class="fixed left-0 z-20 flex h-svh w-60 shrink-0 flex-col border-r border-outline bg-surface-alt p-4 transition-transform duration-300 md:w-64 md:translate-x-0 md:relative dark:border-outline-dark dark:bg-surface-dark-alt"
            x-bind:class="showSidebar ? 'translate-x-0' : '-translate-x-60'" aria-label="sidebar navigation">
            <div class="flex justify-between items-center">
                <RouterLink to="/" class="flex h-10 items-center gap-2 text-violet-300 text-2xl uppercase font-bold">
                    {{ global.app_name }}
                </RouterLink>

                <RouterLink to="/"
                    class="flex items-center justify-center w-8 h-8 rounded-full bg-violet-500 hover:bg-violet-600 text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
                    aria-label="Add" @click="handleAddClick">
                    <PhPlus class="size-5" />
                </RouterLink>
            </div>



            <div class=" mt-5 mb-4">
                <AsideButton to="/settings" text="Settings" class="group">
                    <PhGear class="size-5 group-hover:rotate-45 transition-transform" />
                </AsideButton>
                <AsideButton to="/" text="Tour guide" class="group">
                    <PhAirplane class="size-5 group-hover:-translate-y-1 transition-transform" />
                </AsideButton>
                <AsideButton to="/" text="Business consultant" class="group ">
                    <PhBuildings
                        class="size-5 transition-all duration-300 transform group-hover:scale-75 group-hover:rotate-12 group-hover:hidden" />
                    <PhCurrencyEur
                        class="size-5  transition-all duration-300 transform scale-75 hidden group-hover:block group-hover:scale-100 group-hover:rotate-0" />
                </AsideButton>

            </div>


            <!-- search  -->
            <div class="relative my-4 flex w-full max-w-xs flex-col gap-1 text-on-surface dark:text-on-surface-dark">
                <PhMagnifyingGlass
                    class="absolute left-2 top-1/2 size-5 -translate-y-1/2 text-on-surface/50 dark:text-on-surface-dark/50" />

                <input type="search" v-model="search"
                    class="w-full border border-outline rounded-radius bg-surface px-2 py-1.5 pl-9 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-75 dark:border-outline-dark dark:bg-surface-dark/50 dark:focus-visible:outline-primary-dark"
                    name="search" aria-label="Search" placeholder="Search" />
            </div>

            <div class="flex flex-col gap-2 overflow-y-auto pb-6">
                <ChatsList :chats="chats" />
            </div>
        </nav>

        <!-- main content  -->
        <slot />

        <!-- toggle button for small screen  -->
        <button
            class="fixed right-4 top-4 z-20 rounded-full bg-primary p-4 md:hidden text-on-primary dark:bg-primary-dark dark:text-on-primary-dark"
            x-on:click="showSidebar = ! showSidebar">
            <svg x-show="showSidebar" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor"
                class="size-5" aria-hidden="true">
                <path
                    d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z" />
            </svg>
            <svg x-show="! showSidebar" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor"
                class="size-5" aria-hidden="true">
                <path
                    d="M0 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm5-1v12h9a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1zM4 2H2a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h2z" />
            </svg>
            <span class="sr-only">sidebar toggle</span>
        </button>
    </div>
</template>