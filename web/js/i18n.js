/**
 * Internationalization (i18n) System for Propack VP Web
 * Hỗ trợ Tiếng Việt (vi) và Tiếng Trung (zh)
 */

// Current language state (storage-polyfill already wraps localStorage safely)
let currentLanguage = localStorage.getItem('language') || 'vi';

// Translations object
const translations = {
    vi: {
        // ============================================
        // COMMON / SHARED
        // ============================================
        
        // App title
        app_title: 'Quản Lý Dự Án - Propack VP',
        
        // Loading states
        loading: 'Đang tải...',
        loading_data: 'Đang tải dữ liệu...',
        saving: 'Đang lưu...',
        deleting: 'Đang xóa...',
        processing: 'Đang xử lý...',
        
        // Success/Error/Warning
        success: 'Thành công',
        error: 'Lỗi',
        warning: 'Cảnh báo',
        info: 'Thông tin',
        
        // Actions
        save: 'Lưu',
        cancel: 'Hủy',
        delete: 'Xóa',
        edit: 'Sửa',
        view: 'Xem',
        add: 'Thêm',
        refresh: 'Làm mới',
        export: 'Xuất',
        search: 'Tìm kiếm',
        close: 'Đóng',
        confirm: 'Xác nhận',
        apply: 'Áp dụng',
        reset: 'Mặc định',
        submit: 'Gửi',
        
        // Pagination
        page: 'Trang',
        of: 'của',
        per_page: 'trang',
        first_page: 'Trang đầu',
        previous_page: 'Trước',
        next_page: 'Sau',
        last_page: 'Trang cuối',
        page_info: 'Hiển thị {start} - {end} của {total} bản ghi',
        jump_to_page: 'Nhảy đến trang',
        
        // Empty/Error states
        no_data: 'Không có dữ liệu',
        no_results: 'Không tìm thấy kết quả',
        load_error: 'Lỗi tải dữ liệu',
        
        // Confirmation
        confirm_delete: 'Xác nhận xóa',
        confirm_delete_message: 'Bạn có chắc chắn muốn xóa {count} item đã chọn không?',
        confirm_logout: 'Bạn có chắc muốn đăng xuất?',
        
        // ============================================
        // LOGIN
        // ============================================
        login_title: 'Quản Lý Dự Án',
        login_subtitle: 'Đăng nhập để tiếp tục',
        username: 'Tên đăng nhập',
        password: 'Mật khẩu',
        remember_me: 'Ghi nhớ đăng nhập',
        login_btn: 'Đăng nhập',
        login_failed: 'Đăng nhập thất bại',
        login_error: 'Vui lòng nhập tên đăng nhập và mật khẩu',
        logging_in: 'Đang đăng nhập...',
        toast_login_success: 'Đăng nhập thành công!',
        toast_logout_success: 'Đã đăng xuất!',
        toast_login_failed: 'Đăng nhập thất bại',
        login_failed_retry: 'Đăng nhập thất bại. Vui lòng thử lại.',
        
        // ============================================
        // NAVIGATION
        // ============================================
        nav_projects: 'Dự Án',
        nav_notices: 'Thông báo',
        nav_taomabanve: 'Tạo Mã Bản Vẽ',
        nav_profile: 'Hồ Sơ',
        nav_ai: 'PropackAI',
        
        // Language selector
        language_vi: 'VI',
        language_zh: '中文',
        language_label: 'Ngôn ngữ',
        
        // User section
        submit_feedback: 'Gửi Phản hồi',
        logout: 'Đăng xuất',
        logged_in_as: 'Đăng nhập với',
        
        // ============================================
        // PROJECTS MODULE
        // ============================================
        projects_title: 'Dự án',
        add_project: 'Thêm mới',
        quick_add_double_click: 'Bấm đúp để tạo ID mới',
        quick_add_start_title: 'Bấm đúp để tạo ID mới rồi nhập thông tin',
        quick_add_new_id: 'ID mới',
        quick_add_save_title: 'Lưu dự án mới',
        quick_add_missing_fields: 'Vui lòng nhập: {fields}',
        edit_project: 'Sửa',
        delete_project: 'Xóa',
        refresh_projects: 'Làm mới dữ liệu',
        toggle_columns: 'Chọn cột hiển thị',
        btn_toggle_columns: 'Chọn cột',
        export_excel: 'Xuất Excel',
        export_csv: 'Xuất CSV',
        
        // Filters
        filter_status: 'Lọc theo trạng thái',
        filter_urgency: 'Lọc theo độ khẩn',
        all_status: 'Tất cả trạng thái',
        all_urgency: 'Tất cả độ khẩn',
        status_pending: 'Chờ xử lý',
        status_in_progress: 'Đang làm',
        status_completed: 'Hoàn thành',
        urgency_normal: 'Bình thường',
        urgency_urgent: 'Khẩn cấp',
        urgency_very_urgent: 'Rất khẩn',
        search_projects: 'Tìm kiếm...',
        clear_search: 'Xóa tìm kiếm',
        
        // Table headers
        stt: 'STT',
        col_stt: 'STT',
        col_tracking_id: 'Tracking ID',
        col_ngay: 'Ngày',
        col_khachhang: 'Khách hàng',
        col_nhanvienkd: 'Nhân viên KD',
        col_tensanpham: 'Tên sản phẩm',
        col_quycach: 'Quy cách',
        col_lienhe_kh: 'Người liên hệ (KH)',
        col_soluong: 'Số lượng',
        col_mapo: 'Mã PO',
        col_mabave: 'Mã bản vẽ',
        col_mabavkythuat: 'Mã bản vẽ phương án',
        col_mame: 'Mã mẹ',
        col_loaisanpham: 'Loại sản phẩm',
        col_kysu: 'Kỹ sư',
        col_tinhtrang: 'Tình trạng nhận dự án',
        col_dokhan: 'Độ khẩn',
        col_tg_mongmuon: 'TG mong muốn',
        col_tg_hoanthanh: 'TG hoàn thành',
        col_trangthai: 'Trạng thái',
        col_nguoinhan: 'Người nhận',
        col_actions: 'Hành động',
        col_select: 'Chọn',
        
        // Column selector
        column_selector_title: 'Chọn cột hiển thị',
        column_reset: 'Mặc định',
        column_apply: 'Áp dụng',
        
        // Modal - Add/Edit Project
        add_project_title: 'Thêm dự án mới',
        edit_project_title: 'Sửa dự án',
        view_project_title: 'Chi tiết dự án',
        
        // Form fields - Basic info
        form_ngay_khoitao: 'Ngày khởi tạo',
        form_khachhang: 'Khách hàng',
        form_khachhang_required: 'Khách hàng *',
        select_customer: '-- Chọn khách hàng --',
        liveSearch_placeholder: 'Tìm kiếm khách hàng...',
        form_nhanvienkd: 'Nhân viên kinh doanh',
        
        // Form fields - Product info
        form_tensanpham: 'Tên sản phẩm',
        form_tensanpham_required: 'Tên sản phẩm *',
        form_quycach: 'Quy cách',
        form_lienhe_kh: 'Người liên hệ (KH)',
        form_soluong: 'Số lượng',
        form_mapo: 'Mã PO',
        
        // Form sections
        product_info: 'Thông tin sản phẩm',
        drawing_codes: 'Mã bản vẽ',
        
        // Form fields - Drawing codes
        form_mabave_chinh: 'Mã bản vẽ chính',
        form_mabave: 'Mã bản vẽ (phương án)',
        form_mabavkythuat: 'Mã bản vẽ kỹ thuật',
        form_mame: 'Mã mẹ',
        
        // Form fields - Technical info
        form_loaisanpham: 'Loại sản phẩm',
        select_loaisanpham: '-- Chọn loại sản phẩm --',
        loaisanpham_sjt: 'Bản vẽ tách chi tiết',
        loaisanpham_wlj: 'Giá đựng vật liệu',
        loaisanpham_zzc: 'Xe trung chuyển',
        loaisanpham_gzt: 'Bàn thao tác',
        loaisanpham_wcp: 'Phòng sạch',
        loaisanpham_lsx: 'Băng tải',
        loaisanpham_zwj: 'Băng tải chuyển hướng',
        loaisanpham_gzl: 'Cải tạo',
        loaisanpham_bsx: 'Băng chuyền xích',
        loaisanpham_wll: 'Hàng rào',
        loaisanpham_gtx: 'Băng chuyền con lăn',
        loaisanpham_zht: 'Bản vẽ mặt bằng',
        loaisanpham_lhx: 'Băng chuyền lão hóa',
        form_kysu: 'Nhân viên thiết kế',
        form_tinhtrang: 'Tình trạng hoàn thành',
        
        // Form fields - Time & Urgency
        form_capbach: 'Tính cấp bách',
        form_tg_mongmuon: 'Thời gian mong muốn có bản vẽ',
        form_tg_hoanthanh: 'Thời gian hoàn thành kế hoạch',
        
        // Urgency options
        urgency_normal_option: 'Bình thường',
        urgency_urgent_option: 'Khẩn cấp',
        urgency_very_urgent_option: 'Rất khẩn cấp',
        
        // Quick actions
        quick_view: 'Xem chi tiết',
        quick_edit: 'Sửa',
        quick_delete: 'Xóa',
        quick_accept: 'Nhận việc',
        
        // Toast messages
        toast_project_created: 'Tạo dự án thành công',
        toast_project_updated: 'Cập nhật dự án thành công',
        toast_project_deleted: 'Đã xóa {count} dự án',
        toast_export_success: 'Đã xuất file {type}',
        toast_no_data_export: 'Không có dữ liệu để xuất',
        
        // Validation
        validation_khachhang_required: 'Vui lòng nhập tên khách hàng',
        validation_tensanpham_required: 'Vui lòng nhập tên sản phẩm',
        validation_lienhe_required: 'Vui lòng nhập người liên hệ',
        validation_invalid_page: 'Vui lòng nhập trang từ 1 đến {max}',
        
        // ============================================
        // NOTICES MODULE
        // ============================================
        notices_title: 'Thông báo',
        add_notice: 'Thêm mới',
        edit_notice: 'Sửa',
        delete_notice: 'Xóa',
        
        // Stats
        stat_total: 'Tổng',
        stat_pending: 'Chờ duyệt',
        stat_accepted: 'Đã nhận',
        stat_urgent: 'Khẩn',
        auto_refresh_note: 'Tự động cập nhật mỗi 30 giây',
        
        // Status options
        status_pending_option: 'Chờ duyệt',
        status_accepted: 'Đã nhận',
        status_in_progress: 'Đang làm',
        status_completed_option: 'Hoàn thành',
        
        // Notice form
        form_sanpham: 'Sản phẩm',
        form_kysu_field: 'Kỹ sư',
        form_dokhan: 'Độ khẩn',
        form_trangthai: 'Trạng thái',
        
        // Table headers
        notice_stt: 'STT',
        notice_tracking_id: 'Tracking ID',
        notice_ngay: 'Ngày',
        notice_khachhang: 'Khách hàng',
        notice_sanpham: 'Sản phẩm',
        notice_soluong: 'Số lượng',
        notice_nhanvienkd: 'Nhân viên KD',
        notice_kysu: 'Kỹ sư',
        notice_dokhan: 'Độ khẩn',
        notice_trangthai: 'Trạng thái',
        notice_actions: 'Hành động',
        notice_select: 'Chọn',
        
        // Quick actions
        notice_quick_accept: 'Nhận việc',
        notice_quick_view: 'Xem chi tiết',
        notice_quick_edit: 'Sửa',
        notice_quick_delete: 'Xóa',
        
        // Form labels
        notice_form_ngay_khoitao: 'Ngày khởi tạo',
        notice_form_khachhang: 'Khách hàng',
        notice_form_khachhang_required: 'Khách hàng *',
        notice_form_nhanvienkd: 'Nhân viên kinh doanh',
        notice_form_tensanpham: 'Tên sản phẩm',
        notice_form_tensanpham_required: 'Tên sản phẩm *',
        notice_form_soluong: 'Số lượng',
        notice_form_kysu: 'Kỹ sư',
        notice_form_dokhan: 'Độ khẩn',
        notice_form_trangthai: 'Trạng thái',
        
        // Filter options
        notice_filter_status: 'Lọc theo trạng thái',
        notice_filter_urgency: 'Lọc theo độ khẩn',
        notice_all_status: 'Tất cả trạng thái',
        notice_all_urgency: 'Tất cả độ khẩn',
        
        // Empty state
        no_notices_found: 'Không tìm thấy thông báo nào',
        
        // Actions
        accept_job: 'Nhận việc',
        accept_job_confirm: 'Bạn có muốn nhận công việc này?',
        accept_job_success: 'Đã nhận công việc',
        
        // Toast messages
        toast_notice_created: 'Tạo thông báo thành công',
        toast_notice_updated: 'Cập nhật thông báo thành công',
        toast_notice_deleted: 'Đã xóa {count} thông báo',
        
        // ============================================
        // PROFILE MODULE
        // ============================================
        profile_title: 'Hồ sơ',
        basic_info: 'Thông tin cơ bản',
        contact_info: 'Thông tin liên lạc',
        login_history: 'Lịch sử đăng nhập',
        
        form_username: 'Tên đăng nhập',
        form_role: 'Vai trò',
        form_fullname: 'Họ và tên',
        form_employee_id: 'Mã nhân viên',
        form_employee_id_placeholder: 'Nhập mã nhân viên',
        form_department: 'Phòng ban',
        form_status: 'Trạng thái',
        form_email: 'Email',
        form_phone: 'Số điện thoại',
        form_last_login: 'Đăng nhập lần cuối',
        form_created_at: 'Ngày tạo tài khoản',
        
        save_profile: 'Lưu thông tin',
        change_password: 'Đổi mật khẩu',
        refresh_profile: 'Làm mới',
        
        // Password change
        password_change_title: 'Đổi mật khẩu',
        current_password: 'Mật khẩu hiện tại',
        new_password: 'Mật khẩu mới',
        confirm_password: 'Xác nhận mật khẩu mới',
        confirm_password_btn: 'Xác nhận',
        
        // Validation
        password_current_required: 'Vui lòng nhập mật khẩu hiện tại',
        password_new_required: 'Vui lòng nhập mật khẩu mới',
        password_confirm_required: 'Vui lòng xác nhận mật khẩu mới',
        password_not_match: 'Mật khẩu mới không khớp',
        password_min_length: 'Mật khẩu mới phải có ít nhất 6 ký tự',
        
        // Error messages
        error_loading_profile: 'Không thể tải thông tin hồ sơ',
        error_saving_profile: 'Không thể lưu hồ sơ',
        error_loading: 'Không thể tải',
        error_saving: 'Không thể lưu',
        error_session_expired: 'Phiên đăng nhập hết hạn',
        error_fill_all_fields: 'Vui lòng nhập đầy đủ thông tin',
        
        // Toast messages
        toast_profile_saved: 'Lưu hồ sơ thành công!',
        toast_password_changed: 'Đổi mật khẩu thành công!',
        
        // ============================================
        // SUBMIT FEEDBACK
        // ============================================
        feedback_title: 'Gửi Phản Hồi',
        feedback_type: 'Loại log',
        feedback_type_general: 'Chung',
        feedback_type_error: 'Lỗi',
        feedback_type_debug: 'Debug',
        feedback_type_login: 'Đăng nhập',
        feedback_content: 'Nội dung phản hồi',
        feedback_content_placeholder: 'Nhập nội dung phản hồi cần gửi...',
        feedback_submit: 'Gửi phản hồi',
        
        // Toast messages
        toast_feedback_sent: 'Phản hồi đã được gửi!',
        toast_feedback_error: 'Vui lòng nhập nội dung phản hồi',
        feedback_content_required: 'Vui lòng nhập nội dung phản hồi',
        feedback_error: 'Có lỗi xảy ra',
        
        // Toast show titles
        toast_success: 'Thành công',
        toast_error: 'Lỗi',
        toast_warning: 'Cảnh báo',
        toast_info: 'Thông tin',
        exporting_data: 'Đang xuất dữ liệu...',
        basic_info: 'Thông tin cơ bản',
        technical_info: 'Thông tin kỹ thuật',
        time_urgency: 'Thời gian & Độ khẩn',
        
        // ============================================
        // CREATE CODE (TAOMABANVE) MODULE
        // ============================================
        create_code_title: 'Tạo Mã Bản Vẽ',
        requester_name: 'Tên người xin mã',
        employee_code: 'Mã nhân viên công trình',
        three_digits: '3 chữ số',
        employee_code_hint: 'Nhập ID nhân viên công trình 3 chữ số (vd: 001, 002, 003)',
        category: 'Hạng mục',
        select_category: '-- Chọn hạng mục --',
        plan_code: 'Mã bản vẽ phương án',
        plan_code_placeholder: 'Nhập mã bản vẽ phương án',
        search_history_placeholder: 'Tìm kiếm lịch sử...',
        create_btn: 'Tạo Mã',
        confirm_create_code_title: 'Xác nhận muốn tạo mã này:',
        
        // Categories
        cat_sjt: 'SJT散件图 - Bản vẽ tách chi tiết',
        cat_wlj: 'WLJ物料架 - Giá đựng vật liệu',
        cat_zzc: 'ZZC周转车 - Xe trung chuyển',
        cat_gzt: 'GZT工作台 - Bàn thao tác',
        cat_wcp: 'WCP无尘棚 - Phòng sạch',
        cat_lsx: 'LSX流水线 - Băng tải',
        cat_zwj: 'ZWJ转弯机 - Băng tải chuyển hướng 90,180',
        cat_gzl: 'GZL改造类 - Cải tạo',
        cat_bsx: 'BSX倍速线 - Băng chuyền xích',
        cat_wll: 'WLL围栏类 - Hàng rào',
        cat_gtx: 'GTX滚筒线 - Băng chuyền con lăn',
        cat_zht: 'ZHT展会图 - Bản vẽ mặt bằng',
        cat_lhx: 'LHX老化线 - Băng chuyền lão hóa',
        
        // History
        history_title: 'Lịch Sử Tạo Mã',
        history: 'Lịch Sử Tạo Mã',
        history_total: 'Tổng',
        total: 'Tổng',
        history_today: 'Hôm nay',
        today: 'Hôm nay',
        history_week: 'Tuần',
        week: 'Tuần',
        history_latest: 'Mới nhất',
        latest: 'Mới nhất',
        history_name: 'Tên',
        name: 'Tên',
        history_employee_code: 'Mã nhân viên',
        employee_code_th: 'Mã nhân viên',
        history_category: 'Hạng mục',
        category_th: 'Hạng mục',
        history_drawing_code: 'Mã bản vẽ',
        drawing_code: 'Mã bản vẽ',
        mother_code: 'Mã mẹ',
        history_time: 'Thời gian',
        time: 'Thời gian',
        history_action: 'Thao tác',
        action: 'Thao tác',
        history_copy: 'Copy',
        history_delete: 'Xóa',
        context_copy_code: 'Copy mã',
        context_delete_code: 'Xóa mã',
        right_click_hint: 'Nhấp chuột phải để copy hoặc xóa mã',
        create_code: 'Tạo Mã Bản Vẽ',
        
        // Delete code
        delete_code_title: 'Xóa mã',
        delete_code_confirm: 'Nhập mật khẩu để xóa mã {code}:',
        delete_code_password: 'Mật khẩu',
        delete_code_wrong_password: 'Mật khẩu không đúng',
        delete_code_expired: 'Chỉ được xóa mã trong vòng 2 giờ kể từ khi tạo',
        
        // Toast messages
        toast_code_created: 'Đã tạo mã: ',
        toast_code_copy: 'Đã copy mã vào clipboard',
        toast_code_deleted: 'Đã xóa mã {code}',
        
        // Actions & Messages
        creating: 'Đang tạo mã bản vẽ...',
        creating_code: 'Đang tạo mã...',
        deleting_code: 'Đang xóa mã...',
        exporting_data: 'Đang xuất dữ liệu...',
        
        // No history / Empty states
        no_history: 'Chưa có lịch sử tạo mã',
        load_history_error: 'Lỗi tải lịch sử: ',
        
        // Buttons
        copy_title: 'Copy',
        delete_title: 'Xóa',
        
        // Excel export
        excel_sheet_name: 'LichSuMa',
        excel_filename_prefix: 'lich_su_ma_',
        
        // Validation
        validation_employee_3digits: 'Mã nhân viên phải có 3 chữ số',
        validation_employee_not_zero: 'Mã nhân viên không được là 000',
        validation_name_required: 'Vui lòng nhập tên người xin mã',
        validation_category_required: 'Vui lòng chọn hạng mục',
        
        // Additional
        toast_warning: 'Cảnh báo',
        toast_no_data_export: 'Không có dữ liệu để xuất',
        toast_export_success: 'Đã xuất file {type}',
        
        // Relative time
        seconds_ago: 'giây trước',
        minutes_ago: 'phút trước',
        hours_ago: 'giờ trước',
        yesterday: 'Hôm qua',
        days_ago: 'ngày trước',
        
        // ============================================
        // AI MODULE (Placeholder)
        // ============================================
        ai_title: 'PropackAI',
        
        // ============================================
        // MISC
        // ============================================
        chars: 'ký tự',
        use_system_account: 'Sử dụng tài khoản từ hệ thống',
        
        // Loading states
        loading_projects: 'Đang tải dữ liệu dự án...',
        loading_notices: 'Đang tải thông báo...',
        loading_taomabanve: 'Đang tải trang tạo mã...',
        loading_profile: 'Đang tải hồ sơ...',
        loading_ai: 'Đang tải AI...'
    },
    
    // ==================== ZH - CHINESE ====================
    zh: {
        // ============================================
        // COMMON / SHARED
        // ============================================
        
        // App title
        app_title: '大日程 - Propack VP',
        
        // Loading states
        loading: '加载中...',
        loading_data: '正在加载数据...',
        saving: '正在保存...',
        deleting: '正在删除...',
        processing: '正在处理...',
        
        // Success/Error/Warning
        success: '成功',
        error: '错误',
        warning: '警告',
        info: '信息',
        
        // Actions
        save: '保存',
        cancel: '取消',
        delete: '删除',
        edit: '编辑',
        view: '查看',
        add: '新建项目',
        refresh: '刷新',
        export: '导出',
        search: '搜索',
        close: '关闭',
        confirm: '确认',
        apply: '应用',
        reset: '默认',
        submit: '提交',
        
        // Pagination
        page: '页',
        of: '共',
        per_page: '页',
        first_page: '首页',
        previous_page: '上一页',
        next_page: '下一页',
        last_page: '末页',
        page_info: '显示 {start} - {end}，共 {total} 条',
        jump_to_page: '跳转到页',
        
        // Empty/Error states
        no_data: '暂无数据',
        no_results: '未找到结果',
        load_error: '加载数据出错',
        
        // Confirmation
        confirm_delete: '确认删除',
        confirm_delete_message: '确定要删除选中的 {count} 项吗？',
        confirm_logout: '确定要退出登录吗？',
        
        // ============================================
        // LOGIN
        // ============================================
        login_title: '大日程',
        login_subtitle: '登录以继续',
        username: '用户名',
        password: '密码',
        remember_me: '记住登录',
        login_btn: '登录',
        login_failed: '登录失败',
        login_error: '请输入用户名和密码',
        logging_in: '正在登录...',
        toast_login_success: '登录成功！',
        toast_logout_success: '已退出登录！',
        toast_login_failed: '登录失败',
        login_failed_retry: '登录失败，请重试。',
        
        // ============================================
        // NAVIGATION
        // ============================================
        nav_projects: '大日程',
        nav_notices: '通知',
        nav_taomabanve: '生成图纸编码',
        nav_profile: '个人信息',
        nav_ai: 'PropackAI（试用）',
        
        // Language selector
        language_vi: 'VI',
        language_zh: '中文',
        language_label: '语言',
        
        // User section
        submit_feedback: '提交反馈',
        logout: '退出登录',
        logged_in_as: '登录为',
        
        // ============================================
        // PROJECTS MODULE
        // ============================================
        projects_title: '大日程',
        add_project: '新建',
        quick_add_double_click: '双击创建新ID',
        quick_add_start_title: '双击创建新ID，然后填写信息',
        quick_add_new_id: '新ID',
        quick_add_save_title: '保存新项目',
        quick_add_missing_fields: '请填写：{fields}',
        edit_project: '编辑',
        delete_project: '删除',
        refresh_projects: '刷新数据',
        toggle_columns: '选择显示列',
        btn_toggle_columns: '列',
        export_excel: '导出Excel',
        export_csv: '导出CSV',
        
        // Filters
        filter_status: '按状态筛选',
        filter_urgency: '按紧急程度筛选',
        all_status: '全部状态',
        all_urgency: '全部紧急程度',
        status_pending: '待处理',
        status_in_progress: '进行中',
        status_completed: '已完成',
        urgency_normal: '正常',
        urgency_urgent: '紧急',
        urgency_very_urgent: '非常紧急',
        search_placeholder: '搜索...',
        clear_search: '清除搜索',
        
        // Table headers
        stt: '序号',
        col_stt: '序号',
        col_tracking_id: 'Tracking ID',
        col_ngay: '创建日期',
        col_khachhang: '客户公司名称',
        col_nhanvienkd: '业务员',
        col_tensanpham: '产品名称',
        col_quycach: '规格',
        col_lienhe_kh: '客户联系人',
        col_soluong: '数量',
        col_mapo: 'PO号',
        col_mabave: '图纸编码',
        col_mabavkythuat: '方案图号',
        col_mame: '母料号',
        col_loaisanpham: '产品类型',
        col_kysu: '工程师',
        col_tinhtrang: '接受方案状态',
        col_dokhan: '紧急程度',
        col_tg_mongmuon: '期望时间',
        col_tg_hoanthanh: '完成时间',
        col_trangthai: '状态',
        col_nguoinhan: '接收人',
        col_actions: '操作',
        col_select: '选择',
        
        // Toolbar & Actions
        btn_add: '新建',
        btn_edit: '编辑',
        btn_delete: '删除',
        btn_refresh: '刷新数据',
        btn_toggle_columns: '列',
        btn_export: '导出',
        
        // Search
        search_placeholder: '搜索...',
        
        // Form sections
        product_info: '产品信息',
        drawing_codes: '图纸编码',
        
        // Empty/Error states
        no_data_projects: '暂无项目数据',
        load_error_projects: '加载数据出错',
        
        // Column selector
        column_selector_title: '选择显示列',
        column_reset: '默认',
        column_apply: '应用',
        
        // Modal - Add/Edit Project
        add_project_title: '新建项目',
        edit_project_title: '编辑项目',
        view_project_title: '项目详情',
        
        // Form fields - Basic info
        form_ngay_khoitao: '创建日期',
        form_khachhang: '客户公司名称',
        form_khachhang_required: '客户 *',
        select_customer: '-- 选择客户 --',
        liveSearch_placeholder: '搜索客户...',
        form_nhanvienkd: '业务员',
        
        // Form fields - Product info
        form_tensanpham: '产品名称',
        form_tensanpham_required: '产品名称 *',
        form_quycach: '规格',
        form_lienhe_kh: '联系人(客户)',
        form_soluong: '数量',
        form_mapo: 'PO号',
        
        // Form fields - Drawing codes
        form_mabave_chinh: '图纸编码',
        form_mabave: '图纸编码(方案)',
        form_mabavkythuat: '技术图纸编码',
        form_mame: '母料号',
        
        // Form fields - Technical info
        form_loaisanpham: '产品类型',
        select_loaisanpham: '-- 选择产品类型 --',
        loaisanpham_sjt: '散件图',
        loaisanpham_wlj: '物料架',
        loaisanpham_zzc: '周转车',
        loaisanpham_gzt: '工作台',
        loaisanpham_wcp: '无尘棚',
        loaisanpham_lsx: '流水线',
        loaisanpham_zwj: '转弯机',
        loaisanpham_gzl: '改造类',
        loaisanpham_bsx: '倍速线',
        loaisanpham_wll: '围栏类',
        loaisanpham_gtx: '滚筒线',
        loaisanpham_zht: '展会图',
        loaisanpham_lhx: '老化线',
        form_kysu: '设计人员',
        form_tinhtrang: '完成状态',
        
        // Form fields - Time & Urgency
        form_capbach: '紧急程度',
        form_tg_mongmuon: '期望收到图纸时间',
        form_tg_hoanthanh: '计划完成时间',
        
        // Urgency options
        urgency_normal_option: '普通',
        urgency_urgent_option: '紧急',
        urgency_very_urgent_option: '非常紧急',
        
        // Quick actions
        quick_view: '查看详情',
        quick_edit: '编辑',
        quick_delete: '删除',
        quick_accept: '接受任务',
        
        // Toast messages
        toast_project_created: '创建项目成功',
        toast_project_updated: '更新项目成功',
        toast_project_deleted: '已删除 {count} 个项目',
        toast_export_success: '已导出{type}文件',
        toast_no_data_export: '没有可导出的数据',
        
        // Validation
        validation_khachhang_required: '请输入客户名称',
        validation_tensanpham_required: '请输入产品名称',
        validation_lienhe_required: 'Vui lòng nhập người liên hệ',
        validation_invalid_page: '请输入1到{max}之间的页码',
        
        // ============================================
        // NOTICES MODULE
        // ============================================
        notices_title: '通知',
        add_notice: '新建',
        edit_notice: '编辑',
        delete_notice: '删除',
        
        // Stats
        stat_total: '合计',
        stat_pending: '待审批',
        stat_accepted: '已接收',
        stat_urgent: '加急',
        auto_refresh_note: '每30秒自动刷新',
        no_notices: '暂无通知',
        
        // Status options
        status_pending_option: '待审批',
        status_accepted: '已接收',
        status_in_progress: '进行中',
        status_completed_option: '已完成',
        
        // Notice form
        form_sanpham: '产品',
        form_kysu_field: '工程师',
        form_dokhan: '紧急程度',
        form_trangthai: '状态',
        
        // Table headers
        notice_stt: '序号',
        notice_tracking_id: 'Tracking ID',
        notice_ngay: '日期',
        notice_khachhang: '客户',
        notice_sanpham: '产品',
        notice_soluong: '数量',
        notice_nhanvienkd: '业务员',
        notice_kysu: '工程师',
        notice_dokhan: '紧急程度',
        notice_trangthai: '状态',
        notice_actions: '操作',
        notice_select: '选择',
        
        // Quick actions
        notice_quick_accept: '接受任务',
        notice_quick_view: '查看详情',
        notice_quick_edit: '编辑',
        notice_quick_delete: '删除',
        
        // Form labels
        notice_form_ngay_khoitao: '创建日期',
        notice_form_khachhang: '客户公司名称',
        notice_form_khachhang_required: '客户 *',
        notice_form_nhanvienkd: '业务员',
        notice_form_tensanpham: '产品名称',
        notice_form_tensanpham_required: '产品名称 *',
        notice_form_soluong: '数量',
        notice_form_kysu: '工程师',
        notice_form_dokhan: '紧急程度',
        notice_form_trangthai: '状态',
        
        // Filter options
        notice_filter_status: '按状态筛选',
        notice_filter_urgency: '按紧急程度筛选',
        notice_all_status: '全部状态',
        notice_all_urgency: '全部紧急程度',
        
        // Empty state
        no_notices_found: '没有找到通知',
        
        // Actions
        accept_job: '接受任务',
        accept_job_confirm: '是否接受此任务？',
        accept_job_success: '已接受任务',
        
        // Toast messages
        toast_notice_created: '创建通知成功',
        toast_notice_updated: '更新通知成功',
        toast_notice_deleted: '已删除 {count} 条通知',
        toast_notice_accepted: '已接受任务',
        
        // Loading/Error messages
        loading_notices_data: '正在加载通知数据...',
        error_loading_notices: '加载通知出错',
        
        // Confirm messages
        confirm_accept_job: '是否接受此任务？',
        confirm_delete_notice: '确认删除',
        confirm_delete_notice_message: '确定要删除选中的 {count} 条通知吗？',
        
        // ============================================
        // PROFILE MODULE
        // ============================================
        profile_title: '个人信息',
        basic_info: '基本信息',
        contact_info: '联系方式',
        login_history: '登录历史',
        
        form_username: '用户名',
        form_role: '角色',
        form_fullname: '姓名',
        form_fullname_placeholder: '输入姓名',
        form_employee_id: '员工编号',
        form_employee_id_placeholder: '输入员工编号',
        form_department: '部门',
        form_department_placeholder: '输入部门',
        form_status: '状态',
        form_email: '邮箱',
        form_email_placeholder: '输入邮箱地址',
        form_phone: '电话',
        form_phone_placeholder: '输入电话号码',
        form_last_login: '最后登录',
        form_created_at: '账号创建时间',
        
        save_profile: '保存资料',
        change_password: '修改密码',
        refresh_profile: '刷新',
        
        // Password change
        password_change_title: '修改密码',
        current_password: '当前密码',
        new_password: '新密码',
        confirm_password: '确认新密码',
        confirm_password_btn: '确认',
        
        // Validation
        password_current_required: '请输入当前密码',
        password_new_required: '请输入新密码',
        password_confirm_required: '请确认新密码',
        password_not_match: '新密码不匹配',
        password_min_length: '新密码至少6位',
        
        // Error messages
        error_loading_profile: '无法加载个人信息',
        error_saving_profile: '无法保存个人信息',
        error_loading: '无法加载',
        error_saving: '无法保存',
        error_session_expired: '登录会话已过期',
        error_fill_all_fields: '请填写完整信息',
        
        // Toast messages
        toast_profile_saved: '保存资料成功！',
        toast_password_changed: '修改密码成功！',
        
        // ============================================
        // SUBMIT FEEDBACK
        // ============================================
        feedback_title: '提交反馈',
        feedback_type: '日志类型',
        feedback_type_general: '常规',
        feedback_type_error: '错误',
        feedback_type_debug: '调试',
        feedback_type_login: '登录',
        feedback_content: '反馈内容',
        feedback_content_placeholder: '请输入反馈内容...',
        feedback_submit: '提交反馈',
        
        // Toast messages
        toast_feedback_sent: '反馈已提交！',
        toast_feedback_error: '请输入反馈内容',
        feedback_content_required: '请输入反馈内容',
        feedback_error: '发生错误',
        
        // Toast show titles
        toast_success: '成功',
        toast_error: '错误',
        toast_warning: '警告',
        toast_info: '信息',
        exporting_data: '正在导出数据...',
        basic_info: '基本信息',
        technical_info: '技术信息',
        time_urgency: '时间与紧急程度',
        
        // ============================================
        // CREATE CODE (TAOMABANVE) MODULE
        // ============================================
        create_code_title: '图纸编码生成工具',
        requester_name: '申请人姓名',
        employee_code: '工程人员工号',
        three_digits: '3位数字',
        employee_code_hint: '输入工程人员3位工号（如：001, 002, 003）',
        category: '类别',
        select_category: '-- 选择类别 --',
        plan_code: '方案图号',
        plan_code_placeholder: '输入方案图号',
        search_history_placeholder: '搜索历史...',
        create_btn: '生成',
        confirm_create_code_title: '确认要生成此编码:',
        
        // Categories
        cat_sjt: 'SJT散件图 - 散件图',
        cat_wlj: 'WLJ物料架 - 物料架',
        cat_zzc: 'ZZC周转车 - 周转车',
        cat_gzt: 'GZT工作台 - 工作台',
        cat_wcp: 'WCP无尘棚 - 无尘棚',
        cat_lsx: 'LSX流水线 - 流水线',
        cat_zwj: 'ZWJ转弯机 - 转弯机 90,180',
        cat_gzl: 'GZL改造类 - 改造类',
        cat_bsx: 'BSX倍速线 - 倍速链',
        cat_wll: 'WLL围栏类 - 围栏',
        cat_gtx: 'GTX滚筒线 - 滚筒线',
        cat_zht: 'ZHT展会图 - 展会图',
        cat_lhx: 'LHX老化线 - 老化线',
        
        // History
        history_title: '生成历史',
        history: '生成历史',
        history_total: '合计',
        total: '合计',
        history_today: '今天',
        today: '今天',
        history_week: '本周',
        week: '本周',
        history_latest: '最新',
        latest: '最新',
        history_name: '姓名',
        name: '姓名',
        history_employee_code: '员工工号',
        employee_code_th: '员工工号',
        history_category: '类别',
        category_th: '类别',
        history_drawing_code: '图纸编码',
        drawing_code: '图纸编码',
        mother_code: '母料号',
        history_time: '时间',
        time: '时间',
        history_action: '操作',
        action: '操作',
        history_copy: '复制',
        history_delete: '删除',
        context_copy_code: '复制编码',
        context_delete_code: '删除编码',
        right_click_hint: '右键复制或删除编码',
        create_code: '生成图纸编码',
        
        // Delete code
        delete_code_title: '删除编码',
        delete_code_confirm: '请输入密码以删除编码 {code}:',
        delete_code_password: '密码',
        delete_code_wrong_password: '密码错误',
        delete_code_expired: '编码生成后仅允许在2小时内删除',
        
        // Toast messages
        toast_code_created: '已生成编码: ',
        toast_code_copy: '已复制到剪贴板',
        toast_code_deleted: '已删除编码 {code}',
        
        // Actions & Messages
        creating: '正在生成图纸代码...',
        creating_code: '正在生成编码...',
        deleting_code: '正在删除编码...',
        exporting_data: '正在导出数据...',
        
        // No history / Empty states
        no_history: '暂无创建历史',
        load_history_error: '加载历史出错: ',
        
        // Buttons
        copy_title: '复制',
        delete_title: '删除',
        
        // Excel export
        excel_sheet_name: '创建历史',
        excel_filename_prefix: 'code_history_',
        
        // Validation
        validation_employee_3digits: '员工工号必须为3位数字',
        validation_employee_not_zero: '员工工号不能为000',
        validation_name_required: '请输入申请人姓名',
        validation_category_required: '请选择类别',
        
        // Additional
        toast_warning: '警告',
        toast_no_data_export: '没有可导出的数据',
        toast_export_success: '已导出{type}文件',
        
        // Placeholders
        placeholder_name: '输入申请人姓名',
        placeholder_employee_code: '输入工程人员3位工号（如：001, 002, 003）',
        placeholder_employee_id: '输入员工编号',
        placeholder_search: '搜索...',
        placeholder_feedback: '请输入反馈内容...',
        
        // Button titles
        copy_title: '复制',
        delete_title: '删除',
        view_title: '查看',
        edit_title: '编辑',
        accept_job_title: '接受任务',
        
        // Relative time
        seconds_ago: '秒前',
        minutes_ago: '分钟前',
        hours_ago: '小时前',
        yesterday: '昨天',
        days_ago: '天前',
        
        // ============================================
        // AI MODULE (Placeholder)
        // ============================================
        ai_title: 'PropackAI',
        
        // ============================================
        // MISC
        // ============================================
        chars: '字符',
        use_system_account: '使用系统账号',
        
        // Loading states
        loading_projects: '正在加载项目数据...',
        loading_notices: '正在加载通知...',
        loading_taomabanve: '正在加载编码生成页面...',
        loading_profile: '正在加载个人信息...',
        loading_ai: '正在加载AI...'
    }
};

