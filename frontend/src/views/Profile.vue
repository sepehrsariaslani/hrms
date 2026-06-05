<template>
	<BaseLayout :pageTitle="__('Profile')">
		<template #body>
			<div class="w-full max-w-5xl mx-auto flex flex-col items-center mt-7 mb-7 p-4">
				<img
					v-if="displayedProfileImage"
					class="h-24 w-24 rounded-full object-cover"
					:src="displayedProfileImage"
					:alt="user.data?.first_name || user.data?.full_name"
				/>
				<div
					v-else
					class="flex items-center justify-center bg-gray-200 uppercase text-gray-600 h-24 w-24 rounded-full object-cover"
				>
					{{ user.data?.first_name?.[0] || user.data?.full_name?.[0] || "?" }}
				</div>

				<div class="flex flex-col gap-1.5 items-center mt-2 mb-5">
					<span v-if="employee?.data" class="text-lg font-bold text-gray-900">{{
						employee.data.employee_name
					}}</span>
					<span v-if="employee?.data" class="font-normal text-sm text-gray-500">{{
						employee.data.designation
					}}</span>
				</div>

				<div class="w-full bg-white rounded p-4">
					<div class="text-base font-semibold text-gray-900">ویرایش پروفایل</div>
					<div class="mt-4 flex flex-col gap-5">
						<div class="flex items-center gap-4">
							<img
								v-if="displayedProfileImage"
								class="h-16 w-16 rounded-full object-cover"
								:src="displayedProfileImage"
								:alt="user.data?.first_name || user.data?.full_name"
							/>
							<div
								v-else
								class="flex items-center justify-center bg-gray-200 uppercase text-gray-600 h-16 w-16 rounded-full object-cover"
							>
								{{ user.data?.first_name?.[0] || user.data?.full_name?.[0] || "?" }}
							</div>

							<div class="flex flex-col gap-2 grow">
								<div class="text-sm font-medium text-gray-700">عکس پروفایل/کاور کارمند</div>
								<div class="flex flex-row gap-2 flex-wrap">
									<Button variant="outline" class="!py-2" @click="openProfileImagePicker">
										انتخاب عکس
									</Button>
									<Button
										v-if="selectedProfileImage"
										variant="ghost"
										class="!py-2"
										@click="clearSelectedProfileImage"
									>
										حذف انتخاب
									</Button>
								</div>
								<div class="text-xs text-gray-500">فرمت JPG/PNG و حداکثر ۵ مگابایت</div>
								<input
									ref="profileImageInput"
									type="file"
									class="hidden"
									accept="image/*"
									@change="handleProfileImageChange"
								/>
							</div>
						</div>

						<div class="border-t pt-4">
							<div class="text-sm font-semibold text-gray-800 mb-3">جزئیات شخصی</div>
							<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
								<div class="flex flex-col gap-1">
									<label class="text-xs text-gray-600">موبایل</label>
									<input
										v-model="employeeForm.cell_number"
										type="text"
										inputmode="numeric"
										maxlength="20"
										class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
										@input="employeeForm.cell_number = normalizeDigits(employeeForm.cell_number)"
									/>
								</div>
								<div class="flex flex-col gap-1">
									<label class="text-xs text-gray-600">ایمیل شخصی</label>
									<input
										v-model="employeeForm.personal_email"
										type="email"
										class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
									/>
								</div>
								<div class="flex flex-col gap-1">
									<label class="text-xs text-gray-600">گروه خونی</label>
									<input
										v-model="employeeForm.blood_group"
										type="text"
										maxlength="10"
										class="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
									/>
								</div>
							</div>
						</div>

						<div class="border-t pt-4">
							<div class="flex items-center justify-between mb-3">
								<div class="text-sm font-semibold text-gray-800">حساب‌های بانکی (Bank Account)</div>
								<Button variant="outline" class="!py-2" @click="addBankAccountRow">
									افزودن حساب جدید
								</Button>
							</div>

							<div v-if="bankAccounts.length" class="flex flex-col gap-3">
								<div
									v-for="(account, index) in bankAccounts"
									:key="account._rowKey"
									class="rounded border border-gray-200 p-3"
								>
									<div class="flex items-center justify-between mb-2">
										<div class="text-xs text-gray-600">حساب {{ index + 1 }}</div>
										<div class="flex gap-2">
											<label class="text-xs flex items-center gap-1">
												<input
													type="checkbox"
													:checked="account.is_default"
													@change="setDefaultBankAccount(index)"
												/>
												پیش‌فرض
											</label>
											<Button
												variant="ghost"
												class="!py-1 !px-2 !text-rose-600"
												@click="removeBankAccountRow(index)"
											>
												حذف
											</Button>
										</div>
									</div>

									<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">عنوان حساب</label>
											<input
												v-model="account.account_name"
												type="text"
												class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm text-gray-800"
												placeholder="مثال: حساب حقوق"
											/>
										</div>
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">نام بانک</label>
											<Link
												v-model="account.bank"
												doctype="Bank"
												placeholder="انتخاب بانک"
											/>
										</div>
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">شماره حساب</label>
											<input
												v-model="account.bank_account_no"
												type="text"
												maxlength="30"
												inputmode="numeric"
												class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm text-gray-800"
												@input="
													account.bank_account_no = normalizeDigits(account.bank_account_no)
												"
											/>
										</div>
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">شماره کارت</label>
											<input
												v-model="account.card_number"
												type="text"
												maxlength="19"
												inputmode="numeric"
												class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm text-gray-800"
												@input="account.card_number = normalizeDigits(account.card_number)"
											/>
										</div>
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">شماره شبا</label>
											<input
												v-model="account.iban"
												type="text"
												maxlength="34"
												class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm text-gray-800"
												@input="account.iban = normalizeIban(account.iban)"
											/>
										</div>
										<div class="flex flex-col gap-1">
											<label class="text-xs text-gray-600">کد شعبه</label>
											<input
												v-model="account.branch_code"
												type="text"
												maxlength="20"
												class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm text-gray-800"
											/>
										</div>
									</div>
								</div>
							</div>
							<div v-else class="text-sm text-gray-500">
								فعلاً حساب بانکی ثبت نشده است.
							</div>
						</div>

						<Button
							class="w-full shadow py-4"
							:loading="isSavingProfile"
							:disabled="isSavingProfile || !isProfileDirty"
							@click="saveProfileChanges"
						>
							ذخیره تغییرات
						</Button>
					</div>
				</div>

				<div class="flex flex-col gap-5 my-4 w-full">
					<div class="flex flex-col bg-white rounded">
						<div
							v-for="link in profileLinks"
							:key="link.title"
							class="flex flex-row cursor-pointer flex-start p-4 items-center justify-between border-b"
							@click="openInfoModal(link)"
						>
							<div class="flex flex-row items-center gap-3 grow">
								<FeatherIcon :name="link.icon" class="h-5 w-5 text-gray-500" />
								<div class="text-base font-normal text-gray-800">{{ link.title }}</div>
							</div>
							<FeatherIcon name="chevron-right" class="h-5 w-5 text-gray-500" />
						</div>
					</div>
				</div>

				<Button
					@click="logout"
					variant="outline"
					theme="red"
					class="w-full shadow py-4 mt-5"
				>
					<template #prefix>
						<FeatherIcon name="log-out" class="w-4" />
					</template>
					{{ __("Log Out") }}
				</Button>
			</div>

			<ion-modal
				ref="modal"
				:is-open="isInfoModalOpen"
				@didDismiss="closeInfoModal"
				:initial-breakpoint="1"
				:breakpoints="[0, 1]"
			>
				<ProfileInfoModal
					v-if="selectedItem"
					:title="selectedItem.title"
					:data="selectedItemData"
				/>
			</ion-modal>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { IonModal } from "@ionic/vue"
