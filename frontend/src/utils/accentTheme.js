const THEME_CONFIG_KEY = "hrms:accent_theme_config"
const LEGACY_COLOR_KEY = "hrms:accent_color"
const DEFAULT_ACCENT_COLOR = "#dc2626"
const DEFAULT_THEME_CONFIG = {
	primary: DEFAULT_ACCENT_COLOR,
	mode: "auto",
	scheme: "analogous",
	secondary: "#2563eb",
	tertiary: "#0ea5e9",
}
const ACCENT_MODES = ["auto", "manual"]
const COLOR_SCHEMES = [
	"analogous",
	"complementary",
	"split-complementary",
	"triadic",
	"tetradic",
	"monochromatic",
]

const SHADE_MIX = {
	50: { with: "#ffffff", amount: 0.92 },
	100: { with: "#ffffff", amount: 0.84 },
	200: { with: "#ffffff", amount: 0.7 },
	300: { with: "#ffffff", amount: 0.56 },
	400: { with: "#ffffff", amount: 0.38 },
	500: null,
	600: { with: "#000000", amount: 0.12 },
	700: { with: "#000000", amount: 0.24 },
	800: { with: "#000000", amount: 0.38 },
	900: { with: "#000000", amount: 0.52 },
}

function clampChannel(value) {
	return Math.max(0, Math.min(255, Math.round(value)))
}

function clampPercent(value) {
	return Math.max(0, Math.min(100, Number(value)))
}

function normalizeHexColor(value) {
	if (!value) return null
	const raw = String(value).trim()
	const hex = raw.startsWith("#") ? raw.slice(1) : raw
	if (!/^[0-9a-fA-F]{3}$|^[0-9a-fA-F]{6}$/.test(hex)) return null
	if (hex.length === 3) {
		return `#${hex
			.split("")
			.map((char) => `${char}${char}`)
			.join("")
			.toLowerCase()}`
	}
	return `#${hex.toLowerCase()}`
}

function hexToRgb(hex) {
	const safe = normalizeHexColor(hex)
	if (!safe) return null
	const value = safe.slice(1)
	return {
		r: parseInt(value.slice(0, 2), 16),
		g: parseInt(value.slice(2, 4), 16),
		b: parseInt(value.slice(4, 6), 16),
	}
}

function rgbToHex(rgb) {
	const toHex = (channel) => clampChannel(channel).toString(16).padStart(2, "0")
	return `#${toHex(rgb.r)}${toHex(rgb.g)}${toHex(rgb.b)}`
}

function rgbToHsl({ r, g, b }) {
	const rn = r / 255
	const gn = g / 255
	const bn = b / 255
	const max = Math.max(rn, gn, bn)
	const min = Math.min(rn, gn, bn)
	const delta = max - min

	let h = 0
	if (delta !== 0) {
		if (max === rn) {
			h = ((gn - bn) / delta) % 6
		} else if (max === gn) {
			h = (bn - rn) / delta + 2
		} else {
			h = (rn - gn) / delta + 4
		}
	}

	h = Math.round((h * 60 + 360) % 360)
	const l = (max + min) / 2
	const s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1))

	return {
		h,
		s: clampPercent(s * 100),
		l: clampPercent(l * 100),
	}
}

function hslToRgb({ h, s, l }) {
	const hue = ((Number(h) % 360) + 360) % 360
	const sat = clampPercent(s) / 100
	const light = clampPercent(l) / 100
	const chroma = (1 - Math.abs(2 * light - 1)) * sat
	const x = chroma * (1 - Math.abs(((hue / 60) % 2) - 1))
	const m = light - chroma / 2

	let r1 = 0
	let g1 = 0
	let b1 = 0

	if (hue < 60) {
		r1 = chroma
		g1 = x
	} else if (hue < 120) {
		r1 = x
		g1 = chroma
	} else if (hue < 180) {
		g1 = chroma
		b1 = x
	} else if (hue < 240) {
		g1 = x
		b1 = chroma
	} else if (hue < 300) {
		r1 = x
		b1 = chroma
	} else {
		r1 = chroma
		b1 = x
	}

	return {
		r: clampChannel((r1 + m) * 255),
		g: clampChannel((g1 + m) * 255),
		b: clampChannel((b1 + m) * 255),
	}
}

