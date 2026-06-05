class FrappePushNotification {
	constructor(projectName) {
		this.projectName = projectName
		this.webConfig = null
		this.vapidPublicKey = ""
		this.token = null
		this.initialized = false
		this.messaging = null
		this.serviceWorkerRegistration = null
		this.onMessageHandler = null
	}

	async initialize(serviceWorkerRegistration) {
		console.warn("Push notifications are not available in this environment")
	}

	async appendConfigToServiceWorkerURL(url, parameter_name = "config") {
		return url
	}

	async fetchWebConfig() {
		return {}
	}

	async fetchVapidPublicKey() {
		return ""
	}

	onMessage(callback) {}

	isNotificationEnabled() {
		return false
	}

	async enableNotification() {
		return { permission_granted: false, token: "" }
	}

	async disableNotification() {}

	async registerTokenHandler(token) {
		return false
	}

	async unregisterTokenHandler(token) {
		return false
	}
}

export default FrappePushNotification
