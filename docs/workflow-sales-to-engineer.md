# Workflow làm việc thực tế của dự án

Tài liệu này mô tả **workflow nghiệp vụ của dự án**, không phải workflow kỹ thuật của hệ thống.

Dự án có 2 luồng làm việc chính:

1. **Luồng phương án**: làm bản vẽ/phương án trước khi trúng thầu.
2. **Luồng xuống đơn**: chỉ bắt đầu sau khi phương án trúng thầu; lúc này mới có mã bản vẽ xuống đơn và mã mẹ.

---

## Tổng Quan

Một project có thể dừng lại ở giai đoạn phương án nếu không trúng thầu. Không phải project nào cũng đi đến giai đoạn xuống đơn.

Vì vậy, các cột trong bảng cần được hiểu theo mốc công việc:

| Nhóm dữ liệu | Giai đoạn phương án | Sau khi trúng thầu / xuống đơn |
|---|---|---|
| Thông tin khách hàng | Có | Có |
| Quy cách / yêu cầu | Có | Có thể bổ sung/chỉnh sửa |
| Mã bản vẽ phương án | Có thể có | Giữ để đối chiếu |
| Mã bản vẽ xuống đơn | Chưa có | Bắt đầu có |
| Mã mẹ | Chưa có | Bắt đầu có |
| BOM / hoàn thành đơn | Chưa bắt buộc | Bắt đầu theo dõi |

---

## Luồng 1: Làm Phương Án

### Mục Đích

Làm phương án để báo giá, trao đổi với khách hàng và tham gia đấu thầu.

Ở giai đoạn này, dự án **chưa được xem là đơn hàng chính thức**.

### Dữ Liệu Thường Có

| Trường trên bảng | Ý nghĩa |
|---|---|
| Ngày | Tháng/ngày tạo nhu cầu |
| Khách hàng | Khách hàng hoặc công ty cần làm phương án |
| Nhân viên kinh doanh | Người phụ trách khách hàng |
| Khách hàng yêu cầu quy cách | Kích thước, nội dung, yêu cầu chính của phương án |
| Loại sản phẩm | Nhóm sản phẩm để phân loại và tạo mã |
| Tính cấp bách | Mức độ ưu tiên |
| Người thiết kế | Người làm phương án/bản vẽ |
| Tình trạng hoàn thành | Trạng thái của phương án |

### Mã Và Dữ Liệu Chưa Bắt Buộc

Trong luồng phương án, các thông tin sau **có thể trống**:

| Trường | Lý do |
|---|---|
| Mã bản vẽ xuống đơn | Chưa trúng thầu nên chưa xuống đơn |
| Mã mẹ | Chưa có sản phẩm chính thức để tạo mã mẹ |
| PO | Khách hàng chưa đặt hàng |
| BOM | Chưa cần hoàn thiện BOM chính thức |
| Thời gian hoàn thành kế hoạch | Có thể chưa xác định |

### Kết Quả Của Luồng Phương Án

Có 2 khả năng:

1. **Không trúng thầu**
   - Project dừng ở trạng thái phương án.
   - Không cần mã bản vẽ xuống đơn.
   - Không cần mã mẹ.

2. **Trúng thầu**
   - Project chuyển sang luồng 2.
   - Bắt đầu bổ sung mã bản vẽ xuống đơn, mã mẹ và các thông tin sản xuất.

---

## Luồng 2: Sau Khi Phương Án Trúng Thầu / Xuống Đơn

### Mục Đích

Chuyển project từ phương án sang đơn hàng chính thức để xử lý bản vẽ kỹ thuật, mã mẹ, BOM và sản xuất.

Luồng này **chỉ bắt đầu khi phương án đã trúng thầu**.

### Dữ Liệu Bắt Đầu Cần Có

| Trường trên bảng | Ý nghĩa |
|---|---|
| Mã bản vẽ xuống đơn | Mã bản vẽ chính thức sau khi có đơn |
| Mã mẹ | Mã vật tư/sản phẩm mẹ để liên kết BOM, ERP, vật liệu |
| PO | Mã PO nếu khách hàng đã phát hành |
| Số lượng | Số lượng theo đơn |
| Thời gian mong muốn có bản vẽ | Deadline theo đơn |
| Thời gian hoàn thành kế hoạch | Mốc hoàn thành nội bộ |
| Tình trạng hoàn thành | Theo dõi đã ra bản vẽ, đang BOM, BOM hoàn thành... |