function shiftHue(hue, delta) {
	return (Number(hue) + Number(delta) + 360) % 360
}

function buildHexFromHsl(h, s, l) {
	return rgbToHex(hslToRgb({ h, s, l }))
}

function resolveMode(mode) {
	return ACCENT_MODES.includes(mode) ? mode : DEFAULT_THEME_CONFIG.mode
}

function resolveScheme(scheme) {
	return COLOR_SCHEMES.includes(scheme) ? scheme : DEFAULT_THEME_CONFIG.scheme
}

function computeAutoSecondaryAndTertiary(primaryColor, scheme) {
	const primaryRgb = hexToRgb(primaryColor)
	if (!primaryRgb) {
		return {
			secondary: DEFAULT_THEME_CONFIG.secondary,
			tertiary: DEFAULT_THEME_CONFIG.tertiary,
		}
	}

	const primaryHsl = rgbToHsl(primaryRgb)
	const saturation = primaryHsl.s
	const lightness = primaryHsl.l

	let secondaryHue = shiftHue(primaryHsl.h, 30)
	let tertiaryHue = shiftHue(primaryHsl.h, -30)
	let secondarySat = saturation
	let tertiarySat = saturation
	let secondaryLight = lightness
	let tertiaryLight = lightness

	switch (scheme) {
		case "complementary":
			secondaryHue = shiftHue(primaryHsl.h, 180)
			tertiaryHue = shiftHue(primaryHsl.h, 150)
			secondarySat = clampPercent(saturation - 6)
			tertiarySat = clampPercent(saturation - 10)
			secondaryLight = clampPercent(lightness + 4)
			tertiaryLight = clampPercent(lightness - 4)
			break
		case "split-complementary":
			secondaryHue = shiftHue(primaryHsl.h, 150)
			tertiaryHue = shiftHue(primaryHsl.h, -150)
			secondarySat = clampPercent(saturation - 3)
			tertiarySat = clampPercent(saturation - 3)
			secondaryLight = clampPercent(lightness + 3)
			tertiaryLight = clampPercent(lightness - 3)
			break
		case "triadic":
			secondaryHue = shiftHue(primaryHsl.h, 120)
			tertiaryHue = shiftHue(primaryHsl.h, 240)
			secondarySat = clampPercent(saturation)
			tertiarySat = clampPercent(saturation)
			secondaryLight = clampPercent(lightness + 2)
			tertiaryLight = clampPercent(lightness + 2)
			break
		case "tetradic":
			secondaryHue = shiftHue(primaryHsl.h, 90)
			tertiaryHue = shiftHue(primaryHsl.h, 180)
			secondarySat = clampPercent(saturation - 2)
			tertiarySat = clampPercent(saturation - 6)
			secondaryLight = clampPercent(lightness + 2)
			tertiaryLight = clampPercent(lightness + 4)
			break
		case "monochromatic":
			secondaryHue = primaryHsl.h
			tertiaryHue = primaryHsl.h
			secondarySat = clampPercent(saturation - 12)
			tertiarySat = clampPercent(saturation + 8)
			secondaryLight = clampPercent(lightness + 18)
			tertiaryLight = clampPercent(lightness - 14)
			break
		case "analogous":
		default:
			secondaryHue = shiftHue(primaryHsl.h, 28)
			tertiaryHue = shiftHue(primaryHsl.h, -28)
			secondarySat = clampPercent(saturation + 2)
			tertiarySat = clampPercent(saturation - 4)
			secondaryLight = clampPercent(lightness + 2)
			tertiaryLight = clampPercent(lightness + 6)
			break
	}

	return {
		secondary: buildHexFromHsl(
			secondaryHue,
			Math.max(20, secondarySat),
			Math.max(24, secondaryLight)
		),
		tertiary: buildHexFromHsl(
			tertiaryHue,
			Math.max(20, tertiarySat),
			Math.max(24, tertiaryLight)
		),
	}
}

