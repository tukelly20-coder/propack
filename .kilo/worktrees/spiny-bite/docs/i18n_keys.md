# Web App i18n Keys Documentation

## Tổng quan
Ứng dụng web sử dụng hệ thống i18n (internationalization) hỗ trợ 2 ngôn ngữ:
- **Tiếng Việt (vi)** - Ngôn ngữ mặc định
- **Tiếng Trung (zh)** - Ngôn ngữ phụ

Hệ thống dịch được lưu trữ trong `web/js/i18n.js` và được sử dụng thông qua hàm `t(key)`.

---

## Các Key Theo Module

### 1. COMMON / SHARED (Chung)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `app_title` | Quản Lý Dự Án - Propack VP | 大日程 - Propack VP |
| `loading` | Đang tải... | 加载中... |
| `loading_data` | Đang tải dữ liệu... | 正在加载数据... |
| `saving` | Đang lưu... | 正在保存... |
| `deleting` | Đang xóa... | 正在删除... |
| `processing` | Đang xử lý... | 正在处理... |
| `success` | Thành công | 成功 |
| `error` | Lỗi | 错误 |
| `warning` | Cảnh báo | 警告 |
| `info` | Thông tin | 信息 |
| `save` | Lưu | 保存 |
| `cancel` | Hủy | 取消 |
| `delete` | Xóa | 删除 |
| `edit` | Sửa | 编辑 |
| `view` | Xem | 查看 |
| `add` | Thêm | 新建项目 |
| `refresh` | Làm mới | 刷新 |
| `export` | Xuất | 导出 |
| `search` | Tìm kiếm | 搜索 |
| `close` | Đóng | 关闭 |
| `confirm` | Xác nhận | 确认 |
| `apply` | Áp dụng | 应用 |
| `reset` | Mặc định | 默认 |
| `submit` | Gửi | 提交 |
| `page` | Trang | 页 |
| `of` | của | 共 |
| `per_page` | trang | 页 |
| `first_page` | Trang đầu | 首页 |
| `previous_page` | Trước | 上一页 |
| `next_page` | Sau | 下一页 |
| `last_page` | Trang cuối | 末页 |
| `page_info` | Hiển thị {start} - {end} của {total} bản ghi | 显示 {start} - {end}，共 {total} 条 |
| `jump_to_page` | Nhảy đến trang | 跳转到页 |
| `no_data` | Không có dữ liệu | 暂无数据 |
| `no_results` | Không tìm thấy kết quả | 未找到结果 |
| `load_error` | Lỗi tải dữ liệu | 加载数据出错 |
| `confirm_delete` | Xác nhận xóa | 确认删除 |
| `confirm_delete_message` | Bạn có chắc chắn muốn xóa {count} item đã chọn không? | 确定要删除选中的 {count} 项吗？ |
| `confirm_logout` | Bạn có chắc muốn đăng xuất? | 确定要退出登录吗？ |
| `chars` | ký tự | 字符 |
| `use_system_account` | Sử dụng tài khoản từ hệ thống | 使用系统账号 |
| `basic_info` | Thông tin cơ bản | 基本信息 |
| `technical_info` | Thông tin kỹ thuật | 技术信息 |
| `time_urgency` | Thời gian & Độ khẩn | 时间与紧急程度 |

---

### 2. LOGIN (Đăng nhập)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `login_title` | Quản Lý Dự Án | 大日程 |
| `login_subtitle` | Đăng nhập để tiếp tục | 登录以继续 |
| `username` | Tên đăng nhập | 用户名 |
| `password` | Mật khẩu | 密码 |
| `remember_me` | Ghi nhớ đăng nhập | 记住登录 |
| `login_btn` | Đăng nhập | 登录 |
| `login_failed` | Đăng nhập thất bại | 登录失败 |
| `login_error` | Vui lòng nhập tên đăng nhập và mật khẩu | 请输入用户名和密码 |
| `logging_in` | Đang đăng nhập... | 正在登录... |
| `toast_login_success` | Đăng nhập thành công! | 登录成功！ |
| `toast_logout_success` | Đã đăng xuất! | 已退出登录！ |
| `toast_login_failed` | Đăng nhập thất bại | 登录失败 |
| `login_failed_retry` | Đăng nhập thất bại. Vui lòng thử lại. | 登录失败，请重试。 |

---