import { FeatherIcon, createDocumentResource, createResource, toast } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"
import Link from "@/components/Link.vue"
import ProfileInfoModal from "@/components/ProfileInfoModal.vue"
import { FileAttachment } from "@/composables"
import { employees } from "@/data/employees"
import { showErrorAlert } from "@/utils/dialogs"
import { formatCurrency } from "@/utils/formatters"

const DOCTYPE = "Employee"
const MAX_PROFILE_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

const socket = inject("$socket")
const session = inject("$session")
const user = inject("$user")
const employee = inject("$employee")
const __ = inject("$translate")

const isInfoModalOpen = ref(false)
const selectedItem = ref(null)
const profileImageInput = ref(null)
const selectedProfileImage = ref(null)
const selectedProfileImagePreview = ref("")
const isSavingProfile = ref(false)

const employeeForm = ref({
	cell_number: "",
	personal_email: "",
	blood_group: "",
})
const initialEmployeeForm = ref({ ...employeeForm.value })

const bankAccounts = ref([])
const initialBankAccountsSnapshot = ref("")

const employeeEditableFields = ["cell_number", "personal_email", "blood_group"]

const profileLinks = [
	{
		icon: "user",
		title: __("Employee Details"),
		fields: ["employee_name", "employee_number", "gender", "date_of_birth", "date_of_joining", "blood_group"],
	},
	{
		icon: "file",
		title: __("Company Information"),
		fields: ["company", "department", "designation", "branch", "grade", "reports_to", "employment_type"],
	},
	{
		icon: "book",
		title: __("Contact Information"),
		fields: ["cell_number", "personal_email", "company_email", "preferred_email"],
	},
	{
		icon: "dollar-sign",
		title: __("Salary Information"),
		fields: ["ctc", "payroll_cost_center", "salary_mode", "bank_name", "bank_ac_no", "iban"],
	},
]

