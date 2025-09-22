# Load Test Results

## Test Setup
- Tool: Locust
- Target: https://btth3.onrender.com
- Concurrent Users: 100
- Duration: 5 minutes

## Metrics
| Endpoint   | P95 Latency (ms) | Error Rate (%) | Total Requests |
|------------|------------------|----------------|----------------|
| /retrieve  | 350              | 0.5%           | 12,000         |
| /agent     | 420              | 1.2%           | 6,000          |

## Bottleneck Analysis
- CPU usage: 85%
- Memory usage: 60%
- Error spikes khi số request tăng nhanh → nghi vấn kết nối DB hoặc threadpool FastAPI giới hạn.

## Conclusion
- Hệ thống ổn định với 100 concurrent users.
- Điểm nghẽn có thể nằm ở connection pool tới DB.
- Khuyến nghị: tăng `uvicorn workers`, tune DB pool.
