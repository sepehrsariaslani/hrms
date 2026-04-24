<template>
	<BaseLayout :pageTitle="__('Settings')">
		<template #body>
			<div class="w-full max-w-5xl mx-auto flex flex-col gap-5 mt-7 mb-7 p-4">
						<div class="flex flex-col bg-white rounded">
							<Switch
								size="md"
								:label="__('Enable Push Notifications')"
								:class="description ? 'p-2' : ''"
								:model-value="pushNotificationState"
								:disabled="disablePushSetting"
								:description="description"
								@update:model-value="togglePushNotifications"
							/>
						</div>

						<div class="flex flex-col gap-3 rounded bg-white p-4">
							<div class="text-sm font-bold text-gray-900">
								{{ __("Display Theme") }}
							</div>
							<div class="text-xs text-gray-500">
								{{ __("Choose how HRMS appears for your account.") }}
							</div>
							<div class="grid grid-cols-3 gap-2">
								<Button
									v-for="option in colorModeOptions"
									:key="option.value"
									:variant="colorMode === option.value ? 'solid' : 'outline'"
									class="py-3 text-sm"
									@click="setDisplayMode(option.value)"
								>
									{{ option.label }}
								</Button>
							</div>
						</div>

						<div v-if="hasThemeAccess" class="flex flex-col gap-4 rounded bg-white p-4">
							<div class="flex items-start justify-between gap-3">
								<div>
									<div class="text-sm font-bold text-gray-900">
										{{ __("HR Color Theme") }}
									</div>
									<div class="mt-1 text-xs text-gray-500">
										{{ __("Choose primary/secondary/tertiary accents. Auto mode uses color wheel harmony like Adobe color themes.") }}
									</div>
								</div>
								<div class="flex items-center gap-2">
									<div class="h-7 w-7 rounded-full border border-gray-200" :style="{ backgroundColor: accentColorDraft }"></div>
									<div class="h-7 w-7 rounded-full border border-gray-200" :style="{ backgroundColor: effectiveSecondaryColor }"></div>
									<div class="h-7 w-7 rounded-full border border-gray-200" :style="{ backgroundColor: effectiveTertiaryColor }"></div>
								</div>
							</div>

							<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
								<div class="rounded-lg border border-gray-100 p-3">
									<div class="text-xs text-gray-600 mb-2">{{ __("Mode") }}</div>
									<div class="grid grid-cols-2 gap-2">
										<Button
											:variant="themeMode === 'auto' ? 'solid' : 'outline'"
											class="py-3 text-sm"
											:disabled="!hasThemeAccess"
											@click="themeMode = 'auto'"
										>
											{{ __("Auto") }}
										</Button>
										<Button
											:variant="themeMode === 'manual' ? 'solid' : 'outline'"
											class="py-3 text-sm"
											:disabled="!hasThemeAccess"
											@click="themeMode = 'manual'"
										>
											{{ __("Manual") }}
										</Button>
									</div>
								</div>

								<div class="rounded-lg border border-gray-100 p-3">
									<div class="text-xs text-gray-600 mb-2">{{ __("Color Harmony") }}</div>
									<select
										v-model="themeScheme"
										class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
										:disabled="!hasThemeAccess || themeMode !== 'auto'"
									>
										<option v-for="option in schemeOptions" :key="option.value" :value="option.value">
											{{ option.label }}
										</option>
									</select>
								</div>
							</div>

							<div class="grid grid-cols-1 gap-3 md:grid-cols-3">
								<div class="rounded-lg border border-gray-100 p-3">
									<div class="text-xs text-gray-600 mb-2">{{ __("Primary") }}</div>
									<div class="flex items-center gap-2">
										<input
											v-model="accentColorDraft"
											type="color"
											class="h-10 w-12 cursor-pointer rounded border border-gray-200 bg-white p-1"
											:disabled="!hasThemeAccess"
										/>
										<Input v-model="accentColorDraft" :disabled="!hasThemeAccess" placeholder="#dc2626" />
									</div>
								</div>

								<div class="rounded-lg border border-gray-100 p-3">
									<div class="text-xs text-gray-600 mb-2">
										{{ __("Secondary") }}
										<span v-if="themeMode === 'auto'" class="text-[10px] text-gray-400">({{ __("Auto") }})</span>
									</div>
									<div class="flex items-center gap-2">
										<input
											v-model="secondaryColorDraft"
											type="color"
											class="h-10 w-12 cursor-pointer rounded border border-gray-200 bg-white p-1"
											:disabled="!hasThemeAccess || themeMode !== 'manual'"
										/>
										<Input v-model="secondaryColorDraft" :disabled="!hasThemeAccess || themeMode !== 'manual'" placeholder="#2563eb" />
									</div>
								</div>

								<div class="rounded-lg border border-gray-100 p-3">
									<div class="text-xs text-gray-600 mb-2">
										{{ __("Tertiary") }}
										<span v-if="themeMode === 'auto'" class="text-[10px] text-gray-400">({{ __("Auto") }})</span>
									</div>
									<div class="flex items-center gap-2">
										<input
											v-model="tertiaryColorDraft"
											type="color"
											class="h-10 w-12 cursor-pointer rounded border border-gray-200 bg-white p-1"
											:disabled="!hasThemeAccess || themeMode !== 'manual'"
										/>
										<Input v-model="tertiaryColorDraft" :disabled="!hasThemeAccess || themeMode !== 'manual'" placeholder="#06b6d4" />
									</div>
								</div>
							</div>

							<div class="flex flex-wrap gap-2">
								<button
									v-for="preset in themePresets"
									:key="preset.value"
									type="button"
									class="h-7 w-7 rounded-full border border-white shadow ring-1 ring-gray-200"
									:style="{ backgroundColor: preset.value }"
									:title="preset.label"
									@click="setPresetColor(preset.value)"
									:disabled="!hasThemeAccess"
								/>
							</div>


							<div class="flex items-center gap-2">
								<Button
									variant="solid"
									class="py-4"
									:disabled="!hasThemeAccess || !canSaveTheme"
									@click="saveThemeColor"
								>
									{{ __("Save Theme") }}
								</Button>
								<Button
									variant="outline"
									class="py-4"
									:disabled="!hasThemeAccess"
									@click="restoreDefaultThemeColor"
								>
									{{ __("Reset") }}
								</Button>
							</div>
						</div>

						<!-- Loading Indicator -->
						<div
							v-if="isLoading"
							class="flex -mt-2 items-center justify-center gap-2"
						>
							<LoadingIndicator class="w-3 h-3 text-gray-800" />
							<span class="text-gray-900 text-sm">
								{{ pushNotificationState ? __("Disabling Push Notifications...") : __("Enabling Push Notifications...") }}
							</span>
						</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { Switch, Input, toast, LoadingIndicator } from "frappe-ui"

