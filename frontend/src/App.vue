<template>
	<ion-app>
		<ion-router-outlet id="main-content" :animated="false" />
		<Toasts />

		<InstallPrompt />
		<AppOnboarding />
	</ion-app>
</template>

<script setup>
import { onMounted } from "vue"
import { IonApp, IonRouterOutlet } from "@ionic/vue"

import { Toasts } from "frappe-ui"

import InstallPrompt from "@/components/InstallPrompt.vue"
import AppOnboarding from "@/components/AppOnboarding.vue"
import { showNotification } from "@/utils/pushNotifications"

onMounted(() => {
	window?.frappePushNotification?.onMessage((payload) => {
		showNotification(payload)
	})
})
</script>
