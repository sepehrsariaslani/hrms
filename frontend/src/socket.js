import { io } from "socket.io-client"
import { socketio_port } from "../../../../sites/common_site_config.json"

import { getCachedListResource } from "frappe-ui/src/resources/listResource"
import { getCachedResource } from "frappe-ui/src/resources/resources"

let lastNotificationToneAt = 0
let lastSystemNotificationAt = 0

function playNotificationTone() {
	const now = Date.now()
	if (now - lastNotificationToneAt < 1500) return
	lastNotificationToneAt = now

	try {
		const AudioContextClass = window.AudioContext || window.webkitAudioContext
		if (!AudioContextClass) return

		const context = new AudioContextClass()
		const gainNode = context.createGain()
		gainNode.gain.value = 0.06
		gainNode.connect(context.destination)

		const playTone = (frequency, offsetSeconds, durationSeconds) => {
			const oscillator = context.createOscillator()
			oscillator.type = "sine"
			oscillator.frequency.value = frequency
			oscillator.connect(gainNode)
			oscillator.start(context.currentTime + offsetSeconds)
			oscillator.stop(context.currentTime + offsetSeconds + durationSeconds)
		}

		playTone(880, 0, 0.12)
		playTone(660, 0.14, 0.16)

		setTimeout(() => {
			context.close()
		}, 600)
	} catch (_error) {
		// Ignore audio errors (e.g., browser autoplay restrictions).
	}
}

function showSystemNotification() {
	if (typeof Notification === "undefined") return
	if (Notification.permission !== "granted") return
	if (document.visibilityState === "visible") return

	const now = Date.now()
	if (now - lastSystemNotificationAt < 4000) return
	lastSystemNotificationAt = now

	try {
		const notification = new Notification("Frappe HR", {
			body: "یک یادآور یا اعلان جدید دریافت شد.",
			icon: "/assets/hrms/manifest/favicon-196.png",
			tag: "hrms-live-notification",
		})

		setTimeout(() => {
			notification.close()
		}, 6000)
	} catch (_error) {
		// Ignore browser notification errors.
	}
}

export function initSocket() {
	let host = window.location.hostname
	let siteName = window.site_name
	let port = window.location.port ? `:${socketio_port}` : ""
	let protocol = port ? "http" : "https"
	let url = `${protocol}://${host}${port}/${siteName}`
	let socket = io(url, {
		withCredentials: true,
		reconnectionAttempts: 5,
	})

	socket.on("hrms:refetch_resource", (data) => {
		if (data.cache_key === "hrms:notifications") {
			playNotificationTone()
			showSystemNotification()
		}

		if (data.cache_key) {
			let resource =
				getCachedResource(data.cache_key) ||
				getCachedListResource(data.cache_key)

			if (resource) {
				resource.reload()
			}
		}
	})

	return socket
}