### 3. NAVIGATION (Điều hướng)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `nav_projects` | Dự Án | 大日程 |
| `nav_notices` | Thông báo | 通知 |
| `nav_taomabanve` | Tạo Mã Bản Vẽ | 生成图纸编码 |
| `nav_profile` | Hồ Sơ | 个人信息 |
| `nav_ai` | PropackAI | PropackAI（试用） |
| `language_vi` | VI | VI |
| `language_zh` | 中文 | 中文 |
| `submit_feedback` | Gửi Phản hồi | 提交反馈 |
| `logout` | Đăng xuất | 退出登录 |
| `logged_in_as` | Đăng nhập với | 登录为 |

---

### 4. PROJECTS MODULE (Module Dự Án - **新建项目**)

#### 4.1 Actions & Buttons

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `projects_title` | Dự án | 大日程 |
| `add_project` | Thêm mới | 新建 |
| `edit_project` | Sửa | 编辑 |
| `delete_project` | Xóa | 删除 |
| `refresh_projects` | Làm mới dữ liệu | 刷新数据 |
| `toggle_columns` | Chọn cột hiển thị | 选择显示列 |
| `export_excel` | Xuất Excel | 导出Excel |
| `export_csv` | Xuất CSV | 导出CSV |
| `btn_add` | 新建 | 新建 |
| `btn_edit` | 编辑 | 编辑 |
| `btn_delete` | 删除 | 删除 |
| `btn_refresh` | 刷新数据 | 刷新数据 |
| `btn_toggle_columns` | Chọn cột hiển thị | 列 |
| `btn_export` | Xuất | 导出 |

#### 4.2 Filters

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `filter_status` | Lọc theo trạng thái | 按状态筛选 |
| `filter_urgency` | Lọc theo độ khẩn | 按紧急程度筛选 |
| `all_status` | Tất cả trạng thái | 全部状态 |
| `all_urgency` | Tất cả độ khẩn | 全部紧急程度 |
| `status_pending` | Chờ xử lý | 待处理 |
| `status_in_progress` | Đang làm | 进行中 |
| `status_completed` | Hoàn thành | 已完成 |
| `urgency_normal` | Bình thường | 正常 |
| `urgency_urgent` | Khẩn cấp | 紧急 |
| `urgency_very_urgent` | Rất khẩn | 非常紧急 |
| `search_projects` | Tìm kiếm... | 搜索... |
| `clear_search` | Xóa tìm kiếm | 清除搜索 |

#### 4.3 Table Headers

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `col_stt` | STT | 序号 |
| `col_tracking_id` | Tracking ID | Tracking ID |
| `col_ngay` | Ngày | 创建日期 |
| `col_khachhang` | Khách hàng | 客户公司名称 |
| `col_nhanvienkd` | Nhân viên KD | 业务员 |
| `col_tensanpham` | Tên sản phẩm | 产品名称 |
| `col_quycach` | Quy cách | 规格 |
| `col_lienhe_kh` | Người liên hệ (KH) | 客户联系人 |
| `col_soluong` | Số lượng | 数量 |
| `col_mapo` | Mã PO | PO号 |
| `col_mabave` | Mã bản vẽ | 图纸编码 |
| `col_mabavkythuat` | Mã bản vẽ phương án | 方案图号 |
| `col_mame` | Mã mẹ | 母料号 |
| `col_loaisanpham` | Loại sản phẩm | 产品类型 |
| `col_kysu` | Kỹ sư | 工程师 |
| `col_tinhtrang` | Tình trạng nhận dự án | 接受方案状态 |
| `col_dokhan` | Độ khẩn | 紧急程度 |
| `col_tg_mongmuon` | TG mong muốn | 期望时间 |
| `col_tg_hoanthanh` | TG hoàn thành | 完成时间 |
| `col_trangthai` | Trạng thái | 状态 |
| `col_nguoinhan` | Người nhận | 接收人 |
| `col_actions` | Hành động | 操作 |
| `col_select` | Chọn | 选择 |

#### 4.4 Column Selector

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `column_selector_title` | Chọn cột hiển thị | 选择显示列 |
| `column_reset` | Mặc định | 默认 |
| `column_apply` | Áp dụng | 应用 |

#### 4.5 Modal Titles

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `add_project_title` | Thêm dự án mới | 新建项目 |
| `edit_project_title` | Sửa dự án | 编辑项目 |
| `view_project_title` | Chi tiết dự án | 项目详情 |