const employeeDoc = createDocumentResource({
	doctype: DOCTYPE,
	name: employee.data?.name,
	fields: "*",
	auto: false,
	transform: (data) => {
		data.ctc = formatCurrency(data.ctc, data.salary_currency)
		return data
	},
})

const employeeDocType = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: DOCTYPE },
	auto: true,
})

const bankAccountListResource = createResource({
	url: "frappe.client.get_list",
	auto: false,
})

const bankAccountInsertResource = createResource({
	url: "frappe.client.insert",
	auto: false,
})

const bankAccountSetValueResource = createResource({
	url: "frappe.client.set_value",
	auto: false,
})

const bankAccountDeleteResource = createResource({
	url: "frappe.client.delete",
	auto: false,
})

const displayedProfileImage = computed(
	() => selectedProfileImagePreview.value || employeeDoc.doc?.image || user.data?.user_image || ""
)

const selectedItemData = computed(() => {
	if (!selectedItem.value?.fields?.length || !employeeDoc.doc) return []
	return selectedItem.value.fields.map((fieldname) => {
		const fieldMeta = (employeeDocType.data || []).find((row) => row.fieldname === fieldname)
		return {
			fieldname,
			value: employeeDoc.doc?.[fieldname] ?? "",
			label: __(fieldMeta?.label, null, "Employee"),
			fieldtype: fieldMeta?.fieldtype || "Data",
		}
	})
})

const normalizeDigits = (value) => {
	const map = {
		"۰": "0",
		"۱": "1",
		"۲": "2",
		"۳": "3",
		"۴": "4",
		"۵": "5",
		"۶": "6",
		"۷": "7",
		"۸": "8",
		"۹": "9",
		"٠": "0",
		"١": "1",
		"٢": "2",
		"٣": "3",
		"٤": "4",
		"٥": "5",
		"٦": "6",
		"٧": "7",
		"٨": "8",
		"٩": "9",
	}
	return String(value || "").replace(/[۰-۹٠-٩]/g, (digit) => map[digit] || digit)
}

const normalizeIban = (value) => normalizeDigits(value).replace(/\s+/g, "").toUpperCase()

const openInfoModal = (request) => {
	selectedItem.value = request
	isInfoModalOpen.value = true
}

const closeInfoModal = () => {
	isInfoModalOpen.value = false
	selectedItem.value = null
}

const openProfileImagePicker = () => {
	profileImageInput.value?.click()
}

const clearSelectedProfileImage = () => {
	if (selectedProfileImagePreview.value?.startsWith("blob:")) {
		URL.revokeObjectURL(selectedProfileImagePreview.value)
	}
	selectedProfileImage.value = null
	selectedProfileImagePreview.value = ""
	if (profileImageInput.value) profileImageInput.value.value = ""
}

const handleProfileImageChange = (event) => {
	const selectedFile = event?.target?.files?.[0]
	if (!selectedFile) return

	if (!selectedFile.type?.startsWith("image/")) {
		showErrorAlert("لطفاً فقط فایل تصویر انتخاب کنید.")
		clearSelectedProfileImage()
		return
	}

	if (selectedFile.size > MAX_PROFILE_IMAGE_SIZE_BYTES) {
		showErrorAlert("حجم عکس نباید بیشتر از ۵ مگابایت باشد.")
		clearSelectedProfileImage()
		return
	}

	if (selectedProfileImagePreview.value?.startsWith("blob:")) {
		URL.revokeObjectURL(selectedProfileImagePreview.value)
	}

	selectedProfileImage.value = selectedFile
	selectedProfileImagePreview.value = URL.createObjectURL(selectedFile)
}

