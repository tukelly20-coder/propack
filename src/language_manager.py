# Language Management Module for SOFFT Project Tracking
# Hỗ trợ Tiếng Việt (vi) và 中文 (zh)

import os


# Language configurations
LANGUAGE_FILE = "language.txt"
SUPPORTED_LANGUAGES = ['vi', 'zh']
DEFAULT_LANGUAGE = 'vi'


# Project headers in both languages
PROJECT_HEADERS = {
    'vi': [
        "Tracking ID",
        "Ngày khởi tạo",
        "Khách hàng",
        "Nhân viên kinh doanh",
        "Tên sản phẩm",
        "Quy cách",
        "Người liên hệ (KH)",
        "Số lượng",
        "Mã PO",
        "Mã bản vẽ phương án (mã trước khi đặt hàng)",
        "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)",
        "Mã thành phẩm (Mã mẹ)",
        "Hạng mục",
        "Kỹ sư thiết kế",
        "Tình trạng hoàn thành dự án",
        "Tính cấp bách",
        "Thời gian mong muốn có bản vẽ",
        "Thời gian hoàn thành kế hoạch"
    ],
    'zh': [
        "追踪编号",
        "日期",
        "客户",
        "业务员",
        "客户需求名称",
        "客户需求规格",
        "对接人",
        "数量",
        "PO号",
        "方案图号（下单前）",
        "工程图号（下单后）",
        "母料号",
        "产品类型",
        "设计者",
        "工程完成情况",
        "紧急程度",
        "期望出图时间",
        "方案完成时间"
    ]
}


# Key mapping for database fields (same for both languages)
PROJECT_KEYS = {
    'vi': {
        "Tracking ID": "Tracking ID",
        "Ngày khởi tạo": "Ngày",  # Map header "Ngày khởi tạo" sang key "Ngày" trong DB
        "Ngày": "Ngày",
        "Khách hàng": "Khách hàng",
        "Nhân viên kinh doanh": "Nhân viên kinh doanh",
        "Tên sản phẩm": "Tên sản phẩm",
        "Quy cách": "Quy cách",
        "Người liên hệ (KH)": "Người liên hệ\n(KH)",
        "Số lượng": "Số lượng",
        "Mã PO": "Mã PO",
        "Mã bản vẽ": "Mã bản vẽ",
        "Mã bản vẽ kỹ thuật": "Mã bản vẽ kỹ thuật (sau khi đặt hàng)",
        "Mã mẹ": "Mã mẹ",
        "Loại sản phẩm": "Loại sản phẩm",
        "Nhân viên thiết kế": "Nhân viên thiết kế",
        "Tình trạng hoàn thành dự án": "Tình trạng hoàn thành dự án",
        "Tính cấp bách": "Tính cấp bách",
        "Thời gian mong muốn có bản vẽ": "Thời gian mong muốn có bản vẽ",
        "Thời gian hoàn thành kế hoạch": "Thời gian hoàn thành kế hoạch"
    },
    'zh': {
        "追踪编号": "Tracking ID",
        "日期": "Ngày",  # Map "日期" sang "Ngày" trong DB (khóa gốc)
        "客户": "Khách hàng",
        "业务员": "Nhân viên kinh doanh",
        "客户需求名称": "Tên sản phẩm",
        "客户需求规格": "Quy cách",
        "对接人": "Người liên hệ\n(KH)",
        "数量": "Số lượng",
        "PO号": "Mã PO",
        "方案图号（下单前）": "Mã bản vẽ",
        "工程图号（下单后）": "Mã bản vẽ kỹ thuật (sau khi đặt hàng)",
        "母料号": "Mã mẹ",
        "产品类型": "Loại sản phẩm",
        "设计者": "Nhân viên thiết kế",
        "工程完成情况": "Tình trạng hoàn thành dự án",
        "紧急程度": "Tính cấp bách",
        "期望出图时间": "Thời gian mong muốn có bản vẽ",
        "方案完成时间": "Thời gian hoàn thành kế hoạch"
    }
}