#### 4.6 Form Fields - Basic Info

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `form_ngay_khoitao` | Ngày khởi tạo | 创建日期 |
| `form_khachhang` | Khách hàng | 客户公司名称 |
| `form_khachhang_required` | Khách hàng * | 客户 * |
| `select_customer` | -- Chọn khách hàng -- | -- 选择客户 -- |
| `liveSearch_placeholder` | Tìm kiếm khách hàng... | 搜索客户... |
| `form_nhanvienkd` | Nhân viên kinh doanh | 业务员 |

#### 4.7 Form Fields - Product Info

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `product_info` | Thông tin sản phẩm | 产品信息 |
| `form_tensanpham` | Tên sản phẩm | 产品名称 |
| `form_tensanpham_required` | Tên sản phẩm * | 产品名称 * |
| `form_quycach` | Quy cách | 规格 |
| `form_lienhe_kh` | Người liên hệ (KH) | 联系人(客户) |
| `form_soluong` | Số lượng | 数量 |
| `form_mapo` | Mã PO | PO号 |

#### 4.8 Form Sections

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `drawing_codes` | Mã bản vẽ | 图纸编码 |

#### 4.9 Form Fields - Drawing Codes

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `form_mabave_chinh` | Mã bản vẽ chính | 图纸编码 |
| `form_mabave` | Mã bản vẽ (phương án) | 图纸编码(方案) |
| `form_mabavkythuat` | Mã bản vẽ kỹ thuật | 技术图纸编码 |
| `form_mame` | Mã mẹ | 母料号 |

#### 4.10 Form Fields - Technical Info

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `form_loaisanpham` | Loại sản phẩm | 产品类型 |
| `select_loaisanpham` | -- Chọn loại sản phẩm -- | -- 选择产品类型 -- |
| `loaisanpham_sjt` | SJT - Bản vẽ tách chi tiết | 散件图 |
| `loaisanpham_wlj` | WLJ - Giá đựng vật liệu | 物料架 |
| `loaisanpham_zzc` | ZZC - Xe trung chuyển | 周转车 |
| `loaisanpham_gzt` | GZT - Bàn thao tác | 工作台 |
| `loaisanpham_wcp` | WCP - Phòng sạch | 无尘棚 |
| `loaisanpham_lsx` | LSX - Băng tải | 流水线 |
| `loaisanpham_zwj` | ZWJ - Băng tải chuyển hướng | 转弯机 |
| `loaisanpham_gzl` | GZL - Cải tạo | 改造类 |
| `loaisanpham_bsx` | BSX - Băng chuyền xích | 倍速线 |
| `loaisanpham_wll` | WLL - Hàng rào | 围栏类 |
| `loaisanpham_gtx` | GTX - Băng chuyền con lăn | 滚筒线 |
| `loaisanpham_zht` | ZHT - Bản vẽ mặt bằng | 展会图 |
| `loaisanpham_lhx` | LHX - Băng chuyền lão hóa | 老化线 |
| `form_kysu` | Nhân viên thiết kế | 设计人员 |
| `form_tinhtrang` | Tình trạng hoàn thành | 完成状态 |

#### 4.11 Form Fields - Time & Urgency

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `form_capbach` | Tính cấp bách | 紧急程度 |
| `form_tg_mongmuon` | Thời gian mong muốn có bản vẽ | 期望收到图纸时间 |
| `form_tg_hoanthanh` | Thời gian hoàn thành kế hoạch | 计划完成时间 |
| `urgency_normal_option` | Bình thường | 普通 |
| `urgency_urgent_option` | Khẩn cấp | 紧急 |
| `urgency_very_urgent_option` | Rất khẩn cấp | 非常紧急 |

#### 4.12 Quick Actions

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `quick_view` | Xem chi tiết | 查看详情 |
| `quick_edit` | Sửa | 编辑 |
| `quick_delete` | Xóa | 删除 |
| `quick_accept` | Nhận việc | 接受任务 |

#### 4.13 Toast Messages

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `toast_project_created` | Tạo dự án thành công | 创建项目成功 |
| `toast_project_updated` | Cập nhật dự án thành công | 更新项目成功 |
| `toast_project_deleted` | Đã xóa {count} dự án | 已删除 {count} 个项目 |
| `toast_export_success` | Đã xuất file {type} | 已导出{type}文件 |
| `toast_no_data_export` | Không có dữ liệu để xuất | 没有可导出的数据 |

#### 4.14 Validation

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `validation_khachhang_required` | Vui lòng nhập tên khách hàng | 请输入客户名称 |
| `validation_tensanpham_required` | Vui lòng nhập tên sản phẩm | 请输入产品名称 |
| `validation_lienhe_required` | Vui lòng nhập người liên hệ | Vui lòng nhập người liên hệ |
| `validation_invalid_page` | Vui lòng nhập trang từ 1 đến {max} | 请输入1到{max}之间的页码 |