const assignEmployeeFormFromDoc = () => {
	const doc = employeeDoc.doc || {}
	const snapshot = {
		cell_number: normalizeDigits(doc.cell_number || "").slice(0, 20),
		personal_email: doc.personal_email || "",
		blood_group: doc.blood_group || "",
	}
	employeeForm.value = { ...snapshot }
	initialEmployeeForm.value = { ...snapshot }
}

const toBankAccountRow = (doc) => ({
	_rowKey: doc.name || `new-${Math.random().toString(36).slice(2)}`,
	name: doc.name || "",
	account_name: doc.account_name || "",
	bank: doc.bank || "",
	bank_account_no: normalizeDigits(doc.bank_account_no || "").slice(0, 30),
	card_number: normalizeDigits(doc.card_number || "").slice(0, 19),
	iban: normalizeIban(doc.iban || "").slice(0, 34),
	branch_code: doc.branch_code || "",
	is_default: Boolean(doc.is_default),
	isNew: !doc.name,
	isDeleted: false,
})

const bankSnapshot = () => {
	return JSON.stringify(
		bankAccounts.value
			.filter((item) => !item.isDeleted)
			.map((item) => ({
				name: item.name || "",
				account_name: (item.account_name || "").trim(),
				bank: (item.bank || "").trim(),
				bank_account_no: normalizeDigits(item.bank_account_no || "").replace(/\D/g, ""),
				card_number: normalizeDigits(item.card_number || "").replace(/\D/g, "").slice(0, 19),
				iban: normalizeIban(item.iban || ""),
				branch_code: (item.branch_code || "").trim(),
				is_default: Boolean(item.is_default),
			}))
			.sort((left, right) => String(left.name).localeCompare(String(right.name)))
	)
}

const isEmployeeFormDirty = computed(() => {
	return employeeEditableFields.some((key) => {
		const currentValue = normalizeDigits(employeeForm.value[key] || "")
		const initialValue = normalizeDigits(initialEmployeeForm.value[key] || "")
		return currentValue !== initialValue
	})
})

const isBankAccountsDirty = computed(() => bankSnapshot() !== initialBankAccountsSnapshot.value)
const isProfileDirty = computed(
	() => isEmployeeFormDirty.value || isBankAccountsDirty.value || Boolean(selectedProfileImage.value)
)

const addBankAccountRow = () => {
	bankAccounts.value.push(
		toBankAccountRow({
			name: "",
			account_name: "",
			bank: "",
			bank_account_no: "",
			card_number: "",
			iban: "",
			branch_code: "",
			is_default: bankAccounts.value.filter((item) => !item.isDeleted).length === 0 ? 1 : 0,
		})
	)
}

const removeBankAccountRow = (index) => {
	const row = bankAccounts.value[index]
	if (!row) return
	if (row.name) {
		row.isDeleted = true
		row.is_default = false
	} else {
		bankAccounts.value.splice(index, 1)
	}
}

const setDefaultBankAccount = (index) => {
	bankAccounts.value.forEach((row, rowIndex) => {
		if (row.isDeleted) return
		row.is_default = rowIndex === index
	})
}

const getEmployeeUpdatePayload = () => ({
	cell_number: normalizeDigits(employeeForm.value.cell_number || "").slice(0, 20),
	personal_email: (employeeForm.value.personal_email || "").trim(),
	blood_group: (employeeForm.value.blood_group || "").trim(),
})

const validateBankAccounts = () => {
	const activeRows = bankAccounts.value.filter((row) => !row.isDeleted)
	for (const row of activeRows) {
		const title = (row.account_name || "").trim()
		const bank = (row.bank || "").trim()
		const accountNumber = normalizeDigits(row.bank_account_no || "").replace(/\D/g, "")
		const cardNumber = normalizeDigits(row.card_number || "").replace(/\D/g, "")
		if (!(title && bank && accountNumber)) {
			showErrorAlert("برای هر حساب بانکی، عنوان حساب، نام بانک و شماره حساب الزامی است.")
			return false
		}
		if (cardNumber && cardNumber.length !== 16) {
			showErrorAlert("شماره کارت باید ۱۶ رقم باشد.")
			return false
		}
	}
	return true
}

