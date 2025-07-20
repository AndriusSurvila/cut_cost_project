<script setup>
import Sidebar from '../Widgets/Sidebar.vue'
import { RouterView } from 'vue-router'
</script>

<template>
    <Sidebar>
        <div id="main-content"
            class="h-svh w-full p-4 bg-surface dark:bg-surface-dark overflow-x-hidden overflow-y-hidden">
            <RouterView :key="$route.fullPath" />
        </div>
    </Sidebar>
</template>