# UI Text translations
UI_TEXT = {
    'vi': {
        # Window titles
        "window_title": "Quản Lý Dự Án - SQLite",
        
        # Menu items
        "menu_file": "File",
        "menu_edit": "Edit",
        "menu_columns": "Setting",
        "menu_filter": "Lọc dữ liệu",
        "menu_help": "Help",
        
        # Column settings
        "action_column_settings": "Cài đặt cột...",
        "dialog_column_settings": "选择显示列",
        "select_all": "全选",
        "deselect_all": "取消全选",
        
        # File menu
        "action_save": "Lưu",
        "action_save_shortcut": "Ctrl+S",
        "action_export_excel": "Xuất Excel",
        "action_export_csv": "Xuất CSV",
        "action_exit": "Thoát",
        
        # Edit menu
        "action_add": "Thêm mới",
        "action_add_shortcut": "Ctrl+N",
        "action_edit": "Chỉnh sửa",
        "action_edit_shortcut": "Ctrl+E",
        "action_delete": "Xóa",
        "action_delete_shortcut": "Delete",
        "action_refresh": "Làm mới",
        
        # Help menu
        "action_about": "Về ứng dụng",
        
        # Filter menu
        "action_filter_help": "Hướng dẫn lọc...",
        "action_clear_filter": "Xóa tất cả bộ lọc",
        "action_filter_this": "🔍 Lọc giá trị này",
        "filter_dialog_title": "Hướng dẫn lọc dữ liệu",
        "filter_dialog_message": "Để lọc dữ liệu theo cột, hãy CLICK VÀO TÊN CỘT (header) trên bảng.\n\nMột hộp thoại sẽ hiện ra cho phép bạn chọn các giá trị muốn hiển thị.",
        "filter_count": "Đã chọn: {} / {}",
        "filter_total": "Tổng số giá trị: {}",
        "sort_asc": "↑ Tăng dần (A→Z)",
        "sort_desc": "↓ Giảm dần (Z→A)",
        
        # Toolbar
        "toolbar_add": "Thêm",
        "toolbar_edit": "Sửa",
        "toolbar_delete": "Xóa",
        "toolbar_save": "Lưu",
        "toolbar_search": "Tìm",
        "toolbar_refresh": "Làm mới",
        "toolbar_export_excel": "Xuất Excel",
        "toolbar_export_csv": "Xuất CSV",
        
        # Search
        "search_label": "Tìm kiếm:",
        "search_placeholder": "Nhập từ khóa tìm kiếm...",
        "search_btn": "Tìm",
        "search_advanced_btn": "Tìm kiếm nâng cao",
        "refresh_btn": "Làm mới",
        
        # Search Dialog
        "search_dialog_title": "Tìm kiếm lịch sử",
        "search_columns_label": "Tìm trong các cột:",
        "search_results_label": "Tìm thấy: {} kết quả",
        "search_results_count": "Tìm thấy: {} / {}",
        "search_select_all": "Chọn tất cả",
        "search_clear_all": "Bỏ chọn tất cả",
        "search_no_results": "Không tìm thấy kết quả",
        "select_all_tooltip": "Chọn tất cả cột",
        "clear_all_tooltip": "Bỏ chọn tất cả",
        "no_search_results": "Không có kết quả nào phù hợp",
        
        # Pagination
        "page_label": "Trang:",
        "page_size_label": "Số dòng:",
        "total_records": "Tổng: {} bản ghi",
        "page_info": "Hiển thị trang {}/{} - {} bản ghi",
        
        # Dialogs
        "dialog_add_title": "Thêm mới",
        "dialog_edit_title": "Chỉnh sửa",
        "dialog_view_title": "Xem chi tiết",
        "dialog_update_status_title": "Cập nhật tình trạng",
        "dialog_confirm_delete": "Xác nhận xóa",
        "dialog_confirm_delete_msg": "Bạn có chắc chắn muốn xóa {} bản ghi đã chọn?",
        "dialog_save_changes": "Lưu thay đổi",
        "dialog_save_changes_msg": "Bạn có muốn lưu các thay đổi không?",
        
        # View dialog
        "view_btn_update": "Cập nhật",
        "msg_update_success": "Đã cập nhật tình trạng",
        "progress_info_tab": "Thông tin tiến độ",
        
        # Messages
        "msg_select_record": "Vui lòng chọn một bản ghi để chỉnh sửa",
        "msg_select_one_record": "Vui lòng chỉ chọn một bản ghi để chỉnh sửa",
        "msg_select_delete": "Vui lòng chọn ít nhất một bản ghi để xóa",
        "msg_add_success": "Đã thêm bản ghi mới",
        "msg_edit_success": "Đã cập nhật bản ghi",
        "msg_delete_success": "Đã xóa {} bản ghi",
        "msg_save_success": "Đã lưu dữ liệu vào SQLite",
        "msg_file_not_found": "Không tìm thấy database",
        "msg_file_invalid": "Database không hợp lệ",
        "msg_load_success": "Đã tải {} bản ghi từ database",
        "msg_data_refreshed": "Đã làm mới dữ liệu - {} bản ghi",
        
        # Errors
        "error_read_file": "Có lỗi xảy ra khi đọc file: {}",
        "error_save_file": "Có lỗi xảy ra khi lưu file: {}",
        "error_export_csv": "Có lỗi xảy ra khi xuất CSV: {}",
        "error_export_excel": "Có lỗi xảy ra khi xuất Excel: {}",
        
        # About
        "about_title": "Về ứng dụng",
        "about_text": "Quản Lý Dự Án - SQLite\n\n"
                    "Ứng dụng quản lý dữ liệu dự án\n"
                    "Sử dụng PySide6\n\n"
                    "Phím tắt:\n"
                    "- Ctrl+N: Thêm mới\n"
                    "- Ctrl+E: Chỉnh sửa\n"
                    "- Delete: Xóa\n"
                    "- F5: Làm mới dữ liệu",
        
        # New Sales Dialog
        "new_sales_title": "Tạo Yêu Cầu Project Mới",
        "new_sales_title_label": "THÔNG TIN YÊU CẦU PROJECT",
        "new_sales_basic_section": "THÔNG TIN CƠ BẢN",
        "new_sales_customer_section": "THÔNG TIN KHÁCH HÀNG",
        "new_sales_project_section": "THÔNG TIN SẢN PHẨM",
        "new_sales_urgency_section": "ĐỘ KHẨN CẤP",
        "new_sales_tracking_id": "Tracking ID:",
        "new_sales_created_date": "Ngày khởi tạo:",
        "new_sales_sales_name": "Tên nhân viên:",
        "new_sales_customer": "Tên khách hàng:",
        "new_sales_product_name": "Tên sản phẩm:",
        "new_sales_specs": "Quy cách:",
        "new_sales_contact": "Người liên hệ:",
        "new_sales_urgency": "Tính cấp bách:",
        "new_sales_desired_time": "Thời gian mong muốn có phương án:",
        "new_sales_urgency_normal": "Bình thường",
        "new_sales_urgency_urgent": "Khẩn cấp",
        "new_sales_urgency_very_urgent": "Rất khẩn cấp",
        "new_sales_btn_save": "Lưu",
        "new_sales_btn_cancel": "Hủy",
        "new_sales_btn_saving": "Đang lưu...",
        "new_sales_placeholder_customer": "Nhập tên khách hàng",
        "new_sales_placeholder_product": "Nhập tên sản phẩm do khách hàng đặt",
        "new_sales_placeholder_specs": "Nhập quy cách sản phẩm",
        "new_sales_placeholder_contact": "Nhập tên người liên hệ",
        "new_sales_warning": "Cảnh báo",
        "new_sales_success": "Thành công",
        "new_sales_error": "Lỗi",
        "new_sales_conn_error": "Lỗi kết nối: {}",
        "new_sales_save_success": "Đã tạo yêu cầu thành công!\nTracking ID: {}",
        "new_sales_save_failed": "Không thể lưu: {}",
        "new_sales_validate_customer": "Vui lòng nhập tên khách hàng",
        "new_sales_validate_product": "Vui lòng nhập tên sản phẩm",
        "new_sales_validate_contact": "Vui lòng nhập người liên hệ",
        "new_sales_so_luong": "Số lượng:",
        "new_sales_placeholder_so_luong": "Nhập số lượng",
        
        # Notice Tab
        "notice_tab_title": "THÔNG BÁO",
        "notice_status_filter": "📊 Trạng thái:",
        "notice_filter_all": "Tất cả",
        "notice_filter_pending": "Chờ nhận",
        "notice_filter_accepted": "Đã nhận",
        "notice_filter_mine": "Của tôi",
        "notice_urgency_filter": "⚡ Độ khẩn:",
        "notice_urgency_all": "Tất cả",
        "notice_urgency_normal": "Bình thường",
        "notice_urgency_urgent": "Khẩn cấp",
        "notice_urgency_very_urgent": "Rất khẩn",
        "notice_search_label": "🔍 Tìm kiếm:",
        "notice_search_placeholder": "Sản phẩm, Tracking ID, Nhân viên...",
        "notice_auto_refresh": "🔄 Auto-refresh (30s)",
        "notice_btn_refresh": "🔄 Làm mới",
        "notice_btn_view": "Xem chi tiết",
        "notice_btn_accept": "Nhận Job",
        "notice_btn_close": "❌ Đóng",
        "notice_details_title": "📝 Chi tiết",
        "notice_header_tracking_id": "Tracking ID",
        "notice_header_customer": "Khách hàng",
        "notice_header_product": "Sản phẩm",
        "notice_header_date": "Ngày tạo",
        "notice_header_urgency": "Độ khẩn",
        "notice_header_status": "Trạng thái",
        "notice_header_accepted_by": "Người nhận",
        "notice_info_sales": "Sales chỉ thấy yêu cầu của mình. Engineer thấy tất cả yêu cầu chờ.",
        "notice_loading": "⏳ Đang tải dữ liệu...",
        "notice_no_requests": "✅ Không có yêu cầu nào đang chờ.\nTạo yêu cầu mới từ tab Dự án.",
        "notice_total_requests": "📊 Tổng số yêu cầu: {}",
        "notice_info_double_click": "Double-click vào dòng để xem chi tiết. Click 'Nhận Job' để nhận công việc.",
        "notice_error_title": "Lỗi",
        "notice_load_error": "Không thể tải thông báo: {}",
        "notice_status_pending": "⏳ Chờ nhận",
        "notice_status_accepted": "✅ Đã nhận",
        "notice_urgency_normal_display": "🟢 Bình thường",
        "notice_urgency_urgent_display": "🟡 Khẩn cấp",
        "notice_urgency_very_urgent_display": "🔴 Rất khẩn",
        "notice_confirm_accept": "Xác nhận nhận job",
        "notice_confirm_accept_msg": "Bạn có chắc muốn nhận job này không?\n\nTracking ID: {}\nKhách hàng: {}",
        "notice_select_to_view": "Vui lòng chọn một yêu cầu để xem.",
        "notice_select_to_accept": "Vui lòng chọn một yêu cầu để nhận.",
        "notice_already_accepted": "Job này đã được nhận trước đó.",
        "notice_cannot_identify_engineer": "Không thể xác định tên engineer.",
        "notice_accept_success": "✅ Đã nhận job thành công!\n\nTracking ID: {}\nNgười nhận: {}",
        "notice_accept_error": "Không thể nhận job: {}",
        "notice_connection_error": "Lỗi kết nối: {}",
        "notice_details_tracking_id": "Tracking ID:",
        "notice_details_created_date": "Ngày tạo:",
        "notice_details_customer_info": "👤 THÔNG TIN KHÁCH HÀNG",
        "notice_details_customer_name": "Tên khách hàng:",
        "notice_details_contact": "Người liên hệ:",
        "notice_details_product_info": "📦 THÔNG TIN SẢN PHẨM",
        "notice_details_product_name": "Tên sản phẩm:",
        "notice_details_specs": "Quy cách:",
        "notice_details_time_info": "⏰ THỜI GIAN",
        "notice_details_urgency": "Độ khẩn:",
        "notice_details_desired_time": "Thời gian mong muốn:",
        "notice_details_sales_info": "👨‍💼 NHÂN VIÊN TẠO",
        "notice_details_sales_name": "Tên:",
        "notice_details_status_info": "📊 TRẠNG THÁI",
        "notice_details_status": "Trạng thái:",
        "notice_details_accepted_by": "Người nhận:",
        "notice_details_accepted_at": "Thời gian nhận:",
        "notice_role_sales": "Sales",
        "notice_role_engineer": "Engineer",
        "notice_role_admin": "Admin",
        "notice_role_it": "IT",
        "notice_role_pur": "Pur",
        "notice_user_info": "👤 User: {} | 🎯 Role: {}",
        
        # View Dialog tabs
        "view_tab_basic": "📋 Cơ bản",
        "view_tab_product": "📦 Sản phẩm",
        "view_tab_drawing": "📐 Bản vẽ",
        "view_tab_progress": "⏱️ Tiến độ",
        "view_tab_metadata": "🔧 Metadata",
        
        # View Dialog labels
        "view_label_tracking_id": "Tracking ID:",
        "view_label_date": "Ngày khởi tạo:",
        "view_label_customer": "Khách hàng:",
        "view_label_sales": "Nhân viên kinh doanh:",
        "view_label_contact": "Người liên hệ (KH):",
        "view_label_po": "Mã PO:",
        "view_label_product_name": "Tên sản phẩm:",
        "view_label_specs": "Quy cách:",
        "view_label_quantity": "Số lượng:",
        "view_label_product_type": "Loại sản phẩm:",
        "view_label_drawing_code": "Mã bản vẽ (phương án):",
        "view_label_drawing_code_tech": "Mã bản vẽ kỹ thuật:",
        "view_label_mother_code": "Mã mẹ:",
        "view_label_designer": "Nhân viên thiết kế:",
        "view_label_urgency": "Tính cấp bách:",
        "view_label_receive_time": "Thời gian tiếp nhận:",
        "view_label_desired_time": "Thời gian mong muốn:",
        "view_label_complete_time": "Thời gian hoàn thành:",
        "view_label_completion_status": "Tình trạng hoàn thành:",
        "view_label_user_id": "User ID:",
        "view_label_pending_status": "Trạng thái chờ:",
        "view_label_accepted_by": "Người nhận:",
        "view_label_accepted_at": "Thời gian nhận:",
        "view_label_urgency_level": "Mức độ khẩn cấp:"
    },
    'zh': {
        # Window titles
        "window_title": "项目管理 - SQLite",
        
        # Menu items
        "menu_file": "文件",
        "menu_edit": "编辑",
        "menu_columns": "栏目设置",
        "menu_filter": "筛选数据",
        "menu_help": "帮助",
        
        # Column settings
        "action_column_settings": "列设置...",
        "dialog_column_settings": "选择显示列",
        "select_all": "全选",
        "deselect_all": "取消全选",
        
        # File menu
        "action_save": "保存",
        "action_save_shortcut": "Ctrl+S",
        "action_export_excel": "导出Excel",
        "action_export_csv": "导出CSV",
        "action_exit": "退出",
        
        # Edit menu
        "action_add": "新建",
        "action_add_shortcut": "Ctrl+N",
        "action_edit": "编辑",
        "action_edit_shortcut": "Ctrl+E",
        "action_delete": "删除",
        "action_delete_shortcut": "Delete",
        "action_refresh": "刷新",
        
        # Help menu
        "action_about": "关于",
        
        # Filter menu
        "action_filter_help": "筛选说明...",
        "action_clear_filter": "清除所有筛选",
        "action_filter_this": "🔍 筛选此值",
        "filter_dialog_title": "筛选数据说明",
        "filter_dialog_message": "要按列筛选数据，请点击表格上的列标题（header）。\n\n将弹出一个对话框，允许您选择要显示的值。",
        "filter_count": "已选择: {} / {}",
        "filter_total": "总数值: {}",
        "sort_asc": "↑ 升序 (A→Z)",
        "sort_desc": "↓ 降序 (Z→A)",
        
        # Toolbar
        "toolbar_add": "新建",
        "toolbar_edit": "编辑",
        "toolbar_delete": "删除",
        "toolbar_save": "保存",
        "toolbar_search": "搜索",
        "toolbar_refresh": "刷新",
        "toolbar_export_excel": "导出Excel",
        "toolbar_export_csv": "导出CSV",
        
        # Search
        "search_label": "搜索:",
        "search_placeholder": "输入关键词搜索...",
        "search_btn": "搜索",
        "search_advanced_btn": "高级搜索",
        "refresh_btn": "刷新",
        
        # Search Dialog
        "search_dialog_title": "搜索历史记录",
        "search_columns_label": "搜索列：",
        "search_results_label": "找到：{} 条结果",
        "search_results_count": "找到: {} / {}",
        "search_select_all": "全选",
        "search_clear_all": "取消全选",
        "search_no_results": "未找到结果",
        "select_all_tooltip": "选择所有列",
        "clear_all_tooltip": "取消所有选择",
        "no_search_results": "未找到结果",
        
        # Pagination
        "page_label": "页:",
        "page_size_label": "每页行数:",
        "total_records": "总计: {} 条记录",
        "page_info": "显示第{}/{}页 - {} 条记录",
        
        # Dialogs
        "dialog_add_title": "新建",
        "dialog_edit_title": "编辑",
        "dialog_view_title": "查看详情",
        "dialog_update_status_title": "更新状态",
        "dialog_confirm_delete": "确认删除",
        "dialog_confirm_delete_msg": "您确定要删除选中的 {} 条记录吗?",
        "dialog_save_changes": "保存更改",
        "dialog_save_changes_msg": "您要保存更改吗?",
        
        # View dialog
        "view_btn_update": "更新",
        "msg_update_success": "已更新状态",
        "progress_info_tab": "进度信息",
        
        # Messages
        "msg_select_record": "请选择一条记录进行编辑",
        "msg_select_one_record": "请仅选择一条记录进行编辑",
        "msg_select_delete": "请至少选择一条记录进行删除",
        "msg_add_success": "已添加新记录",
        "msg_edit_success": "已更新记录",
        "msg_delete_success": "已删除 {} 条记录",
        "msg_save_success": "已将数据保存到 SQLite",
        "msg_file_not_found": "找不到数据库文件",
        "msg_file_invalid": "数据库文件无效",
        "msg_load_success": "已从数据库加载 {} 条记录",
        "msg_data_refreshed": "已刷新数据 - {} 条记录",
        
        # Errors
        "error_read_file": "读取文件时出错: {}",
        "error_save_file": "保存文件时出错: {}",
        "error_export_csv": "导出CSV时出错: {}",
        "error_export_excel": "导出Excel时出错: {}",
        
        # About
        "about_title": "关于",
        "about_text": "项目管理 - SQLite\n\n"
                    "项目管理应用程序\n"
                    "使用 PySide6\n\n"
                    "快捷键:\n"
                    "- Ctrl+N: 新建\n"
                    "- Ctrl+E: 编辑\n"
                    "- Delete: 删除\n"
                    "- F5: 刷新数据",
        
        # New Sales Dialog
        "new_sales_title": "创建新项目请求",
        "new_sales_title_label": "项目请求信息",
        "new_sales_basic_section": "基本信息",
        "new_sales_customer_section": "客户信息",
        "new_sales_project_section": "产品信息",
        "new_sales_urgency_section": "紧急程度",
        "new_sales_tracking_id": "追踪编号:",
        "new_sales_created_date": "创建日期:",
        "new_sales_sales_name": "员工姓名:",
        "new_sales_customer": "客户名称:",
        "new_sales_product_name": "产品名称:",
        "new_sales_specs": "规格:",
        "new_sales_contact": "联系人:",
        "new_sales_urgency": "紧急程度:",
        "new_sales_desired_time": "期望方案时间:",
        "new_sales_urgency_normal": "正常",
        "new_sales_urgency_urgent": "紧急",
        "new_sales_urgency_very_urgent": "非常紧急",
        "new_sales_btn_save": "保存",
        "new_sales_btn_cancel": "取消",
        "new_sales_btn_saving": "保存中...",
        "new_sales_placeholder_customer": "输入客户名称",
        "new_sales_placeholder_product": "输入客户需求产品名称",
        "new_sales_placeholder_specs": "输入产品规格",
        "new_sales_placeholder_contact": "输入联系人姓名",
        "new_sales_warning": "警告",
        "new_sales_success": "成功",
        "new_sales_error": "错误",
        "new_sales_conn_error": "连接错误: {}",
        "new_sales_save_success": "已成功创建请求!\n追踪编号: {}",
        "new_sales_save_failed": "无法保存: {}",
        "new_sales_validate_customer": "请输入客户名称",
        "new_sales_validate_product": "请输入产品名称",
        "new_sales_validate_contact": "请输入联系人",
        "new_sales_so_luong": "数量:",
        "new_sales_placeholder_so_luong": "输入数量",
        
        # Notice Tab
        "notice_tab_title": "待处理通知",
        "notice_status_filter": "📊 状态:",
        "notice_filter_all": "全部",
        "notice_filter_pending": "等待接受",
        "notice_filter_accepted": "已接受",
        "notice_filter_mine": "我的",
        "notice_urgency_filter": "⚡ 紧急程度:",
        "notice_urgency_all": "全部",
        "notice_urgency_normal": "正常",
        "notice_urgency_urgent": "紧急",
        "notice_urgency_very_urgent": "非常紧急",
        "notice_search_label": "🔍 搜索:",
        "notice_search_placeholder": "产品, Tracking ID, 员工...",
        "notice_auto_refresh": "🔄 自动刷新 (30秒)",
        "notice_btn_refresh": "🔄 刷新",
        "notice_btn_view": "查看详情",
        "notice_btn_accept": "接受任务",
        "notice_btn_close": "❌ 关闭",
        "notice_details_title": "📝 详情",
        "notice_header_tracking_id": "追踪编号",
        "notice_header_customer": "客户",
        "notice_header_product": "产品",
        "notice_header_date": "创建日期",
        "notice_header_urgency": "紧急程度",
        "notice_header_status": "状态",
        "notice_header_accepted_by": "接收人",
        "notice_info_sales": "Sales只能看到自己的请求。工程师可以看到所有待处理请求。",
        "notice_loading": "⏳ 加载数据中...",
        "notice_no_requests": "✅ 没有待处理的请求。\n请从项目标签创建新请求。",
        "notice_total_requests": "📊 总请求数: {}",
        "notice_info_double_click": "双击行查看详情。点击'接受任务'接收工作。",
        "notice_error_title": "错误",
        "notice_load_error": "无法加载通知: {}",
        "notice_status_pending": "⏳ 等待接受",
        "notice_status_accepted": "✅ 已接受",
        "notice_urgency_normal_display": "🟢 正常",
        "notice_urgency_urgent_display": "🟡 紧急",
        "notice_urgency_very_urgent_display": "🔴 非常紧急",
        "notice_confirm_accept": "确认接受任务",
        "notice_confirm_accept_msg": "您确定要接受此任务吗？\n\n追踪编号: {}\n客户: {}",
        "notice_select_to_view": "请选择一条请求查看。",
        "notice_select_to_accept": "请选择一条请求接受。",
        "notice_already_accepted": "此任务已被接受。",
        "notice_cannot_identify_engineer": "无法确定工程师姓名。",
        "notice_accept_success": "✅ 已成功接受任务！\n\n追踪编号: {}\n接收人: {}",
        "notice_accept_error": "无法接受任务: {}",
        "notice_connection_error": "连接错误: {}",
        "notice_details_tracking_id": "追踪编号:",
        "notice_details_created_date": "创建日期:",
        "notice_details_customer_info": "👤 客户信息",
        "notice_details_customer_name": "客户名称:",
        "notice_details_contact": "联系人:",
        "notice_details_product_info": "📦 产品信息",
        "notice_details_product_name": "产品名称:",
        "notice_details_specs": "规格:",
        "notice_details_time_info": "⏰ 时间信息",
        "notice_details_urgency": "紧急程度:",
        "notice_details_desired_time": ":",
        "notice_details_sales_info": "👨‍💼 创建员工",
        "notice_details_sales_name": "姓名:",
        "notice_details_status_info": "📊 状态",
        "notice_details_status": "状态:",
        "notice_details_accepted_by": "接收人:",
        "notice_details_accepted_at": "接收时间:",
        "notice_role_sales": "Sales",
        "notice_role_engineer": "工程师",
        "notice_role_admin": "管理员",
        "notice_role_it": "IT",
        "notice_role_pur": "采购",
        "notice_user_info": "👤 用户: {} | 🎯 角色: {}",
        
        # View Dialog tabs
        "view_tab_basic": "📋 基本信息",
        "view_tab_product": "📦 产品",
        "view_tab_drawing": "📐 图纸",
        "view_tab_progress": "⏱️ 进度",
        "view_tab_metadata": "🔧 元数据",
        
        # View Dialog labels
        "view_label_tracking_id": "追踪编号:",
        "view_label_date": "创建日期:",
        "view_label_customer": "客户:",
        "view_label_sales": "业务员:",
        "view_label_contact": "对接人:",
        "view_label_po": "PO号:",
        "view_label_product_name": "产品名称:",
        "view_label_specs": "规格:",
        "view_label_quantity": "数量:",
        "view_label_product_type": "产品类型:",
        "view_label_drawing_code": "方案图号:",
        "view_label_drawing_code_tech": "工程图号:",
        "view_label_mother_code": "母料号:",
        "view_label_designer": "设计者:",
        "view_label_urgency": "紧急程度:",
        "view_label_receive_time": "接收时间:",
        "view_label_desired_time": "期望时间:",
        "view_label_complete_time": "完成时间:",
        "view_label_completion_status": "完成情况:",
        "view_label_user_id": "用户ID:",
        "view_label_pending_status": "等待状态:",
        "view_label_accepted_by": "接收人:",
        "view_label_accepted_at": "接收时间:",
        "view_label_urgency_level": "紧急程度:"
    }
}