import { computed, inject, ref, watch } from "vue"

import BaseLayout from "@/components/BaseLayout.vue"
import { arePushNotificationsEnabled } from "@/data/notifications"
import {
	DEFAULT_THEME_CONFIG,
	applyAccentTheme,
	getAutoSchemePreview,
	getSavedThemeConfig,
	resetAccentTheme,
	saveAccentThemeConfig,
} from "@/utils/accentTheme"
import { getSavedColorMode, saveColorMode } from "@/utils/colorMode"

const __ = inject("$translate")
const user = inject("$user")
const pushNotificationState = ref(
	window.frappePushNotification?.isNotificationEnabled()
)
const isLoading = ref(false)
const colorMode = ref(getSavedColorMode())
const initialTheme = getSavedThemeConfig()
const accentColorDraft = ref(initialTheme.primary)
const secondaryColorDraft = ref(initialTheme.secondary)
const tertiaryColorDraft = ref(initialTheme.tertiary)
const themeMode = ref(initialTheme.mode)
const themeScheme = ref(initialTheme.scheme)

const themePresets = [
	{ label: "Red", value: "#dc2626" },
	{ label: "Orange", value: "#e79913" },
	{ label: "Blue", value: "#2563eb" },
	{ label: "Green", value: "#0f766e" },
]
const THEME_ACCESS_ROLES = ["System Manager"]

const hasThemeAccess = computed(() => {
	const roles = user.data?.roles || []
	return THEME_ACCESS_ROLES.some((role) => roles.includes(role))
})

const HEX_COLOR_RE = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/
const schemeOptions = [
	{ value: "analogous", label: __("Analogous") },
	{ value: "complementary", label: __("Complementary") },
	{ value: "split-complementary", label: __("Split Complementary") },
	{ value: "triadic", label: __("Triadic") },
	{ value: "tetradic", label: __("Tetradic") },
	{ value: "monochromatic", label: __("Monochromatic") },
]

const autoPair = computed(() => getAutoSchemePreview(accentColorDraft.value, themeScheme.value))
const effectiveSecondaryColor = computed(() =>
	themeMode.value === "manual" ? secondaryColorDraft.value : autoPair.value.secondary
)
const effectiveTertiaryColor = computed(() =>
	themeMode.value === "manual" ? tertiaryColorDraft.value : autoPair.value.tertiary
)