const saveBankAccounts = async () => {
	for (const row of bankAccounts.value) {
		if (row.isDeleted && row.name) {
			await bankAccountDeleteResource.submit({ doctype: "Bank Account", name: row.name })
			continue
		}

		if (row.isDeleted) continue

		const payload = {
			account_name: (row.account_name || "").trim(),
			bank: (row.bank || "").trim(),
			bank_account_no: normalizeDigits(row.bank_account_no || "").replace(/\D/g, "").slice(0, 30),
			card_number: normalizeDigits(row.card_number || "").replace(/\D/g, "").slice(0, 19),
			iban: normalizeIban(row.iban || "").slice(0, 34),
			branch_code: (row.branch_code || "").trim(),
			party_type: "Employee",
			party: employee.data?.name,
			is_company_account: 0,
			is_default: row.is_default ? 1 : 0,
		}

		if (!row.name) {
			const inserted = await bankAccountInsertResource.submit({
				doc: { doctype: "Bank Account", ...payload },
			})
			row.name = inserted?.name || ""
			row.isNew = false
		} else {
			await bankAccountSetValueResource.submit({
				doctype: "Bank Account",
				name: row.name,
				fieldname: payload,
			})
		}
	}
}

const loadEmployeeBankAccounts = async () => {
	if (!employee.data?.name) return
	const rows = await bankAccountListResource.fetch({
		doctype: "Bank Account",
		fields: [
			"name",
			"account_name",
			"bank",
			"bank_account_no",
			"card_number",
			"iban",
			"branch_code",
			"is_default",
		],
		filters: { party_type: "Employee", party: employee.data.name, is_company_account: 0 },
		order_by: "is_default desc, modified desc",
		limit_page_length: 100,
	})
	bankAccounts.value = (rows || []).map((row) => toBankAccountRow(row))
	initialBankAccountsSnapshot.value = bankSnapshot()
}

const saveProfileChanges = async () => {
	if (isSavingProfile.value || !isProfileDirty.value) return
	if (!validateBankAccounts()) return
	isSavingProfile.value = true

	try {
		let hasAnyUpdate = false

		if (isEmployeeFormDirty.value) {
			await employeeDoc.setValue.submit(getEmployeeUpdatePayload())
			hasAnyUpdate = true
		}

		if (isBankAccountsDirty.value) {
			await saveBankAccounts()
			hasAnyUpdate = true
		}

		if (selectedProfileImage.value) {
			const uploaded = await new FileAttachment(selectedProfileImage.value).upload(
				"Employee",
				employee.data?.name,
				"image"
			)
			const uploadedUrl = uploaded?.file_url || ""
			if (uploadedUrl) {
				await employeeDoc.setValue.submit({ image: uploadedUrl })
				await createResource({
					url: "frappe.client.set_value",
					auto: false,
				}).submit({
					doctype: "User",
					name: user.data?.name,
					fieldname: "user_image",
					value: uploadedUrl,
				})
			}
			clearSelectedProfileImage()
			hasAnyUpdate = true
		}

		if (!hasAnyUpdate) return

		await Promise.allSettled([
			employeeDoc.reload(),
			user.reload(),
			employee.reload(),
			employees.reload(),
			loadEmployeeBankAccounts(),
		])
		assignEmployeeFormFromDoc()
		initialBankAccountsSnapshot.value = bankSnapshot()

		toast({
			title: __("Success"),
			text: __("Profile updated successfully."),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	} catch (error) {
		console.error("Failed to update profile information", error)
		showErrorAlert(error?.messages?.[0] || __("Unable to save profile information."))
	} finally {
		isSavingProfile.value = false
	}
}

const logout = async () => {
	try {
		await session.logout.submit()
	} catch (error) {
		console.error("An error occurred while attempting to log out!", error)
		showErrorAlert("An error occurred while attempting to log out!")
	}
}

onMounted(() => {
	socket.emit("doctype_subscribe", DOCTYPE)
	socket.on("list_update", (data) => {
		if (data.doctype === DOCTYPE && data.name === employee.data?.name) {
			employeeDoc.reload()
		}
	})
})

watch(
	() => employee.data?.name,
	async (employeeName) => {
		if (!employeeName) return
		employeeDoc.name = employeeName
		await employeeDoc.reload()
		assignEmployeeFormFromDoc()
		await loadEmployeeBankAccounts()
	},
	{ immediate: true }
)

watch(
	() => employeeDoc.doc,
	() => {
		assignEmployeeFormFromDoc()
	},
	{ immediate: true }
)

onBeforeUnmount(() => {
	clearSelectedProfileImage()
	socket.emit("doctype_unsubscribe", DOCTYPE)
	socket.off("list_update")
})
</script>
