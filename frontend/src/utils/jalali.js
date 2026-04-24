const PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

export const PERSIAN_MONTHS = [
	"فروردین",
	"اردیبهشت",
	"خرداد",
	"تیر",
	"مرداد",
	"شهریور",
	"مهر",
	"آبان",
	"آذر",
	"دی",
	"بهمن",
	"اسفند",
]

export const PERSIAN_WEEKDAYS = [
	"یکشنبه",
	"دوشنبه",
	"سه‌شنبه",
	"چهارشنبه",
	"پنجشنبه",
	"جمعه",
	"شنبه",
]

export const PERSIAN_WEEKDAY_SHORT = ["ی", "د", "س", "چ", "پ", "ج", "ش"]

export function toPersianDigits(value) {
	if (value === null || value === undefined) return ""
	return String(value).replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)])
}

function normalizeDate(value) {
	if (!value) return null
	if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value

	if (typeof value === "string") {
		if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
			const date = new Date(`${value}T12:00:00`)
			return Number.isNaN(date.getTime()) ? null : date
		}

		if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(value)) {
			const date = new Date(value.replace(" ", "T"))
			return Number.isNaN(date.getTime()) ? null : date
		}
	}

	const date = new Date(value)
	return Number.isNaN(date.getTime()) ? null : date
}

export function gregorianToJalali(gy, gm, gd) {
	const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
	let jy = gy <= 1600 ? 0 : 979
	gy -= gy <= 1600 ? 621 : 1600
	const gy2 = gm > 2 ? gy + 1 : gy
	let days =
		365 * gy +
		Math.floor((gy2 + 3) / 4) -
		Math.floor((gy2 + 99) / 100) +
		Math.floor((gy2 + 399) / 400) -
		80 +
		gd +
		g_d_m[gm - 1]
	jy += 33 * Math.floor(days / 12053)
	days %= 12053
	jy += 4 * Math.floor(days / 1461)
	days %= 1461
	jy += Math.floor((days - 1) / 365)
	if (days > 365) days = (days - 1) % 365
	const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30)
	const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30)
	return { year: jy, month: jm, day: jd }
}

export function jalaliToGregorian(jy, jm, jd) {
	let gy = jy <= 979 ? 621 : 1600
	jy -= jy <= 979 ? 0 : 979
	let days =
		365 * jy +
		Math.floor(jy / 33) * 8 +
		Math.floor((jy % 33 + 3) / 4) +
		78 +
		jd +
		(jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186)
	gy += 400 * Math.floor(days / 146097)
	days %= 146097
	if (days > 36524) {
		gy += 100 * Math.floor(--days / 36524)
		days %= 36524
		if (days >= 365) days++
	}
	gy += 4 * Math.floor(days / 1461)
	days %= 1461
	if (days > 365) {
		gy += Math.floor((days - 1) / 365)
		days = (days - 1) % 365
	}
	const gd_m = [
		0,
		31,
		(gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 29 : 28,
		31,
		30,
		31,
		30,
		31,
		31,
		30,
		31,
		30,
		31,
	]
	let gm = 0
	for (gm = 0; gm < 13 && days >= gd_m[gm]; gm++) days -= gd_m[gm]
	return { year: gy, month: gm, day: days + 1 }
}

export function getJalaliDaysInMonth(year, month) {
	if (month <= 6) return 31
	if (month <= 11) return 30
	return ((year - (year > 0 ? 474 : 473)) % 2820 + 474 + 38) * 682 % 2816 < 682 ? 30 : 29
}

function getJalaliParts(value) {
	const date = normalizeDate(value)
	if (!date) return null
	const jalaliDate = gregorianToJalali(
		date.getFullYear(),
		date.getMonth() + 1,
		date.getDate()
	)
	return { date, jalaliDate }
}

export function getJalaliYear(value) {
	return getJalaliParts(value)?.jalaliDate?.year
}

export function formatJalaliDate(value, options = {}) {
	const { withYear = true, withWeekday = false } = options
	const parts = getJalaliParts(value)
	if (!parts) return ""

	const { date, jalaliDate } = parts
	const weekday = withWeekday ? `${PERSIAN_WEEKDAYS[date.getDay()]}، ` : ""
	const year = withYear ? ` ${toPersianDigits(jalaliDate.year)}` : ""

	return `${weekday}${toPersianDigits(jalaliDate.day)} ${
		PERSIAN_MONTHS[jalaliDate.month - 1]
	}${year}`
}

export function formatJalaliDateShort(value) {
	return formatJalaliDate(value, { withYear: false })
}

export function formatJalaliMonthYear(value) {
	const parts = getJalaliParts(value)
	if (!parts) return ""

	const { jalaliDate } = parts
	return `${PERSIAN_MONTHS[jalaliDate.month - 1]} ${toPersianDigits(jalaliDate.year)}`
}

export function formatJalaliNumericDate(value, separator = "-") {
	const parts = getJalaliParts(value)
	if (!parts) return ""
	const { jalaliDate } = parts
	const month = String(jalaliDate.month).padStart(2, "0")
	const day = String(jalaliDate.day).padStart(2, "0")
	return toPersianDigits(`${jalaliDate.year}${separator}${month}${separator}${day}`)
}

export function formatJalaliTime(value, options = {}) {
	const { withSeconds = false } = options
	const date = normalizeDate(value)
	if (!date) return ""

	const hour = String(date.getHours()).padStart(2, "0")
	const minute = String(date.getMinutes()).padStart(2, "0")
	const second = String(date.getSeconds()).padStart(2, "0")
	const time = withSeconds ? `${hour}:${minute}:${second}` : `${hour}:${minute}`
	return toPersianDigits(time)
}

export function formatJalaliDateTime(value) {
	const date = formatJalaliNumericDate(value, "-")
	const time = formatJalaliTime(value, { withSeconds: true })
	if (!date && !time) return ""
	return `${date} ${time}`.trim()
}

export function formatGregorianDate(value) {
	const date = normalizeDate(value)
	if (!date) return ""

	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, "0")
	const day = String(date.getDate()).padStart(2, "0")
	return `${year}-${month}-${day}`
}