function mixColors(baseHex, mixHex, amount) {
	const base = hexToRgb(baseHex)
	const mix = hexToRgb(mixHex)
	if (!base || !mix) return baseHex
	const ratio = Math.max(0, Math.min(1, amount))
	return rgbToHex({
		r: base.r + (mix.r - base.r) * ratio,
		g: base.g + (mix.g - base.g) * ratio,
		b: base.b + (mix.b - base.b) * ratio,
	})
}

function buildPalette(baseColor) {
	const palette = {}
	for (const shade of Object.keys(SHADE_MIX)) {
		const rule = SHADE_MIX[shade]
		palette[shade] = rule
			? mixColors(baseColor, rule.with, rule.amount)
			: baseColor
	}
	return palette
}

function setCssVariables(baseColor) {
	const inputConfig =
		typeof baseColor === "string" ? { primary: baseColor } : baseColor || DEFAULT_THEME_CONFIG
	const config = normalizeThemeConfig(inputConfig)
	const autoColors = computeAutoSecondaryAndTertiary(config.primary, config.scheme)
	const secondaryColor =
		config.mode === "manual"
			? normalizeHexColor(config.secondary) || autoColors.secondary
			: autoColors.secondary
	const tertiaryColor =
		config.mode === "manual"
			? normalizeHexColor(config.tertiary) || autoColors.tertiary
			: autoColors.tertiary

	if (typeof document === "undefined") return
	const root = document.documentElement
	const palette = buildPalette(config.primary)
	const secondaryPalette = buildPalette(secondaryColor)
	const tertiaryPalette = buildPalette(tertiaryColor)
	const rgb = hexToRgb(config.primary)
	const secondaryRgb = hexToRgb(secondaryColor)
	const tertiaryRgb = hexToRgb(tertiaryColor)

	if (!rgb || !secondaryRgb || !tertiaryRgb) return

	for (const [shade, color] of Object.entries(palette)) {
		root.style.setProperty(`--hrms-accent-${shade}`, color)
	}

	for (const [shade, color] of Object.entries(secondaryPalette)) {
		root.style.setProperty(`--hrms-accent-secondary-${shade}`, color)
	}

	for (const [shade, color] of Object.entries(tertiaryPalette)) {
		root.style.setProperty(`--hrms-accent-tertiary-${shade}`, color)
	}

	root.style.setProperty("--hrms-accent-rgb", `${rgb.r}, ${rgb.g}, ${rgb.b}`)
	root.style.setProperty(
		"--hrms-accent-secondary-rgb",
		`${secondaryRgb.r}, ${secondaryRgb.g}, ${secondaryRgb.b}`
	)
	root.style.setProperty(
		"--hrms-accent-tertiary-rgb",
		`${tertiaryRgb.r}, ${tertiaryRgb.g}, ${tertiaryRgb.b}`
	)
	root.style.setProperty(
		"--hrms-hero-gradient",
		`linear-gradient(135deg, ${palette[700]} 0%, ${secondaryPalette[600]} 52%, ${tertiaryPalette[600]} 100%)`
	)
	root.style.setProperty("--ion-color-primary", palette[500])
	root.style.setProperty("--ion-color-primary-rgb", `${rgb.r}, ${rgb.g}, ${rgb.b}`)
	root.style.setProperty("--ion-color-primary-shade", palette[700])
	root.style.setProperty("--ion-color-primary-tint", palette[300])
	root.style.setProperty("--ion-color-secondary", secondaryPalette[500])
	root.style.setProperty(
		"--ion-color-secondary-rgb",
		`${secondaryRgb.r}, ${secondaryRgb.g}, ${secondaryRgb.b}`
	)
	root.style.setProperty("--ion-color-secondary-shade", secondaryPalette[700])
	root.style.setProperty("--ion-color-secondary-tint", secondaryPalette[300])
	root.style.setProperty("--ion-color-tertiary", tertiaryPalette[500])
	root.style.setProperty(
		"--ion-color-tertiary-rgb",
		`${tertiaryRgb.r}, ${tertiaryRgb.g}, ${tertiaryRgb.b}`
	)
	root.style.setProperty("--ion-color-tertiary-shade", tertiaryPalette[700])
	root.style.setProperty("--ion-color-tertiary-tint", tertiaryPalette[300])
	return {
		...config,
		secondary: secondaryColor,
		tertiary: tertiaryColor,
	}
}

