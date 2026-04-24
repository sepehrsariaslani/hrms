const STORAGE_KEY = "hrms:color_mode"
const COLOR_MODES = ["system", "light", "dark"]

function normalizeMode(mode) {
	return COLOR_MODES.includes(mode) ? mode : "system"
}

function prefersDark() {
	return typeof window !== "undefined" &&
		typeof window.matchMedia === "function" &&
		window.matchMedia("(prefers-color-scheme: dark)").matches
}

function shouldUseDark(mode) {
	if (mode === "dark") return true
	if (mode === "light") return false
	return prefersDark()
}

export function getSavedColorMode() {
	if (typeof localStorage === "undefined") return "system"
	return normalizeMode(localStorage.getItem(STORAGE_KEY))
}

export function applyColorMode(mode = getSavedColorMode()) {
	if (typeof document === "undefined") return normalizeMode(mode)

	const safeMode = normalizeMode(mode)
	const root = document.documentElement
	const darkEnabled = shouldUseDark(safeMode)

	root.classList.toggle("dark", darkEnabled)
	root.setAttribute("data-color-mode", safeMode)
	root.setAttribute("data-theme", darkEnabled ? "dark" : "light")

	return safeMode
}

export function saveColorMode(mode) {
	const safeMode = normalizeMode(mode)
	if (typeof localStorage !== "undefined") {
		localStorage.setItem(STORAGE_KEY, safeMode)
	}
	return applyColorMode(safeMode)
}

export function initializeColorMode() {
	const mode = applyColorMode(getSavedColorMode())

	if (
		typeof window !== "undefined" &&
		typeof window.matchMedia === "function" &&
		!window.__hrmsColorModeListenerRegistered
	) {
		const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
		const listener = () => {
			applyColorMode(getSavedColorMode())
		}
		mediaQuery.addEventListener("change", listener)
		window.__hrmsColorModeListenerRegistered = true
	}

	return mode
}

export { COLOR_MODES }