# EditDialog field definitions
# Widget types: spinbox_readonly, datetime, combobox_editable, number, combobox, text
DIALOG_FIELDS = {
    'vi': [
        ("Tracking ID", "Tracking ID", "spinbox_readonly"),
        ("Ngày", "Ngày", "datetime"),
        ("Khách hàng", "Khách hàng", "combobox_editable"),
        ("Nhân viên kinh doanh", "Nhân viên kinh doanh", "combobox_editable"),
        ("Tên sản phẩm", "Tên sản phẩm", "combobox_editable"),
        ("Quy cách", "Quy cách", "combobox_editable"),
        ("Người liên hệ (KH)", "Người liên hệ\n(KH)", "text"),
        ("Số lượng", "Số lượng", "number"),
        ("Mã PO", "Mã PO", "text"),
        ("Mã bản vẽ", "Mã bản vẽ", "text"),
        ("Mã bản vẽ kỹ thuật", "Mã bản vẽ kỹ thuật (sau khi đặt hàng)", "text"),
        ("Mã mẹ", "Mã mẹ", "text"),
        ("Loại sản phẩm", "Loại sản phẩm", "combobox_editable"),
        ("Nhân viên thiết kế", "Nhân viên thiết kế", "combobox_editable"),
        ("Tình trạng hoàn thành dự án", "Tình trạng hoàn thành dự án", "combobox_editable"),
        ("Tính cấp bách", "Tính cấp bách", "combobox"),
        ("Thời gian mong muốn có bản vẽ", "Thời gian mong muốn có bản vẽ", "datetime"),
        ("Thời gian hoàn thành kế hoạch", "Thời gian hoàn thành kế hoạch", "datetime"),
    ],
    'zh': [
        ("追踪编号", "Tracking ID", "spinbox_readonly"),
        ("日期", "Ngày", "datetime"), 
        ("客户", "Khách hàng", "combobox_editable"),
        ("业务员", "Nhân viên kinh doanh", "combobox_editable"),
        ("客户需求名称", "Tên sản phẩm", "combobox_editable"),
        ("客户需求规格", "Quy cách", "combobox_editable"),
        ("对接人", "Người liên hệ\n(KH)", "text"),
        ("数量", "Số lượng", "number"),
        ("PO号", "Mã PO", "text"),
        ("方案图号（下单前）", "Mã bản vẽ", "text"),
        ("工程图号（下单后）", "Mã bản vẽ kỹ thuật (sau khi đặt hàng)", "text"),
        ("母料号", "Mã mẹ", "text"),
        ("产品类型", "Loại sản phẩm", "combobox_editable"),
        ("设计者", "Nhân viên thiết kế", "combobox_editable"),
        ("工程完成情况", "Tình trạng hoàn thành dự án", "combobox_editable"),
        ("紧急程度", "Tính cấp bách", "combobox"),
        ("期望出图时间", "Thời gian mong muốn có bản vẽ", "date"),
        ("方案完成时间", "Thời gian hoàn thành kế hoạch", "date"),
    ]
}