### Ý Nghĩa Các Mã

| Loại mã | Khi nào có | Dùng để làm gì |
|---|---|---|
| Mã bản vẽ phương án | Trong giai đoạn làm phương án | Đối chiếu phương án, lịch sử đấu thầu |
| Mã bản vẽ xuống đơn | Sau khi trúng thầu | Quản lý bản vẽ chính thức của đơn hàng |
| Mã mẹ | Sau khi xuống đơn | Liên kết BOM, ERP, vật liệu và sản xuất |

### Kết Quả Của Luồng Xuống Đơn

Project được theo dõi đến khi hoàn thành các mốc chính:

1. Đã có mã bản vẽ xuống đơn.
2. Đã có mã mẹ nếu cần BOM/sản xuất.
3. Đã hoàn thành bản vẽ kỹ thuật.
4. Đã hoàn thành BOM nếu project cần BOM.
5. Sẵn sàng chuyển tiếp cho các bước sản xuất/mua vật tư.

---

## Trạng Thái Gợi Ý Trên Bảng

Cột **Tình trạng hoàn thành** nên phân biệt rõ 2 luồng:

| Trạng thái | Thuộc luồng | Ý nghĩa |
|---|---|---|
| Đang làm phương án | Phương án | Đang vẽ/chỉnh phương án |
| Phương án đã hoàn thành | Phương án | Đã ra bản vẽ/phương án để báo giá |
| Không trúng thầu | Phương án | Kết thúc ở giai đoạn phương án |
| Trúng thầu - chờ xuống đơn | Chuyển tiếp | Đã trúng thầu nhưng chưa có mã xuống đơn |
| Đã xuống đơn | Xuống đơn | Bắt đầu có mã bản vẽ chính thức |
| Đang làm bản vẽ kỹ thuật | Xuống đơn | Đang xử lý bản vẽ sau đơn |
| BOM đang làm | Xuống đơn | Đang tạo BOM |
| BOM hoàn thành | Xuống đơn | BOM đã xong |
| Hoàn thành | Xuống đơn | Hoàn tất các việc cần theo dõi |

---

## Cách Hiểu Các Ô Trống Trong Bảng

Không phải ô trống nào cũng là lỗi.

Trong luồng phương án, các cột như **mã bản vẽ xuống đơn**, **mã mẹ**, **PO**, **BOM** có thể trống là bình thường, vì project chưa trúng thầu.

Chỉ nên xem là thiếu dữ liệu khi project đã vào luồng xuống đơn mà các thông tin bắt buộc vẫn trống.

---

## Nguyên Tắc Hiển Thị Trong Phần Mềm

1. Khi project đang ở luồng phương án:
   - Ưu tiên hiện thông tin khách hàng, quy cách, loại sản phẩm, người thiết kế, trạng thái phương án.
   - Không nên báo lỗi chỉ vì chưa có mã mẹ hoặc mã bản vẽ xuống đơn.

2. Khi project đã trúng thầu:
   - Bắt đầu yêu cầu bổ sung mã bản vẽ xuống đơn.
   - Bắt đầu yêu cầu mã mẹ nếu có BOM/sản xuất.
   - Theo dõi rõ trạng thái BOM và hoàn thành.

3. Modal chi tiết dự án nên giúp người xem biết project đang ở luồng nào:
   - Phương án.
   - Chờ xuống đơn.
   - Đã xuống đơn / đang BOM / hoàn thành.

---

## Tóm Tắt Ngắn Gọn

Workflow làm việc của dự án không phải chỉ là "Sales tạo - Engineer nhận".

Workflow đúng là:

1. Tạo nhu cầu/phương án.
2. Làm bản vẽ phương án.
3. Nếu không trúng thầu: dừng ở phương án.
4. Nếu trúng thầu: chuyển sang xuống đơn.
5. Sau khi xuống đơn mới có mã bản vẽ chính thức và mã mẹ.
6. Tiếp tục theo dõi bản vẽ kỹ thuật, BOM và hoàn thành.

