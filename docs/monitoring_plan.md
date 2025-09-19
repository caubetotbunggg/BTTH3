# Monitoring Plan

## Mục tiêu

Tài liệu này định nghĩa các metric quan trọng, cách đo, ngưỡng cảnh báo, kênh cảnh báo, và sơ đồ luồng data để thu thập metrics bằng Prometheus/Grafana. Mục tiêu là đảm bảo hệ thống có thể giám sát latency, QPS, error rate và các chỉ số vận hành chính khác.

---

## 1. Danh sách metric quan trọng

| Metric name                 |                                       Mục đích | Cách đo / Export                                                                 |         Unit |                                                         Threshold (alert) |
| --------------------------- | ---------------------------------------------: | -------------------------------------------------------------------------------- | -----------: | ------------------------------------------------------------------------: |
| request\_latency\_ms        |                  Độ trễ end-to-end cho request | Middleware đo thời gian xử lý request, expose histogram + summary cho Prometheus | milliseconds |                                            p95 > 2000ms hoặc p99 > 5000ms |
| requests\_per\_second (qps) |                          Lượng request trên 1s | Counter tăng trong middleware, tính rate ở Prometheus                            |          rps | sudden drop >50% so với baseline hoặc sustained spike > 500 rps (tùy app) |
| error\_rate                 |                                Tỷ lệ lỗi (5xx) | Counter cho lỗi 4xx/5xx trong middleware                                         | % or count/s |             error\_rate (5xx) > 1% trong 5 phút hoặc error count > 10/min |
| cpu\_usage                  |                      Sử dụng CPU của container | Node exporter / container exporter hoặc cloud metrics                            |            % |                                                              > 80% for 5m |
| memory\_usage               |                          Sử dụng RAM container | container metrics                                                                |       MB / % |                                                              > 85% for 5m |
| disk\_io                    |                     Disk read/write throughput | node exporter                                                                    |         MB/s |                                             sustained high IO > threshold |
| queue\_depth                | Độ dài hàng đợi (job queue / background tasks) | Exporter cho queue (Redis, Celery)                                               |       number |                                                        > 100 items for 5m |
| vectorstore\_latency        |          Thời gian gọi vector store (retrieve) | Instrument wrapper around calls to vector DB                                     |           ms |                                                              p95 > 1000ms |
| embedding\_latency\_batch   |                  Thời gian cho batch embedding | Instrument batch API calls                                                       |           ms |                                                              p95 > 2000ms |
| cache\_hit\_rate            |                                Tỉ lệ cache hit | Counter hit/miss                                                                 |            % |                              cache\_hit\_rate < 70% (indicates misconfig) |

---

## 2. Cách đo (recommended implementations)

### 2.1 FastAPI middleware (measuring request latency / QPS / errors)

* Tạo middleware để:

  * ghi `start = time.time()` khi request tới
  * gọi `await call_next(request)`
  * tính `elapsed_ms = (time.time() - start) * 1000`
  * cập nhật Prometheus metrics: `REQUEST_LATENCY.observe(elapsed_ms)`, `REQUEST_COUNT.inc()`; nếu response status >=500 thì `ERROR_COUNT.inc()`.
* Export metrics endpoint `/metrics` trả theo định dạng Prometheus.

*Example (pseudo):*

```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
REQUEST_LATENCY = Histogram('request_latency_ms', 'Request latency in ms', ['path', 'method'])
REQUEST_COUNT = Counter('requests_total', 'Total HTTP requests', ['path', 'method', 'status'])
ERROR_COUNT = Counter('errors_total', 'Total error responses', ['path', 'method', 'status'])

# middleware code: observe, inc counters

@app.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### 2.2 Instrument internal calls

* Bọc các client calls (vector store, embedding API, DB) bằng decorator/timer để expose latency metrics cho từng backend.
* Ví dụ: `vectorstore_query_latency_ms{operation="retrieve"}`

### 2.3 Cache metrics

* Expose `cache_hits_total` và `cache_misses_total` để tính `cache_hit_rate`.

---

## 3. Alerting: ngưỡng & kênh

### 3.1 Threshold examples

* `High latency`: p95(request\_latency\_ms) > 2000ms for 5m
* `High error rate`: increase of 5xx rate > 1% for 5m or > 10 errors/min
* `High CPU`: container CPU > 80% for 5m
* `Low Cache Hit`: cache\_hit\_rate < 70% for 10m

### 3.2 Kênh alert

* Email ([team-oncall@example.com](mailto:team-oncall@example.com))
* Slack channel: `#alerts-app` (use webhook or Alertmanager -> Slack integration)
* PagerDuty for on-call escalation (optional)

### 3.3 Alert routing

* Critical (service down / p95 > 5s): PagerDuty + Slack + Email
* Warning (p95 > 2s, error rate exceed): Slack + Email
* Info (spike but not sustained): Slack only

---

## 4. Sơ đồ data flow sang Prometheus

```
 +-----------------+    +----------------+    +--------------+
 | FastAPI service | -> | /metrics (HTTP) | -> | Prometheus   |
 | - middleware    |    | exposes metrics |    | (scrape)     |
 | - instrumented  |    +----------------+    +--------------+
 |   libraries     |                               |
 +-----------------+                               v
                                               +---------+
                                               | Grafana |
                                               +---------+
```

* Prometheus sẽ `scrape` endpoint `http://<service-host>:<port>/metrics`
* Grafana đọc metric từ Prometheus để hiển thị dashboard
* Alertmanager (connected to Prometheus) sẽ gửi alert đến Slack/Email/PagerDuty

---

## 5. Prometheus scrape config (snippet)

```yaml
scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['host.docker.internal:8000'] # in Docker desktop local dev
    metrics_path: '/metrics'
    scrape_interval: 15s
```

> Notes:
>
> * In production use service discovery (kubernetes, Consul, etc.) instead of static\_configs.

---

## 6. Grafana dashboard ideas

* Panel 1: p50 / p95 / p99 request latency (line)
* Panel 2: QPS (requests per second) (line)
* Panel 3: Error rate (5xx count per minute) (bar)
* Panel 4: Cache hit rate (gauge)
* Panel 5: Vectorstore latency (histogram heatmap)

---

## 7. Implementation checklist (Deliverables)

* [ ] `docs/monitoring_plan.md` (this file)
* [ ] Middleware + `/metrics` endpoint in app
* [ ] Local Docker Compose for Prometheus + Grafana (snippet)
* [ ] Grafana dashboard (screenshot)
* [ ] Alertmanager config to route alerts to Slack/Email

---

## 8. Quick local setup (Docker Compose snippet)

```yaml
version: '3.7'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - '9090:9090'
  grafana:
    image: grafana/grafana:latest
    ports:
      - '3000:3000'
  app:
    build:
      context: .
      dockerfile: ./app/Dockerfile
    ports:
      - '8000:8000'
```

---

## 9. Notes / best practices

* Use labels for metrics (avoid high cardinality). Example label: `path` not `user_id`.
* Use histograms for latency to compute p95/p99.
* Keep exporters lightweight; push heavy aggregation to Prometheus.
* Test alerting paths (trigger a synthetic alert) to ensure Slack/Email works.

---

## 10. Next steps

1. Implement middleware and `/metrics` endpoint in the app (instrument common operations).
2. Stand up local Prometheus + Grafana using the Compose snippet.
3. Create dashboards and snapshots.
4. Configure Alertmanager and Slack integration.

---

