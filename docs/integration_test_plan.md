# Integration Test Plan

## Mục tiêu
Đảm bảo endpoint `/agent` hoạt động đúng theo luồng xử lý 3 bước:
1. Retrieve laws  
2. Generate answer  
3. Format citation  

và xử lý tốt các tình huống lỗi (timeout, input không hợp lệ, lỗi nội bộ).

---

## Test Cases

### 1. Happy Path: Thực thi đầy đủ 3 bước
**Mô tả:** Người dùng hỏi về một khái niệm có trong dữ liệu, chạy đủ `Retrieve → Generate → Format`.  
- **Input:**  
  ```json
  { "user_input": "hợp đồng lao động", "k": 3 }
````

* **Expected Output:**

  * Status code `200`.
  * Response chứa:

    * `steps_executed = [ {step:1}, {step:2}, {step:3} ]`.
    * `laws` có dữ liệu.
    * `answer` có text.
    * `formatted` có citations.

---

### 2. Timeout tại bất kỳ step

**Mô tả:** Một bước trong pipeline (Retrieve / Generate / Format) bị treo quá lâu.

* **Input:**

  ```json
  { "user_input": "hợp đồng lao động", "k": 3, "timeout_sec": 0.001 }
  ```
* **Expected Output:**

  * Status code `504`.
  * Message: `"Step X timed out after ...s"`.
  * `steps_executed` chỉ chứa các step đã chạy xong trước khi timeout.

---

### 3. Error trong một step

**Mô tả:** Agent gặp lỗi khi gọi tool.

* **Input:**

  ```json
  { "user_input": "tính hợp pháp của điều khoản ABC", "k": 3 }
  ```
* **Expected Output:**

  * Status code `500`.
  * Message: `"Step X failed: ..."`.
  * `steps_executed` chỉ chứa các step chạy thành công trước đó.

---

### 4. Query không có dữ liệu

**Mô tả:** Người dùng hỏi ngoài phạm vi luật.

* **Input:**

  ```json
  { "user_input": "định nghĩa vật lý lượng tử", "k": 3 }
  ```
* **Expected Output:**

  * Status code `200`.
  * `laws.chunks = []`.
  * `answer` và `formatted` sẽ trả lời theo hướng `"Không tìm thấy thông tin phù hợp."`.

---

### 5. Invalid Input Format

**Mô tả:** Request thiếu trường bắt buộc.

* **Input:**

  ```json
  { "text": "hợp đồng" }
  ```
* **Expected Output:**

  * Status code `422`.
  * Message `"Invalid request format"`.

---

### 6. Empty Query

**Mô tả:** Người dùng gửi query rỗng.

* **Input:**

  ```json
  { "user_input": "", "k": 3 }
  ```
* **Expected Output:**

  * Status code `400`.
  * Message `"Query cannot be empty"`.

---

### 7. Dừng sau 1 hoặc 2 bước (max\_steps < 3)

**Mô tả:** Kiểm tra tham số `max_steps`.

* **Input:**

  ```json
  { "user_input": "hợp đồng lao động", "k": 3, "max_steps": 2 }
  ```
* **Expected Output:**

  * Status code `200`.
  * Chỉ có step 1 và step 2 được thực thi.
  * Không có `formatted`.

---