---

### 5. NOTICES MODULE (Module Thông báo)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `notices_title` | Thông báo | 通知 |
| `add_notice` | Thêm mới | 新建 |
| `edit_notice` | Sửa | 编辑 |
| `delete_notice` | Xóa | 删除 |
| `stat_total` | Tổng | 合计 |
| `stat_pending` | Chờ duyệt | 待审批 |
| `stat_accepted` | Đã nhận | 已接收 |
| `stat_urgent` | Khẩn | 加急 |
| `auto_refresh_note` | Tự động cập nhật mỗi 30 giây | 每30秒自动刷新 |
| `status_pending_option` | Chờ duyệt | 待审批 |
| `status_accepted` | Đã nhận | 已接收 |
| `status_in_progress` | Đang làm | 进行中 |
| `status_completed_option` | Hoàn thành | 已完成 |
| `form_sanpham` | Sản phẩm | 产品 |
| `form_kysu_field` | Kỹ sư | 工程师 |
| `form_dokhan` | Độ khẩn | 紧急程度 |
| `form_trangthai` | Trạng thái | 状态 |
| `notice_stt` | STT | 序号 |
| `notice_tracking_id` | Tracking ID | Tracking ID |
| `notice_ngay` | Ngày | 日期 |
| `notice_khachhang` | Khách hàng | 客户 |
| `notice_sanpham` | Sản phẩm | 产品 |
| `notice_soluong` | Số lượng | 数量 |
| `notice_nhanvienkd` | Nhân viên KD | 业务员 |
| `notice_kysu` | Kỹ sư | 工程师 |
| `notice_dokhan` | Độ khẩn | 紧急程度 |
| `notice_trangthai` | Trạng thái | 状态 |
| `notice_actions` | Hành động | 操作 |
| `notice_select` | Chọn | 选择 |
| `notice_quick_accept` | Nhận việc | 接受任务 |
| `notice_quick_view` | Xem chi tiết | 查看详情 |
| `notice_quick_edit` | Sửa | 编辑 |
| `notice_quick_delete` | Xóa | 删除 |
| `accept_job` | Nhận việc | 接受任务 |
| `accept_job_confirm` | Bạn có muốn nhận công việc này? | 是否接受此任务？ |
| `accept_job_success` | Đã nhận công việc | 已接受任务 |
| `toast_notice_created` | Tạo thông báo thành công | 创建通知成功 |
| `toast_notice_updated` | Cập nhật thông báo thành công | 更新通知成功 |
| `toast_notice_deleted` | Đã xóa {count} thông báo | 已删除 {count} 条通知 |
| `toast_notice_accepted` | Đã nhận công việc | 已接受任务 |
| `no_notices_found` | Không tìm thấy thông báo nào | 没有找到通知 |
| `loading_notices_data` | Đang tải dữ liệu thông báo... | 正在加载通知数据... |
| `error_loading_notices` | Lỗi tải thông báo | 加载通知出错 |

---

### 6. PROFILE MODULE (Module Hồ sơ)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `profile_title` | Hồ sơ | 个人信息 |
| `basic_info` | Thông tin cơ bản | 基本信息 |
| `contact_info` | Thông tin liên lạc | 联系方式 |
| `login_history` | Lịch sử đăng nhập | 登录历史 |
| `form_username` | Tên đăng nhập | 用户名 |
| `form_role` | Vai trò | 角色 |
| `form_fullname` | Họ và tên | 姓名 |
| `form_employee_id` | Mã nhân viên | 员工编号 |
| `form_department` | Phòng ban | 部门 |
| `form_status` | Trạng thái | 状态 |
| `form_email` | Email | 邮箱 |
| `form_phone` | Số điện thoại | 电话 |
| `form_last_login` | Đăng nhập lần cuối | 最后登录 |
| `form_created_at` | Ngày tạo tài khoản | 账号创建时间 |
| `save_profile` | Lưu thông tin | 保存资料 |
| `change_password` | Đổi mật khẩu | 修改密码 |
| `refresh_profile` | Làm mới | 刷新 |
| `current_password` | Mật khẩu hiện tại | 当前密码 |
| `new_password` | Mật khẩu mới | 新密码 |
| `confirm_password` | Xác nhận mật khẩu mới | 确认新密码 |
| `confirm_password_btn` | Xác nhận | 确认 |
| `password_current_required` | Vui lòng nhập mật khẩu hiện tại | 请输入当前密码 |
| `password_new_required` | Vui lòng nhập mật khẩu mới | 请输入新密码 |
| `password_confirm_required` | Vui lòng xác nhận mật khẩu mới | 请确认新密码 |
| `password_not_match` | Mật khẩu mới không khớp | 新密码不匹配 |
| `password_min_length` | Mật khẩu mới phải có ít nhất 6 ký tự | 新密码至少6位 |
| `toast_profile_saved` | Lưu hồ sơ thành công! | 保存资料成功！ |
| `toast_password_changed` | Đổi mật khẩu thành công! | 修改密码成功！ |