# Urgency levels for "Tính cấp bách" / "紧急程度"
# Sử dụng giá trị tiếng Anh làm key để lưu vào DB
URGENCY_LEVELS = {
    'vi': [
        ("normal", "Bình thường"),
        ("urgent", "Khẩn cấp"),
        ("very_urgent", "Rất khẩn cấp"),
        ("paused", "Tạm dừng"),
        ("completed", "Hoàn thành"),
    ],
    'zh': [
        ("normal", "正常"),
        ("urgent", "紧急"),
        ("very_urgent", "非常紧急"),
        ("paused", "暂停"),
        ("completed", "结束"),
    ]
}


# Metadata headers - Các cột metadata từ database
METADATA_HEADERS = {
    'vi': [
        "User ID",
        "Trạng thái chờ",
        "Người nhận",
        "Thời gian nhận",
        "Mức độ khẩn cấp"
    ],
    'zh': [
        "ID",
        "等待状态",
        "接收人",
        "接收时间",
        "紧急程度"
    ]
}

# Metadata key mapping - Mapping từ display header sang database key
METADATA_KEYS = {
    'vi': {
        "User ID": "user_id",
        "Trạng thái chờ": "is_pending",
        "Người nhận": "accepted_by",
        "Thời gian nhận": "accepted_at",
        "Mức độ khẩn cấp": "urgency_level"
    },
    'zh': {
        "ID": "user_id",
        "等待状态": "is_pending",
        "接收人": "accepted_by",
        "接收时间": "accepted_at",
        "紧急程度": "urgency_level"
    }
}


