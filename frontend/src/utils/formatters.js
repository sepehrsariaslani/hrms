import { createDocumentResource } from "frappe-ui"

import dayjs from "@/utils/dayjs"
import {
	formatJalaliDate,
	formatJalaliDateShort,
	formatJalaliTime,
	getJalaliYear,
	toPersianDigits,
} from "@/utils/jalali"

const settings = createDocumentResource({
	doctype: "System Settings",
	name: "System Settings",
	auto: false,
})

export const formatCurrency = (value, currency) => {
	if (!currency) return toPersianDigits(value)

	// hack: if value contains a space, it is already formatted
	if (value?.toString().trim().includes(" ")) return toPersianDigits(value)

	const locale = settings.doc?.country == "India" ? "en-IN" : settings.doc?.language
	const currencyInput = String(currency || "").trim()
	const currencyAliases = {
		"ریال": "IRR",
		"ريال": "IRR",
		"rial": "IRR",
		"toman": "IRR",
		"تومان": "IRR",
		"تومن": "IRR",
	}
	const normalizedCurrency = currencyAliases[currencyInput]
		|| currencyAliases[currencyInput.toLowerCase()]
		|| (/^[A-Za-z]{3}$/.test(currencyInput) ? currencyInput.toUpperCase() : "")

	if (!normalizedCurrency) {
		return toPersianDigits(`${value} ${currencyInput}`.trim())
	}

	try {
		const formatter = Intl.NumberFormat(locale, {
			style: "currency",
			currency: normalizedCurrency,
			trailingZeroDisplay: "stripIfInteger",
			currencyDisplay: "narrowSymbol",
		})
		return toPersianDigits(
			formatter
				.format(value)
				// add space between the digits and symbol
				.replace(/^(\D+)/, "$1 ")
				// remove extra spaces if any (added by some browsers)
				.replace(/\s+/, " ")
		)
	} catch (_error) {
		return toPersianDigits(`${value} ${currencyInput}`.trim())
	}
}

const defaultTranslate = (text, replace) => {
	if (!replace) return text
	return text.replace(/\{(\d+)\}/g, (match, index) => {
		return replace[index] ?? match
	})
}

export const formatTimestamp = (timestamp, translate = defaultTranslate) => {
	const formattedTime = formatJalaliTime(timestamp)

	if (dayjs(timestamp).isToday()) return formattedTime
	else if (dayjs(timestamp).isYesterday())
		return `${formattedTime} ${translate("yesterday")}`
	else if (getJalaliYear(timestamp) === getJalaliYear(new Date()))
		return `${formattedTime} ${translate("on {0}", [formatJalaliDateShort(timestamp)])}`

	return `${formattedTime} ${translate("on {0}", [formatJalaliDate(timestamp)])}`
}