const canSaveTheme = computed(() => {
	if (!HEX_COLOR_RE.test(String(accentColorDraft.value || "").trim())) return false
	if (themeMode.value !== "manual") return true
	return (
		HEX_COLOR_RE.test(String(secondaryColorDraft.value || "").trim()) &&
		HEX_COLOR_RE.test(String(tertiaryColorDraft.value || "").trim())
	)
})

const disablePushSetting = computed(() => {
	return (
		!(
			window.frappe?.boot.push_relay_server_url &&
			arePushNotificationsEnabled.data
		) || isLoading.value
	)
})

const description = computed(() => {
	return !(
		window.frappe?.boot.push_relay_server_url &&
		arePushNotificationsEnabled.data
	)
		? __("Push notifications have been disabled on your site")
		: ""
})

const colorModeOptions = [
	{ value: "system", label: __("System") },
	{ value: "light", label: __("Light") },
	{ value: "dark", label: __("Dark") },
]

const draftThemeConfig = computed(() => ({
	primary: accentColorDraft.value,
	mode: themeMode.value,
	scheme: themeScheme.value,
	secondary: secondaryColorDraft.value,
	tertiary: tertiaryColorDraft.value,
}))

watch(
	draftThemeConfig,
	(value) => {
		if (!hasThemeAccess.value) return
		if (!canSaveTheme.value) return
		applyAccentTheme(value)
	},
	{ deep: true }
)

const setPresetColor = (color) => {
	if (!hasThemeAccess.value) return
	accentColorDraft.value = color
}

const setDisplayMode = (mode) => {
	colorMode.value = saveColorMode(mode)
}

const saveThemeColor = () => {
	if (!hasThemeAccess.value || !canSaveTheme.value) return
	const saved = saveAccentThemeConfig(draftThemeConfig.value)
	accentColorDraft.value = saved.primary
	secondaryColorDraft.value = saved.secondary
	tertiaryColorDraft.value = saved.tertiary
	themeMode.value = saved.mode
	themeScheme.value = saved.scheme
	toast({
		title: __("Success"),
		text: __("HRMS theme colors updated"),
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

const restoreDefaultThemeColor = () => {
	if (!hasThemeAccess.value) return
	const restored = resetAccentTheme()
	accentColorDraft.value = restored.primary || DEFAULT_THEME_CONFIG.primary
	secondaryColorDraft.value = restored.secondary || DEFAULT_THEME_CONFIG.secondary
	tertiaryColorDraft.value = restored.tertiary || DEFAULT_THEME_CONFIG.tertiary
	themeMode.value = restored.mode || DEFAULT_THEME_CONFIG.mode
	themeScheme.value = restored.scheme || DEFAULT_THEME_CONFIG.scheme
	toast({
		title: __("Success"),
		text: __("Theme reset to default"),
		icon: "check-circle",
		position: "bottom-center",
		iconClasses: "text-green-500",
	})
}

const togglePushNotifications = (newValue) => {
	if (newValue) {
		enablePushNotifications()
	} else {
		isLoading.value = true
		window.frappePushNotification
			.disableNotification()
			.then((data) => {
				pushNotificationState.value = false // Disable the switch
				// TODO: add commonfied toast util for success and error messages
				toast({
					title: __("Success"),
					text: __("Push notifications disabled"),
					icon: "check-circle",
					position: "bottom-center",
					iconClasses: "text-green-500",
				})
			})
			.catch((error) => {
				toast({
					title: __("Error"),
					text: __(error.message),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
			})
			.finally(() => {
				isLoading.value = false
			})
	}
}

const enablePushNotifications = () => {
	isLoading.value = true

	window.frappePushNotification
		.enableNotification()
		.then((data) => {
			if (data.permission_granted) {
				pushNotificationState.value = true
			} else {
				toast({
					title: __("Error"),
					text: __("Push Notification permission denied"),
					icon: "alert-circle",
					position: "bottom-center",
					iconClasses: "text-red-500",
				})
				pushNotificationState.value = false
			}
		})
		.catch((error) => {
			toast({
				title: __("Error"),
				text: __(error.message),
				icon: "alert-circle",
				position: "bottom-center",
				iconClasses: "text-red-500",
			})
			pushNotificationState.value = false
		})
		.finally(() => {
			isLoading.value = false
		})
}
</script>
