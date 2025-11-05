# Hiệu năng sau khi tối ưu Redis Cache

## 1. Trước khi tối ưu
- Mỗi request `/retrieve` đều query vector store và LLM.
- Latency trung bình: ~230–250 ms.

## 2. Sau khi tối ưu (Redis cache 5 phút)
- Request đầu tiên: query vector store (fresh).
- Request lặp lại trong 5 phút: trả kết quả từ Redis.

| Test case         | Latency (ms) | Nguồn  |
|-------------------|--------------|--------|
| Lần 1 (fresh)     | 240          | fresh  |
| Lần 2 (cache hit) | 12           | cache  |
| Lần 3 (cache hit) | 11           | cache  |
| Lần 4 (cache hit) | 13           | cache  |
| Lần 5 (cache hit) | 12           | cache  |

## 3. Kết luận
- Redis cache giảm latency trung bình từ ~240ms xuống ~12ms cho query trùng lặp.
- Giảm tải đáng kể cho vector store & LLM.
