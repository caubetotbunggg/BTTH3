# Rollback Plan – Render Deployment

## Mục tiêu
Đảm bảo có thể quay lại trạng thái trước đó nếu deploy mới gặp sự cố.

---

## Các bước rollback

### 1. Sử dụng Render Dashboard
1. Vào [Render Dashboard](https://dashboard.render.com/).
2. Chọn service đã deploy.
3. Chuyển đến tab **Deploys**.
4. Tìm deploy trước đó (trạng thái "Live" hoặc "Successful").
5. Nhấn **Rollback to this deploy** để khôi phục.

---

### 2. Sử dụng Render CLI (tùy chọn)
Nếu dùng CLI:
```bash
render deploy rollback <SERVICE_ID> <DEPLOY_ID>
```

### 3. Trong trường hợp khẩn cấp (service container lỗi nặng)

Tạm dừng deploy hiện tại:

Trong Dashboard: Settings → Pause Service.

Khởi động lại container bằng image tag cũ (nếu dùng Docker):
```bash
docker-compose down
docker-compose pull <previous_tag>
docker-compose up -d
```

Xác minh service hoạt động bình thường bằng smoke_test.sh.

### 4. Kiểm tra lại sau rollback

Chạy lại smoke_test.sh để đảm bảo service khôi phục thành công.


---

## 🧰 **Quy trình khuyến nghị khi deploy trên Render**
1. **Deploy phiên bản mới** → **Render sẽ giữ deploy trước**.  
2. **Chạy `smoke_test.sh`** (có thể thêm vào CI/CD workflow hoặc chạy thủ công).  
3. Nếu test **thất bại** → **Rollback ngay** qua Render Dashboard/CLI.  
4. Ghi chú nguyên nhân, fix, rồi deploy lại.

---