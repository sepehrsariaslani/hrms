<template>
	<!-- Install PWA dialog -->
	<Dialog v-model="showDialog">
		<template #body-title>
			<h2 class="text-lg font-bold">{{ __("Install Frappe HR") }} </h2>
		</template>
		<template #body-content>
			<p v-if="canUseInstallPrompt">
				{{ __("Install this app on your phone for faster access and full-screen experience.") }}
			</p>
			<p v-else-if="showSecureContextHelp">
				{{ __("To install the app, open this page with HTTPS (or localhost) and try again.") }}
			</p>
			<p v-else>
				{{ __("You can install this app from your browser menu.") }}
			</p>
		</template>
		<template #actions>
			<Button v-if="canUseInstallPrompt" variant="outline" @click="dismiss" class="py-5 w-full">
				{{ __("Later") }}
			</Button>
			<Button v-if="canUseInstallPrompt" variant="solid" @click="install" class="py-5 w-full">
				<template #prefix><FeatherIcon name="download" class="w-4" /></template>
				{{ __("Install") }}
			</Button>
			<Button v-else variant="solid" @click="dismiss" class="py-5 w-full">
				{{ __("OK") }}
			</Button>
		</template>
	</Dialog>

	<!-- iOS installation info message -->
	<Popover :show="iosInstallMessage" placement="bottom">
		<template #body>
			<div
				class="mt-[calc(100vh-15rem)] flex flex-col gap-3 mx-2 rounded py-5 bg-blue-100 drop-shadow-xl"
			>
				<div
					class="flex flex-row text-center items-center justify-between mb-1 px-3"
				>
					<span class="text-base text-gray-900 font-bold">
						{{ __("Install Frappe HR") }}
					</span>
					<span class="inline-flex items-baseline">
						<FeatherIcon
							name="x"
							class="ml-auto h-4 w-4 text-gray-700"
							@click="iosInstallMessage = false"
						/>
					</span>
				</div>
				<div class="text-xs text-gray-800 px-3">
					<span class="flex flex-col gap-2">
						<span>
							{{ __("Get the app on your iPhone for easy access & a better experience") }}
						</span>
						<span class="inline-flex items-start whitespace-nowrap">
							<span>Tap&nbsp;</span>
							<FeatherIcon name="share" class="h-4 w-4 text-blue-600" />
							<span>&nbsp;and then "Add to Home Screen"</span>
						</span>
					</span>
				</div>
			</div>
		</template>
	</Popover>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

import { Dialog, Popover, FeatherIcon } from "frappe-ui"

// Initialize deferredPrompt for use later to show browser install prompt.
const deferredPrompt = ref(null)
const showDialog = ref(false)
const iosInstallMessage = ref(false)
const INSTALL_HELP_DISMISSED_KEY = "hrms:install-help-dismissed"

const canUseInstallPrompt = computed(() => Boolean(deferredPrompt.value))
const showSecureContextHelp = computed(() => !window.isSecureContext)

const isIos = () => {
	// Detects if device is on iOS
	const userAgent = window.navigator.userAgent.toLowerCase()
	return /iphone|ipad|ipod/.test(userAgent)
}

const isMobileDevice = () => {
	const userAgent = window.navigator.userAgent.toLowerCase()
	return /android|iphone|ipad|ipod|mobile/.test(userAgent)
}

// Detects if device is in standalone mode
const isInStandaloneMode = () =>
	window.matchMedia?.("(display-mode: standalone)")?.matches
	|| ("standalone" in window.navigator && window.navigator.standalone)

function dismiss() {
	showDialog.value = false
	if (showSecureContextHelp.value) {
		sessionStorage.setItem(INSTALL_HELP_DISMISSED_KEY, "1")
	}
}

async function install() {
	if (!deferredPrompt.value) return
	deferredPrompt.value.prompt()
	try {
		await deferredPrompt.value.userChoice
	} catch (_error) {
		// Ignore prompt cancellation.
	}
	showDialog.value = false
	deferredPrompt.value = null
}

const beforeInstallPromptHandler = (e) => {
	if (!isMobileDevice() || isInStandaloneMode()) return
	// Prevent the mini-infobar from appearing on mobile
	e.preventDefault()
	// Stash the event so it can be triggered later.
	deferredPrompt.value = e
	showDialog.value = true
	// Optionally, send analytics event that PWA install promo was shown.
	console.log(`'beforeinstallprompt' event was fired.`)
}

const appInstalledHandler = () => {
	showDialog.value = false
	iosInstallMessage.value = false
	deferredPrompt.value = null
}

onMounted(() => {
	if (!isMobileDevice() || isInStandaloneMode()) return

	if (isIos()) {
		iosInstallMessage.value = true
		return
	}

	if (showSecureContextHelp.value && !sessionStorage.getItem(INSTALL_HELP_DISMISSED_KEY)) {
		showDialog.value = true
	}

	window.addEventListener("beforeinstallprompt", beforeInstallPromptHandler)
	window.addEventListener("appinstalled", appInstalledHandler)
})

onBeforeUnmount(() => {
	window.removeEventListener("beforeinstallprompt", beforeInstallPromptHandler)
	window.removeEventListener("appinstalled", appInstalledHandler)
})
</script>
