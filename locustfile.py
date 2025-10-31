from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 3)  # nghỉ 1–3s giữa các request

    @task(2)
    def call_retrieve(self):
        self.client.post(
            "/retrieve?user_input=giao%20duc%20hoa%20nhap&k=5"
        )

