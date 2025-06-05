# 1. URL Pattern

## Danh sách văn bản:

Trang kết quả tìm kiếm sử dụng AJAX:

https://luatvietnam.vn/van-ban/ajax/searchajax?Keywords=&DocTypeIds=58&DocTypeIds=10&SearchOptions=1&RowAmount=20&PageIndex={page_number}

* `DocTypeIds=58` và `DocTypeIds=10`: đại diện cho 2 loại văn bản được lọc (Luật và bộ luật).
* `RowAmount=20`: số lượng văn bản mỗi trang.
* `PageIndex`: số trang (từ 1 đến 38).

## URL văn bản chi tiết:

Từ trang kết quả, các liên kết trỏ tới trang văn bản chi tiết có định dạng:

{type}/{header}.html

Ví dụ:

* lao-dong/du-thao-luat-viec-lam-304955-d10.html

Khi kết hợp với `base_url = https://luatvietnam.vn`, ta có URL đầy đủ:

https://luatvietnam.vn/lao-dong/du-thao-luat-viec-lam-304955-d10.html



# 2. DOM Structure

## Trang kết quả (AJAX):

Mỗi văn bản được hiển thị trong một thẻ `div` như sau:

<div class="post-type-doc">
  <a href="/thong-tu-...">...</a>
</div>



# 3. 🔍 Filter Logic

## Logic lọc URL:

* Dùng `soup.find_all('div', class_='post-type-doc')` để lấy tất cả thẻ chứa thông tin văn bản.
* Mỗi `div` chứa 1 thẻ `a` duy nhất là link văn bản chi tiết.
* `href` từ thẻ `a` được lấy ra để kết hợp với `base_url`.

## Bảo vệ:

* Ghi log các trang thất bại khi `requests.get()` không trả về mã 200 vào file `failed_links.log`.



