# 1. Trường dữ liệu trong JSON

## Chia batch:

* Do các thông tin cần cào đều nằm ở dạng tĩnh nên ta sẽ chỉ sử dụng `Request` và `BeautifulSoup`.
* Để tránh bị chặn do gửi quá nhiều request, ta sẽ chia mỗi batch `15` pages.

## Tham Số:

* `concurrency_limit` : tối đa `10` thread/batch.
* `rate_limit_delay` : delay `1.5` giây mỗi request.