class LanguageManager:
    """Quản lý ngôn ngữ cho ứng dụng"""
    
    def __init__(self):
        self.current_language = self.load_language()
    
    def load_language(self):
        """Đọc ngôn ngữ từ file language.txt"""
        try:
            if os.path.exists(LANGUAGE_FILE):
                with open(LANGUAGE_FILE, 'r', encoding='utf-8') as f:
                    lang = f.read().strip().lower()
                    if lang in SUPPORTED_LANGUAGES:
                        return lang
            return DEFAULT_LANGUAGE
        except Exception:
            return DEFAULT_LANGUAGE
    
    def get_language(self):
        """Lấy ngôn ngữ hiện tại"""
        return self.current_language
    
    def get_headers(self):
        """Lấy headers theo ngôn ngữ hiện tại"""
        return PROJECT_HEADERS.get(self.current_language, PROJECT_HEADERS[DEFAULT_LANGUAGE])
    
    def get_keys(self):
        """Lấy key mapping theo ngôn ngữ hiện tại"""
        return PROJECT_KEYS.get(self.current_language, PROJECT_KEYS[DEFAULT_LANGUAGE])
    
    def get_ui_text(self, key):
        """Lấy text UI theo ngôn ngữ hiện tại"""
        return UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE]).get(key, "")
    
    def get_dialog_fields(self):
        """Lấy field definitions cho dialog theo ngôn ngữ hiện tại"""
        return DIALOG_FIELDS.get(self.current_language, DIALOG_FIELDS[DEFAULT_LANGUAGE])
    
    def get_all_ui_texts(self):
        """Lấy tất cả texts UI theo ngôn ngữ hiện tại"""
        return UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE])
    
    def get_urgency_levels(self):
        """Lấy danh sách các mức độ khẩn cấp theo ngôn ngữ hiện tại"""
        return URGENCY_LEVELS.get(self.current_language, URGENCY_LEVELS[DEFAULT_LANGUAGE])
    
    def get_urgency_level_display(self, english_value):
        """
        Chuyển đổi giá trị urgency_level từ tiếng Anh sang ngôn ngữ hiện tại để hiển thị
        Ví dụ: 'normal' -> 'Bình thường' (vi) hoặc '正常' (zh)
        """
        if not english_value:
            return ""
        
        urgency_levels = self.get_urgency_levels()
        for key, display in urgency_levels:
            if key == english_value:
                return display
        
        # Nếu không tìm thấy, trả về giá trị gốc
        return english_value
    
    def get_urgency_level_key(self, display_value):
        """
        Chuyển đổi giá trị hiển thị sang key tiếng Anh để lưu vào DB
        Ví dụ: 'Bình thường' (vi) -> 'normal' hoặc '正常' (zh) -> 'normal'
        """
        if not display_value:
            return ""
        
        urgency_levels = self.get_urgency_levels()
        for key, display in urgency_levels:
            if display == display_value:
                return key
        
        # Nếu không tìm thấy, thử tìm theo direct comparison
        # (hỗ trợ trường hợp data cũ lưu trực tiếp text)
        for key, display in urgency_levels:
            if key == display_value or display == display_value:
                return key
        
        # Nếu vẫn không tìm thấy, kiểm tra mapping cứng
        if display_value in ['Bình thường', '正常', 'normal']:
            return 'normal'
        elif display_value in ['Khẩn cấp', '紧急', 'urgent']:
            return 'urgent'
        elif display_value in ['Rất khẩn cấp', '非常紧急', 'very_urgent']:
            return 'very_urgent'
        elif display_value in ['Tạm dừng', '暂停', 'paused']:
            return 'paused'
        elif display_value in ['Hoàn thành', '结束', 'completed']:
            return 'completed'
        
        return display_value
    
    def get_new_sales_text(self, key):
        """Lấy text cho NewSalesDialog theo ngôn ngữ hiện tại"""
        texts = UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE])
        return texts.get(f"new_sales_{key}", "")
    
    def get_all_new_sales_texts(self):
        """Lấy tất cả texts cho NewSalesDialog theo ngôn ngữ hiện tại"""
        texts = UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE])
        return {
            k: v for k, v in texts.items() 
            if k.startswith('new_sales_')
        }
    
    def get_notice_tab_text(self, key):
        """Lấy text cho NoticeTab theo ngôn ngữ hiện tại"""
        texts = UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE])
        return texts.get(f"notice_{key}", "")
    
    def get_all_notice_tab_texts(self):
        """Lấy tất cả texts cho NoticeTab theo ngôn ngữ hiện tại"""
        texts = UI_TEXT.get(self.current_language, UI_TEXT[DEFAULT_LANGUAGE])
        return {
            k: v for k, v in texts.items() 
            if k.startswith('notice_')
        }
    
    def get_all_headers(self):
        """Lấy tất cả headers (dữ liệu chính + metadata) theo ngôn ngữ hiện tại"""
        project_headers = PROJECT_HEADERS.get(self.current_language, PROJECT_HEADERS[DEFAULT_LANGUAGE])
        metadata_headers = METADATA_HEADERS.get(self.current_language, METADATA_HEADERS[DEFAULT_LANGUAGE])
        return project_headers + metadata_headers
    
    def get_all_keys(self):
        """Lấy tất cả key mappings (dữ liệu chính + metadata)"""
        project_keys = PROJECT_KEYS.get(self.current_language, PROJECT_KEYS[DEFAULT_LANGUAGE])
        metadata_keys = METADATA_KEYS.get(self.current_language, METADATA_KEYS[DEFAULT_LANGUAGE])
        return {**project_keys, **metadata_keys}


