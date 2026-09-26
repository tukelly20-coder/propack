/**
 * Customers Module
 * Quản lý danh sách khách hàng
 */

// ============================================
// UTILITY
// ============================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// STATE
// ============================================

const CustomersState = {
    customers: [],
    filteredCustomers: [],
    isLoading: false,
    editingId: null,
    deletingId: null,
    searchQuery: ''
};

// ============================================
// INITIALIZATION
// ============================================

function initCustomersModule() {
    console.log('[Customers] Initializing...');
    renderCustomersContent();
    translatePage();
    setupCustomersEvents();
    loadCustomers();
}

// ============================================
// RENDERING
// ============================================

function renderCustomersContent() {
    const container = document.getElementById('customers-container');
    if (!container) return;

    container.innerHTML = `
        <div class="customers-container">
            <!-- Toolbar -->
            <div class="toolbar-row mb-3">
                <div class="row g-2 align-items-center">
                    <div class="col-md-6">
                        <div class="input-group">
                            <span class="input-group-text"><i class="bi bi-search"></i></span>
                            <input type="text" class="form-control" id="customer-search-input"
                                   placeholder="${t('search_customers')}" data-i18n-placeholder="search_customers">
                        </div>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <button class="btn btn-primary" id="btn-add-customer">
                            <i class="bi bi-plus-circle"></i> <span data-i18n="add_customer">${t('add_customer')}</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="table-responsive">
                <table class="table table-hover table-bordered customers-table" id="customers-table">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 80px;">STT</th>
                            <th>${t('customer_code')}</th>
                            <th>${t('customer_name')}</th>
                            <th>${t('customer_phonetic')}</th>
                            <th>${t('customer_english_name')}</th>
                            <th>${t('customer_contact_person')}</th>
                            <th>${t('customer_phone')}</th>
                            <th>${t('customer_email')}</th>
                            <th style="width: 160px;">${t('action')}</th>
                        </tr>
                    </thead>
                    <tbody id="customers-tbody">
                        <tr>
                            <td colspan="9" class="text-center py-4">
                                <div class="spinner-border text-primary" role="status"></div>
                                <p class="mt-2 text-muted">${t('loading')}</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Empty State -->
            <div class="empty-state text-center py-5" id="customers-empty" style="display: none;">
                <i class="bi bi-people display-4 text-muted"></i>
                <p class="mt-2 text-muted">${t('no_customers')}</p>
            </div>
        </div>

        <!-- Customer Modal -->
        <div class="modal fade" id="customer-modal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="customer-modal-title">
                            <i class="bi bi-person-plus"></i> <span data-i18n="add_customer">${t('add_customer')}</span>
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="customer-form">
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_code')}</label>
                                    <input type="text" class="form-control" id="field-customer-code"
                                           placeholder="VD: 0001" maxlength="50">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_name')} *</label>
                                    <input type="text" class="form-control" id="field-customer-name"
                                           placeholder="${t('customer_name')}" required maxlength="200">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_phonetic')}</label>
                                    <input type="text" class="form-control" id="field-customer-phonetic"
                                           placeholder="Phiên âm" maxlength="100">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_english_name')}</label>
                                    <input type="text" class="form-control" id="field-customer-english"
                                           placeholder="English name" maxlength="200">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_contact_person')}</label>
                                    <input type="text" class="form-control" id="field-customer-contact"
                                           placeholder="Người liên hệ" maxlength="100">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_phone')}</label>
                                    <input type="text" class="form-control" id="field-customer-phone"
                                           placeholder="Số điện thoại" maxlength="50">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_email')}</label>
                                    <input type="email" class="form-control" id="field-customer-email"
                                           placeholder="email@example.com" maxlength="100">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">${t('customer_address')}</label>
                                    <input type="text" class="form-control" id="field-customer-address"
                                           placeholder="Địa chỉ" maxlength="200">
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-primary" id="btn-save-customer">
                            <i class="bi bi-save"></i> ${t('save')}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div class="modal fade" id="delete-customer-modal" tabindex="-1" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-exclamation-triangle"></i> ${t('confirm_delete_customer_title')}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p id="delete-customer-message"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${t('cancel')}</button>
                        <button type="button" class="btn btn-danger" id="btn-confirm-delete-customer">
                            <i class="bi bi-trash"></i> ${t('delete')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// DATA LOADING
// ============================================

async function loadCustomers() {
    CustomersState.isLoading = true;
    try {
        const result = await getCustomers();
        if (result && result.success) {
            CustomersState.customers = result.data || [];
            CustomersState.filteredCustomers = [...CustomersState.customers];
        } else {
            CustomersState.customers = [];
            CustomersState.filteredCustomers = [];
        }
    } catch (error) {
        console.error('[Customers] Error loading customers:', error);
        CustomersState.customers = [];
        CustomersState.filteredCustomers = [];
        showToast(t('error'), t('load_error'), 'error');
    } finally {
        CustomersState.isLoading = false;
        renderCustomersTable();
    }
}

function filterCustomers() {
    const query = CustomersState.searchQuery.toLowerCase().trim();
    if (!query) {
        CustomersState.filteredCustomers = [...CustomersState.customers];
    } else {
        CustomersState.filteredCustomers = CustomersState.customers.filter(c => {
            return (c.name || '').toLowerCase().includes(query) ||
                   (c.code || '').toLowerCase().includes(query) ||
                   (c.english_name || '').toLowerCase().includes(query) ||
                   (c.phonetic || '').toLowerCase().includes(query) ||
                   (c.contact_person || '').toLowerCase().includes(query);
        });
    }
    renderCustomersTable();
}

// ============================================
// TABLE RENDERING
// ============================================

function renderCustomersTable() {
    const tbody = document.getElementById('customers-tbody');
    const emptyState = document.getElementById('customers-empty');
    if (!tbody) return;

    if (CustomersState.filteredCustomers.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    tbody.innerHTML = CustomersState.filteredCustomers.map((customer, index) => {
        const id = customer.id || '';
        const code = escapeHtml(customer.code || '');
        const name = escapeHtml(customer.name || '');
        const phonetic = escapeHtml(customer.phonetic || '');
        const englishName = escapeHtml(customer.english_name || '');
        const contactPerson = escapeHtml(customer.contact_person || '');
        const phone = escapeHtml(customer.phone || '');
        const email = escapeHtml(customer.email || '');

        return `
            <tr data-customer-id="${id}">
                <td>${index + 1}</td>
                <td>${code}</td>
                <td><strong>${name}</strong></td>
                <td>${phonetic}</td>
                <td>${englishName}</td>
                <td>${contactPerson}</td>
                <td>${phone}</td>
                <td>${email}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary btn-edit-customer" data-id="${id}" title="${t('edit')}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-delete-customer" data-id="${id}" title="${t('delete')}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// ============================================
// EVENT HANDLERS
// ============================================

function setupCustomersEvents() {
    // Search
    const searchInput = document.getElementById('customer-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            CustomersState.searchQuery = this.value;
            filterCustomers();
        });
    }

    // Add button
    const addBtn = document.getElementById('btn-add-customer');
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            openCustomerModal();
        });
    }

    // Save button
    const saveBtn = document.getElementById('btn-save-customer');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveCustomer);
    }

    // Delete button
    const deleteBtn = document.getElementById('btn-confirm-delete-customer');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', confirmDeleteCustomer);
    }

    // Edit buttons (delegated)
    const tbody = document.getElementById('customers-tbody');
    if (tbody) {
        tbody.addEventListener('click', function(e) {
            const editBtn = e.target.closest('.btn-edit-customer');
            const deleteBtnRow = e.target.closest('.btn-delete-customer');

            if (editBtn) {
                const id = editBtn.dataset.id;
                openCustomerModal(id);
            } else if (deleteBtnRow) {
                const id = deleteBtnRow.dataset.id;
                const name = deleteBtnRow.closest('tr').querySelector('td:nth-child(3) strong')?.textContent || '';
                openDeleteCustomerModal(id, name);
            }
        });
    }
}

