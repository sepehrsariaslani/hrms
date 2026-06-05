<template>
	<div class="bg-white rounded-lg border border-gray-100 p-1 grid grid-cols-2 gap-1">
		<router-link :to="{ name: 'ShiftAllocatorSchedulerView' }" v-slot="{ navigate }">
			<button
				type="button"
				class="rounded-md px-3 py-2 text-xs font-semibold transition"
				:class="
					activeTab === 'allocator'
						? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
						: 'bg-white text-gray-600 border border-transparent hover:bg-gray-50'
				"
				@click="navigate"
			>
				{{ __("تعیین و تکلیف") }}
			</button>
		</router-link>
		<router-link :to="{ name: 'TeamWeeklyShiftBoardView' }" v-slot="{ navigate }">
			<button
				type="button"
				class="rounded-md px-3 py-2 text-xs font-semibold transition"
				:class="
					activeTab === 'team'
						? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
						: 'bg-white text-gray-600 border border-transparent hover:bg-gray-50'
				"
				@click="navigate"
			>
				{{ __("آرایش تیم") }}
			</button>
		</router-link>
	</div>
</template>

<script setup>
import { computed, inject } from "vue"
import { useRoute } from "vue-router"

const __ = inject("$translate")
const route = useRoute()

const activeTab = computed(() => {
	const routeName = String(route.name || "")
	if (routeName === "TeamWeeklyShiftBoardView") return "team"
	return "allocator"
})
</script>