---

### 7. CREATE CODE MODULE (Tạo Mã Bản Vẽ)

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `create_code_title` | Tạo Mã Bản Vẽ | 图纸编码生成工具 |
| `requester_name` | Tên người xin mã | 申请人姓名 |
| `employee_code` | Mã nhân viên công trình | 工程人员工号 |
| `three_digits` | 3 chữ số | 3位数字 |
| `employee_code_hint` | Nhập ID nhân viên công trình 3 chữ số (vd: 001, 002, 003) | 输入工程人员3位工号（如：001, 002, 003） |
| `category` | Hạng mục | 类别 |
| `select_category` | -- Chọn hạng mục -- | -- 选择类别 -- |
| `create_btn` | Tạo Mã | 生成 |
| `cat_sjt` | SJT散件图 - Bản vẽ tách chi tiết | SJT散件图 - 散件图 |
| `cat_wlj` | WLJ物料架 - Giá đựng vật liệu | WLJ物料架 - 物料架 |
| `cat_zzc` | ZZC周转车 - Xe trung chuyển | ZZC周转车 - 周转车 |
| `cat_gzt` | GZT工作台 - Bàn thao tác | GZT工作台 - 工作台 |
| `cat_wcp` | WCP无尘棚 - Phòng sạch | WCP无尘棚 - 无尘棚 |
| `cat_lsx` | LSX流水线 - Băng tải | LSX流水线 - 流水线 |
| `cat_zwj` | ZWJ转弯机 - Băng tải chuyển hướng 90,180 | ZWJ转弯机 - 转弯机 90,180 |
| `cat_gzl` | GZL改造类 - Cải tạo | GZL改造类 - 改造类 |
| `cat_bsx` | BSX倍速线 - Băng chuyền xích | BSX倍速线 - 倍速链 |
| `cat_wll` | WLL围栏类 - Hàng rào | WLL围栏类 - 围栏 |
| `cat_gtx` | GTX滚筒线 - Băng chuyền con lăn | GTX滚筒线 - 滚筒线 |
| `cat_zht` | ZHT展会图 - Bản vẽ mặt bằng | ZHT展会图 - 展会图 |
| `cat_lhx` | LHX老化线 - Băng chuyền lão hóa | LHX老化线 - 老化线 |
| `history` | Lịch Sử Tạo Mã | 生成历史 |
| `history_total` | Tổng | 合计 |
| `total` | Tổng | 合计 |
| `history_today` | Hôm nay | 今天 |
| `today` | Hôm nay | 今天 |
| `history_week` | Tuần | 本周 |
| `week` | Tuần | 本周 |
| `history_latest` | Mới nhất | 最新 |
| `latest` | Mới nhất | 最新 |
| `history_name` | Tên | 姓名 |
| `name` | Tên | 姓名 |
| `history_employee_code` | Mã nhân viên | 员工工号 |
| `employee_code_th` | Mã nhân viên | 员工工号 |
| `history_category` | Hạng mục | 类别 |
| `category_th` | Hạng mục | 类别 |
| `history_drawing_code` | Mã bản vẽ | 图纸编码 |
| `drawing_code` | Mã bản vẽ | 图纸编码 |
| `mother_code` | Mã mẹ | 母料号 |
| `history_time` | Thời gian | 时间 |
| `time` | Thời gian | 时间 |
| `history_action` | Thao tác | 操作 |
| `action` | Thao tác | 操作 |
| `history_copy` | Copy | 复制 |
| `history_delete` | Xóa | 删除 |
| `create_code` | Tạo Mã Bản Vẽ | 生成图纸编码 |
| `delete_code_title` | Xóa mã | 删除编码 |
| `delete_code_confirm` | Nhập mật khẩu để xóa mã {code}: | 请输入密码以删除编码 {code}: |
| `delete_code_password` | Mật khẩu | 密码 |
| `delete_code_wrong_password` | Mật khẩu không đúng | 密码错误 |
| `toast_code_created` | Đã tạo mã: | 已生成编码: |
| `toast_code_copy` | Đã copy mã vào clipboard | 已复制到剪贴板 |
| `toast_code_deleted` | Đã xóa mã {code} | 已删除编码 {code} |
| `creating` | Đang tạo mã bản vẽ... | 正在生成图纸代码... |
| `creating_code` | Đang tạo mã... | 正在生成编码... |
| `deleting_code` | Đang xóa mã... | 正在删除编码... |
| `exporting_data` | Đang xuất dữ liệu... | 正在导出数据... |
| `no_history` | Chưa có lịch sử tạo mã | 暂无创建历史 |
| `load_history_error` | Lỗi tải lịch sử: | 加载历史出错: |
| `copy_title` | Copy | 复制 |
| `delete_title` | Xóa | 删除 |
| `excel_sheet_name` | LichSuMa | 创建历史 |
| `excel_filename_prefix` | lich_su_ma_ | code_history_ |
| `validation_employee_3digits` | Mã nhân viên phải có 3 chữ số | 员工工号必须为3位数字 |
| `validation_employee_not_zero` | Mã nhân viên không được là 000 | 员工工号不能为000 |
| `validation_name_required` | Vui lòng nhập tên người xin mã | 请输入申请人姓名 |
| `validation_category_required` | Vui lòng chọn hạng mục | 请选择类别 |
| `seconds_ago` | giây trước | 秒前 |
| `minutes_ago` | phút trước | 分钟前 |
| `hours_ago` | giờ trước | 小时前 |
| `yesterday` | Hôm qua | 昨天 |
| `days_ago` | ngày trước | 天前 |