// ============================================
// MODAL OPERATIONS
// ============================================

function openCustomerModal(customerId = null) {
    CustomersState.editingId = customerId;
    const modalTitle = document.getElementById('customer-modal-title');
    const form = document.getElementById('customer-form');

    if (customerId) {
        const customer = CustomersState.customers.find(c => c.id == customerId);
        if (customer) {
            if (modalTitle) modalTitle.innerHTML = `<i class="bi bi-pencil"></i> ${t('edit_customer')}`;
            if (form) form.reset();
            $('#field-customer-code').val(customer.code || '');
            $('#field-customer-name').val(customer.name || '');
            $('#field-customer-phonetic').val(customer.phonetic || '');
            $('#field-customer-english').val(customer.english_name || '');
            $('#field-customer-contact').val(customer.contact_person || '');
            $('#field-customer-phone').val(customer.phone || '');
            $('#field-customer-email').val(customer.email || '');
            $('#field-customer-address').val(customer.address || '');
        }
    } else {
        if (modalTitle) modalTitle.innerHTML = `<i class="bi bi-person-plus"></i> ${t('add_customer')}`;
        if (form) form.reset();
    }

    const modal = new bootstrap.Modal(document.getElementById('customer-modal'));
    modal.show();
}

function openDeleteCustomerModal(customerId, customerName) {
    CustomersState.deletingId = customerId;
    const messageEl = document.getElementById('delete-customer-message');
    if (messageEl) {
        messageEl.textContent = t('confirm_delete_customer').replace('{name}', customerName);
    }
    const modal = new bootstrap.Modal(document.getElementById('delete-customer-modal'));
    modal.show();
}