# Global instance
language_manager = LanguageManager()


def load_language():
    """Standalone function to load language from file"""
    try:
        if os.path.exists(LANGUAGE_FILE):
            with open(LANGUAGE_FILE, 'r', encoding='utf-8') as f:
                lang = f.read().strip()
                if lang in SUPPORTED_LANGUAGES:
                    return lang
        return DEFAULT_LANGUAGE
    except Exception:
        return DEFAULT_LANGUAGE


# ============================================================================
# CLIENT UI TEXT - For client.py
# ============================================================================

CLIENT_TEXT = {
    'vi': {
        # Connection status
        'connected': 'Đã kết nối',
        'disconnected': 'Mất kết nối',
        'checking': 'Đang kiểm tra kết nối...',
        'connecting': 'Đang kết nối server...',
        
        # Login dialog
        'login_title': 'Đăng nhập',
        'login_username': 'Tên đăng nhập:',
        'login_password': 'Mật khẩu:',
        'login_button': 'Đăng nhập',
        'login_cancel': 'Hủy',
        'login_remember': 'Ghi nhớ đăng nhập',
        'login_forgot': 'Quên mật khẩu?',
        'login_username_placeholder': 'Nhập tên đăng nhập',
        'login_password_placeholder': 'Nhập mật khẩu',
        'login_failed': 'Đăng nhập thất bại',
        'login_failed_empty': 'Vui lòng nhập đầy đủ thông tin',
        'login_failed_empty_ip': 'Vui lòng nhập IP máy chủ',
        'login_failed_invalid': 'Tên đăng nhập hoặc mật khẩu không đúng',
        'login_success': 'Đăng nhập thành công!',
        'login_welcome': 'Chào mừng, {}',
        'logout': 'Đăng xuất',
        'logout_confirm': 'Bạn có chắc muốn đăng xuất?',
        'current_user': 'Người dùng hiện tại:',
        'login_server_ip': 'IP Máy chủ:',
        'login_server_ip_placeholder': 'Nhập IP máy chủ',
        'login_checking_connection': 'Đang kiểm tra kết nối...',
        'login_connection_failed': 'Không thể kết nối server. Vui lòng kiểm tra IP và thử lại.',
        
        # Pagination
        'page': 'Trang {page}',
        
        # Messages
        'fill_info': 'Vui lòng điền đầy đủ thông tin',
        'confirm_delete': 'Xác nhận xóa',
        'enter_password': 'Nhập mật khẩu',
        'no_data': 'Không có dữ liệu',
        'exported': 'Đã xuất ra {file_path}',
        'need_openpyxl': 'Cần cài đặt openpyxl',
        'export_error': 'Lỗi xuất: {e}',
        'connection_error': 'Không thể kết nối đến server. Vui lòng kiểm tra IP và thử lại.',
        'invalid_employee': 'Mã nhân viên không hợp lệ. Phải là số từ 001 đến 999.',
        
        # Window title
        'window_title': 'Tạo Mã Bản vẽ Tự động',
        
        # Tabs
        'tab_draw': 'Tạo Mã',
        'tab_history': 'Lịch Sử',
        'tab_language': 'Ngôn ngữ',
        'tab_sync': 'Tool Đồng bộ hóa',
        'tab_project_tracking': 'Theo Dõi Dự Án',
        'tab_about': 'Giới thiệu',
        'tab_settings': 'Cài đặt',
        
        # Settings tab
        'settings_title': 'Cài đặt / 设置',
        'settings_user_info': 'Thông tin người dùng',
        'settings_current_user': 'Người dùng hiện tại:',
        'settings_login_time': 'Thời gian đăng nhập:',
        'settings_logout': 'Đăng xuất',
        'settings_logout_confirm': 'Bạn có chắc muốn đăng xuất?',
        
        # Labels
        'server_ip': 'Server IP:',
        'name_label': 'Tên người xin mã:',
        'employee_label': 'Mã nhân viên:',
        'category_label': 'Hạng mục:',
        'draw_button': 'Tạo Mã Bản Vẽ',
        'result_placeholder': 'Mã Bản vẽ sẽ hiển thị ở đây, Xem thêm tại lịch sử',
        
        # Table headers
        'name': 'Tên',
        'employee': 'Mã nhân viên',
        'category': 'Hạng mục',
        'code': 'Mã bản vẽ',
        'time': 'Thời gian',
        
        # Buttons
        'prev': 'Trước',
        'next': 'Sau',
        'delete_selected': 'Xóa(Del)',
        'export_xls': 'Xuất XLS',
        'refresh': 'Làm mới(F5)',
        'select_language': 'Chọn ngôn ngữ:',
        'vietnamese': 'Tiếng Việt 越南语',
        'chinese': 'Tiếng Trung 中文',
        'apply': 'Áp dụng',
        
        # Project Tracking tab
        'pt_title': 'Theo Dõi Dự Án / 项目跟踪',
        'pt_desc': 'Nhấn nút bên dưới để mở cửa sổ theo dõi dự án\n点击下方按钮打开项目跟踪窗口',
        'pt_open': 'Mở Theo Dõi Dự Án / 打开项目跟踪',
        'pt_opening': 'Đang mở cửa sổ Theo Dõi Dự Án...',
        'pt_error': 'Lỗi khi mở Project Tracking: ',
        
        # Sync tool
        'sync_content': 'Nội dung tool đồng bộ hóa',
        'sync_from_placeholder': 'Nhập link From',
        'sync_to_placeholder': 'Nhập link To',
        'sync_button': 'Đồng bộ ngay',
        'sync_fill_info': 'Vui lòng điền đầy đủ thông tin From và To',
        'sync_saved': 'Đã lưu thông tin đồng bộ vào file',
        'sync_running': 'Đang chạy đồng bộ trong cửa sổ cmd riêng biệt',
        'sync_not_found': 'Không tìm thấy file batch',
        'sync_unknown_error': 'Lỗi không xác định: ',
        'sync_save_error': 'Lỗi lưu file: ',
        'browse': 'Browse',
        'browse_from': 'Chọn thư mục From',
        'browse_to': 'Chọn thư mục To',
    },
    'zh': {
        # Connection status
        'connected': '已连接',
        'disconnected': '断开连接',
        'checking': '正在检查连接...',
        'connecting': '正在连接服务器...',
        
        # Login dialog
        'login_title': '登录',
        'login_username': '用户名:',
        'login_password': '密码:',
        'login_button': '登录',
        'login_cancel': '取消',
        'login_remember': '记住登录',
        'login_forgot': '忘记密码?',
        'login_username_placeholder': '输入用户名',
        'login_password_placeholder': '输入密码',
        'login_failed': '登录失败',
        'login_failed_empty': '请填写完整信息',
        'login_failed_empty_ip': '请输入服务器IP',
        'login_failed_invalid': '用户名或密码错误',
        'login_success': '登录成功!',
        'login_welcome': '欢迎, {}',
        'logout': '退出',
        'logout_confirm': '确定要退出吗?',
        'current_user': '当前用户:',
        'login_server_ip': '服务器IP:',
        'login_server_ip_placeholder': '输入服务器IP',
        'login_checking_connection': '正在检查连接...',
        'login_connection_failed': '无法连接到服务器。请检查IP并重试。',
        
        # Pagination
        'page': '第{page}页',
        
        # Messages
        'fill_info': '请填写完整信息',
        'confirm_delete': '确认删除',
        'enter_password': '输入密码',
        'no_data': '无数据',
        'exported': '已导出到 {file_path}',
        'need_openpyxl': '需要安装openpyxl',
        'export_error': '导出错误: {e}',
        'connection_error': '无法连接到服务器。请检查IP并重试。',
        'invalid_employee': '员工编号无效。必须是001到999之间的数字。',
        
        # Window title
        'window_title': '自动生成图纸编码',
        
        # Tabs
        'tab_draw': '生成',
        'tab_history': '记录',
        'tab_language': 'Ngôn ngữ 语言',
        'tab_sync': 'Tool Đồng bộ hóa',
        'tab_project_tracking': '项目跟踪',
        'tab_about': '关于',
        'tab_settings': '设置',
        
        # Settings tab
        'settings_title': '设置 / 设置',
        'settings_user_info': '用户信息',
        'settings_current_user': '当前用户:',
        'settings_login_time': '登录时间:',
        'settings_logout': '退出',
        'settings_logout_confirm': '确定要退出吗?',
        
        # Labels
        'server_ip': '服务器IP:',
        'name_label': '申请人姓名:',
        'employee_label': '员工编号:',
        'category_label': '类别:',
        'draw_button': '生成编码',
        'result_placeholder': '图纸编码将显示在这里,详细见记录',
        
        # Table headers
        'name': '姓名',
        'employee': '员工编号',
        'category': '类别',
        'code': '图纸编码',
        'time': '生成时间',
        
        # Buttons
        'prev': '上一页',
        'next': '下一页',
        'delete_selected': '删除选中项(Del)',
        'export_xls': '导出XLS',
        'refresh': '刷新(F5)',
        'select_language': '选择语言:',
        'vietnamese': 'Tiếng Việt 越南语',
        'chinese': 'Tiếng Trung 中文',
        'apply': '应用',
        
        # Project Tracking tab
        'pt_title': '项目跟踪',
        'pt_desc': '点击下方按钮打开项目跟踪窗口',
        'pt_open': '打开项目跟踪',
        'pt_opening': '正在打开项目跟踪窗口...',
        'pt_error': '打开项目跟踪时出错: ',
        
        # Sync tool
        'sync_content': 'Tool đồng bộ hóa nội dung',
        'sync_from_placeholder': '输入From链接',
        'sync_to_placeholder': '输入To链接',
        'sync_button': '立即同步',
        'sync_fill_info': '请填写完整的From和To信息',
        'sync_saved': '同步信息已保存到文件',
        'sync_running': '正在单独的cmd窗口中运行同步',
        'sync_not_found': '找不到batch文件',
        'sync_unknown_error': '未知错误: ',
        'sync_save_error': '保存文件错误: ',
        'browse': '浏览',
        'browse_from': '选择From文件夹',
        'browse_to': '选择To文件夹',
    }
}

