<template>
  <div class="relative">
    <div class="relative">
      <input
        ref="inputEl"
        type="text"
        :value="displayValue"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="[inputClass, suffixPaddingClass, alignmentClass]"
        inputmode="numeric"
        dir="ltr"
      />
      <div v-if="suffix" :class="suffixClass">
        {{ suffix }}
      </div>
    </div>
    
    <!-- Persian Words Display -->
    <Transition name="fade">
      <div 
        v-if="showWords && numericValue > 0" 
        class="mt-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800"
      >
        <p class="text-sm text-amber-700 dark:text-amber-300 leading-relaxed text-right">
          {{ wordsDisplay }}
        </p>
        <p v-if="toToman" class="mt-1 text-xs text-amber-800 dark:text-amber-200 text-right">
          معادل تومان: {{ tomanDisplay }}
        </p>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: 0
  },
  placeholder: {
    type: String,
    default: 'مبلغ را وارد کنید'
  },
  suffix: {
    type: String,
    default: 'ریال'
  },
  suffixPosition: {
    type: String,
    default: 'left'
  },
  showWords: {
    type: Boolean,
    default: true
  },
  toToman: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  inputClass: {
    type: String,
    default: 'w-full px-4 py-4 pl-14 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent text-2xl font-bold'
  },
  align: {
    type: String,
    default: 'right'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const inputEl = ref(null)
const isFocused = ref(false)

const suffixClass = computed(() => {
  const sideClass = props.suffixPosition === 'right' ? 'right-3' : 'left-3'
  return `absolute ${sideClass} top-1/2 -translate-y-1/2 text-gray-400 text-sm`
})

const suffixPaddingClass = computed(() => {
  if (!props.suffix) return ''
  return props.suffixPosition === 'right' ? 'pr-14' : 'pl-14'
})

const alignmentClass = computed(() => {
  return props.align === 'left' ? 'text-left' : 'text-right'
})

// Persian digits mapping
const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const ENGLISH_DIGITS = '0123456789'

// Persian number words
const ONES = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
const TENS = ['', 'ده', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
const TEENS = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده']
const HUNDREDS = ['', 'صد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
const SCALE_NAMES = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون']

// Convert to Persian digits
function toPersianDigits(text) {
  if (!text && text !== 0) return ''
  text = String(text)
  for (let i = 0; i < 10; i++) {
    text = text.replace(new RegExp(ENGLISH_DIGITS[i], 'g'), PERSIAN_DIGITS[i])
  }
  return text
}

// Convert to English digits
function toEnglishDigits(text) {
  if (!text) return ''
  text = String(text)
  for (let i = 0; i < 10; i++) {
    text = text.replace(new RegExp(PERSIAN_DIGITS[i], 'g'), ENGLISH_DIGITS[i])
  }
  return text
}

// Format number with thousand separators in Persian
function formatWithSeparator(num) {
  if (!num && num !== 0) return ''
  const numStr = String(Math.abs(Math.floor(num)))
  let result = ''
  for (let i = 0; i < numStr.length; i++) {
    if (i > 0 && (numStr.length - i) % 3 === 0) {
      result += '٬' // Persian thousand separator
    }
    result += PERSIAN_DIGITS[parseInt(numStr[i])]
  }
  return num < 0 ? '-' + result : result
}

// Convert number to Persian words
function numberToPersianWords(num) {
  if (num === 0) return 'صفر'
  if (num < 0) return 'منفی ' + numberToPersianWords(-num)
  
  num = Math.floor(num)
  
  function threeDigitToWords(n) {
    if (n === 0) return ''
    
    const result = []
    
    // Hundreds
    if (n >= 100) {
      result.push(HUNDREDS[Math.floor(n / 100)])
      n %= 100
    }
    
    // Tens and ones
    if (n >= 20) {
      result.push(TENS[Math.floor(n / 10)])
      n %= 10
      if (n > 0) {
        result.push(ONES[n])
      }
    } else if (n >= 10) {
      result.push(TEENS[n - 10])
    } else if (n > 0) {
      result.push(ONES[n])
    }
    
    return result.join(' و ')
  }
  
  const parts = []
  let scaleIndex = 0
  
  while (num > 0 && scaleIndex < SCALE_NAMES.length) {
    const chunk = num % 1000
    if (chunk > 0) {
      let chunkWords = threeDigitToWords(chunk)
      if (scaleIndex > 0) {
        chunkWords += ' ' + SCALE_NAMES[scaleIndex]
      }
      parts.unshift(chunkWords)
    }
    num = Math.floor(num / 1000)
    scaleIndex++
  }
  
  return parts.join(' و ')
}

// Computed values
const numericValue = computed(() => {
  const val = props.modelValue
  if (!val && val !== 0) return 0
  const cleaned = toEnglishDigits(String(val)).replace(/[^0-9.-]/g, '')
  return parseFloat(cleaned) || 0
})

const displayValue = computed(() => {
  if (numericValue.value === 0 && !isFocused.value) return ''
  return formatWithSeparator(numericValue.value)
})

const wordsDisplay = computed(() => {
  if (numericValue.value === 0) return ''

  const amount = numericValue.value
  const currencyLabel = 'ریال'

  if (amount === 0) return 'صفر ' + currencyLabel

  return numberToPersianWords(amount) + ' ' + currencyLabel
})

const tomanDisplay = computed(() => {
  if (!props.toToman || numericValue.value <= 0) return ''
  const tomanValue = Math.floor(numericValue.value / 10)
  return `${formatWithSeparator(tomanValue)} تومان`
})

// Methods
function handleInput(e) {
  // Get the raw input value
  let rawValue = e.target.value
  
  // Convert to English digits and remove non-numeric characters
  rawValue = toEnglishDigits(rawValue).replace(/[^0-9]/g, '')
  
  // Parse as number
  const numValue = parseInt(rawValue) || 0
  
  emit('update:modelValue', numValue)
  emit('change', numValue)
}

function handleFocus() {
  isFocused.value = true
}

function handleBlur() {
  isFocused.value = false
}

// Expose focus method
defineExpose({
  focus: () => inputEl.value?.focus()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