async function saveCustomer() {
    const code = ($('#field-customer-code').val() || '').trim();
    const name = ($('#field-customer-name').val() || '').trim();
    const phonetic = ($('#field-customer-phonetic').val() || '').trim();
    const englishName = ($('#field-customer-english').val() || '').trim();
    const contactPerson = ($('#field-customer-contact').val() || '').trim();
    const phone = ($('#field-customer-phone').val() || '').trim();
    const email = ($('#field-customer-email').val() || '').trim();
    const address = ($('#field-customer-address').val() || '').trim();

    if (!name) {
        showToast(t('error'), 'Tên khách hàng không được để trống', 'error');
        return;
    }

    const customerData = {
        code: code || null,
        name: name,
        phonetic: phonetic || null,
        english_name: englishName || null,
        contact_person: contactPerson || null,
        phone: phone || null,
        email: email || null,
        address: address || null
    };

    try {
        let result;
        if (CustomersState.editingId) {
            result = await updateCustomer(CustomersState.editingId, customerData);
            if (result && result.success) {
                showToast(t('success'), t('customer_updated'), 'success');
            } else if (result && !result.success) {
                showToast(t('error'), result.error || t('error_saving'), 'error');
                return;
            }
        } else {
            result = await createCustomer(customerData);
            if (result && result.success) {
                showToast(t('success'), t('customer_created'), 'success');
            } else if (result && !result.success) {
                if (result.error && result.error.includes('đã tồn tại')) {
                    showToast(t('warning'), t('customer_exists'), 'warning');
                } else {
                    showToast(t('error'), result.error || t('error_saving'), 'error');
                }
                return;
            }
        }

        // Close modal
        const modalEl = document.getElementById('customer-modal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        // Reload data
        await loadCustomers();

    } catch (error) {
        console.error('[Customers] Error saving customer:', error);
        showToast(t('error'), t('error_saving'), 'error');
    }
}

async function confirmDeleteCustomer() {
    if (!CustomersState.deletingId) return;

    try {
        const result = await deleteCustomer(CustomersState.deletingId);
        if (result && result.success) {
            showToast(t('success'), t('customer_deleted'), 'success');
        } else if (result && !result.success) {
            showToast(t('error'), result.error || t('error_deleting'), 'error');
            return;
        }

        // Close modal
        const modalEl = document.getElementById('delete-customer-modal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        CustomersState.deletingId = null;
        await loadCustomers();

    } catch (error) {
        console.error('[Customers] Error deleting customer:', error);
        showToast(t('error'), t('error_deleting'), 'error');
    }
}
