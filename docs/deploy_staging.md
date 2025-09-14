````markdown
# Triển khai Staging trên Render

Tài liệu này mô tả quy trình build & push image, cấu hình biến môi trường, và khởi động container cho môi trường staging.

---

## 1. Build & Push Docker Image

> **Lưu ý:** Render có thể tự build từ Dockerfile khi bạn push commit mới. Bước build/push thủ công chỉ cần nếu bạn muốn test local hoặc push image lên registry riêng.

### Build local (tùy chọn)
```bash
# Build image từ Dockerfile chung
docker build -t myapp-staging:latest .
````

### Test local (tùy chọn)

```bash
# Chạy container thử nghiệm
docker run -p 8000:8000 --env-file .env myapp-staging:latest
```

### Push lên registry riêng (nếu không dùng auto-build của Render)

```bash
docker tag myapp-staging:latest <your-registry>/myapp-staging:latest
docker push <your-registry>/myapp-staging:latest
```

Nếu dùng **Render Auto-Deploy**, chỉ cần:

1. Commit code mới.
2. Push lên branch được liên kết.
3. Render sẽ tự động build image từ Dockerfile sau mỗi commit.

---

## 2. Cấu Hình Environment Variables (API Keys)

Trong Render Dashboard:

1. Vào **Dashboard → Service → Settings → Environment**.
2. Thêm hoặc cập nhật các key sau:

   * `GEMINI_API_KEY`
   * `WEAVIATE_URL`
   * `WEAVIATE_API_KEY`
   * `PYTHON_VERSION` (ví dụ: `3.11`)

> Không commit file `.env` chứa giá trị thực vào repo. Render sẽ inject các biến này vào container khi khởi động.

---

## 3. Khởi Động Container

### Tự động trên Render

1. Render tự **pull code mới**, **build Docker image**, và **deploy** sau mỗi commit vào branch được liên kết.
2. Kiểm tra tab **Deploys** để theo dõi tiến trình build.
3. Khi trạng thái chuyển sang **Live**, service staging đã chạy.

### Thủ công local (tùy chọn)

Nếu cần chạy staging local trước:

```bash
docker-compose down  # (nếu có dịch vụ cũ)
docker-compose up -d  # hoặc chạy trực tiếp bằng docker run như ở trên
```

---

## 4. Xác Minh Sau Deploy

1. Mở URL Render của bạn: `https://your-app.onrender.com/docs`.
2. Chạy các endpoint cơ bản (ví dụ `/retrieve`, `/agent`) hoặc dùng script [`scripts/smoke_test.sh`](./smoke_test.sh) để smoke test.
3. Nếu có sự cố, tham khảo [docs/rollback\_plan.md](./rollback_plan.md) để rollback.

---

## 5. Ghi Chú

* Gom tất cả service vào **một Dockerfile** (như ví dụ bạn đang dùng) để Render tự động build.
* Đảm bảo `requirements.txt` và source code luôn được cập nhật trước khi commit.
* Mỗi lần push commit mới, Render sẽ tự động khởi động lại container staging.

```

---