---

### 8. AI MODULE

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `ai_title` | PropackAI | PropackAI |

---

### 9. OTHER/UTILITY

| Key | Tiếng Việt | Tiếng Trung |
|-----|-----------|-------------|
| `loading_projects` | Đang tải dữ liệu dự án... | 正在加载项目数据... |
| `loading_notices` | Đang tải thông báo... | 正在加载通知... |
| `loading_taomabanve` | Đang tải trang tạo mã... | 正在加载编码生成页面... |
| `loading_profile` | Đang tải hồ sơ... | 正在加载个人信息... |
| `loading_ai` | Đang tải AI... | 正在加载AI... |
| `toast_warning` | Cảnh báo | 警告 |
| `toast_no_data_export` | Không có dữ liệu để xuất | 没有可导出的数据 |
| `toast_export_success` | Đã xuất file {type} | 已导出{type}文件 |
| `toast_feedback_sent` | Phản hồi đã được gửi! | 反馈已提交！ |
| `feedback_error` | Có lỗi xảy ra | 发生错误 |

---

## Cấu trúc Dữ liệu

Hệ thống i18n sử dụng object `translations` với cấu trúc:

```javascript
const translations = {
    vi: { /* tất cả key tiếng Việt */ },
    zh: { /* tất cả key tiếng Trung */ }
};
```

Hàm `t(key, params)` được sử dụng để lấy translation:
- `key`: Tên key dịch
- `params`: Object chứa các tham số để thay thế (ví dụ: `{count: 5}` sẽ thay `{count}` bằng 5)

---

## Cách sử dụng

1. Trong HTML: Sử dụng attribute `data-i18n="key_name"`
   ```html
   <span data-i18n="app_title">Quản Lý Dự Án</span>
   ```

2. Trong JavaScript: Gọi hàm `t('key_name')`
   ```javascript
   const title = t('add_project_title');
   ```

3. Placeholder: Sử dụng `data-i18n-placeholder`
   ```html
   <input placeholder="Search..." data-i18n-placeholder="search_placeholder">
   ```

4. Title attribute: Sử dụng `data-i18n-title`
   ```html
   <button title="Save" data-i18n-title="save">Lưu</button>
   ```

---

## Thêm Key Mới

Để thêm key mới:

1. Thêm key vào object `translations.vi` trong `web/js/i18n.js`
2. Thêm key tương ứng vào object `translations.zh`
3. Sử dụng key trong code theo các cách ở phần "Cách sử dụng"

---

**Lưu ý**: Tất cả các key được liệt kê ở trên phải có trong cả 2 ngôn ngữ (vi và zh) để đảm bảo đầy đủ tính đa ngôn ngữ.
