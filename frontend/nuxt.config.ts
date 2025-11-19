// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    compatibilityDate: '2025-07-15',
    devtools: { enabled: true },
    modules: ['@nuxt/ui'],
    css: ['~/assets/css/main.css'],
    runtimeConfig: {
        public: {
            apiBase: 'http://localhost:8000'
        }
    },
    colorMode: {
        preference: 'dark'
    },
    app: {
        head: {
            title: 'ETH LST Tracker',
            link: [
                { rel: 'icon', type: 'image/png', href: '/favicon.png' }
            ]
        }
    }
})