// ============================================
// i18n FUNCTIONS
// ============================================

/**
 * Get translation for a key
 * @param {string} key - Translation key
 * @param {object} params - Optional parameters for interpolation
 * @returns {string}
 */
function t(key, params = {}) {
    const lang = currentLanguage;
    let text = translations[lang]?.[key] || translations['vi'][key] || key;
    
    // Interpolate parameters
    Object.keys(params).forEach(param => {
        text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
    });
    
    return text;
}

/**
 * Change language
 * @param {string} lang - Language code ('vi' or 'zh')
 */
function changeLanguage(lang) {
    console.log('[i18n] changeLanguage called with:', lang);
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('language', lang);
        
        // Translate page content immediately
        translatePage();
        
        // Dispatch event for other modules to listen
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
    }
}

/**
 * Get current language
 * @returns {string}
 */
function getCurrentLanguage() {
    return currentLanguage;
}

/**
 * Translate all data-i18n elements in the page
 */
function translatePage() {
    console.log('[i18n] translatePage called');
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translated = t(key);
        if (element.tagName === 'INPUT') {
            element.placeholder = translated;
        } else {
            element.textContent = translated;
        }
    });
    
    // Translate placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = t(key);
    });
    
    // Translate title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        element.title = t(key);
    });
    
    // Translate select options with nested spans
    document.querySelectorAll('select option span[data-i18n]').forEach(span => {
        const key = span.getAttribute('data-i18n');
        const translated = t(key);
        span.textContent = translated;
    });
}

// Export to global scope
window.t = t;
window.changeLanguage = changeLanguage;
window.getCurrentLanguage = getCurrentLanguage;
window.translatePage = translatePage;
window.currentLanguage = currentLanguage;