function normalizeThemeConfig(input = {}) {
	const primary = normalizeHexColor(input.primary) || DEFAULT_THEME_CONFIG.primary
	const mode = resolveMode(input.mode)
	const scheme = resolveScheme(input.scheme)
	const secondary = normalizeHexColor(input.secondary) || DEFAULT_THEME_CONFIG.secondary
	const tertiary = normalizeHexColor(input.tertiary) || DEFAULT_THEME_CONFIG.tertiary
	return {
		primary,
		mode,
		scheme,
		secondary,
		tertiary,
	}
}

export function getSavedThemeConfig() {
	if (typeof localStorage === "undefined") return { ...DEFAULT_THEME_CONFIG }

	const rawConfig = localStorage.getItem(THEME_CONFIG_KEY)
	if (rawConfig) {
		try {
			const parsed = JSON.parse(rawConfig)
			return normalizeThemeConfig(parsed)
		} catch (error) {
			// fallback to legacy key if JSON parsing fails
		}
	}

	const legacyColor = normalizeHexColor(localStorage.getItem(LEGACY_COLOR_KEY))
	if (legacyColor) {
		return normalizeThemeConfig({ primary: legacyColor })
	}

	return { ...DEFAULT_THEME_CONFIG }
}

function emitThemeChange(config) {
	if (typeof window === "undefined" || typeof window.dispatchEvent !== "function") return
	window.dispatchEvent(
		new CustomEvent("hrms:accent-theme-change", {
			detail: config,
		})
	)
}

export function applyAccentTheme(themeConfig) {
	const normalized = normalizeThemeConfig(themeConfig || getSavedThemeConfig())
	const applied = setCssVariables(normalized)
	if (applied) emitThemeChange(applied)
	return applied || normalized
}

export function initializeAccentTheme() {
	return applyAccentTheme(getSavedThemeConfig())
}

export function saveAccentThemeConfig(themeConfig) {
	const normalized = normalizeThemeConfig(themeConfig)
	const applied = applyAccentTheme(normalized)
	if (typeof localStorage !== "undefined") {
		localStorage.setItem(THEME_CONFIG_KEY, JSON.stringify(applied))
		localStorage.setItem(LEGACY_COLOR_KEY, applied.primary)
	}
	return applied
}

export function resetAccentTheme() {
	if (typeof localStorage !== "undefined") {
		localStorage.removeItem(THEME_CONFIG_KEY)
		localStorage.removeItem(LEGACY_COLOR_KEY)
	}
	return applyAccentTheme(DEFAULT_THEME_CONFIG)
}

export function getAutoSchemePreview(primary, scheme) {
	const safePrimary = normalizeHexColor(primary) || DEFAULT_ACCENT_COLOR
	const safeScheme = resolveScheme(scheme)
	return computeAutoSecondaryAndTertiary(safePrimary, safeScheme)
}

export function getSavedAccentColor() {
	return getSavedThemeConfig().primary
}

export function applyAccentColor(color) {
	return applyAccentTheme({ primary: color }).primary
}

export function saveAccentColor(color) {
	const current = getSavedThemeConfig()
	return saveAccentThemeConfig({ ...current, primary: color }).primary
}

export function resetAccentColor() {
	return resetAccentTheme().primary
}

export { DEFAULT_ACCENT_COLOR, DEFAULT_THEME_CONFIG, ACCENT_MODES, COLOR_SCHEMES }
