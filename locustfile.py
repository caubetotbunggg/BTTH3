from locust import HttpUser, task, between

class RAGUser(HttpUser):
<<<<<<< HEAD
    wait_time = between(1, 3)  # nghỉ 1–3s giữa các request
=======
    wait_time = between(1, 3)
>>>>>>> dev-test-deploy

    @task(2)
    def call_retrieve(self):
        self.client.post(
            "/retrieve?user_input=giao%20duc%20hoa%20nhap&k=5"
        )

<<<<<<< HEAD
=======
    @task(2)
    def call_rag(self):
        self.client.post(
            "/rag?user_input=giao%20duc%20hoa%20nhap&k=3"
        )

    @task(1)
    def call_agent(self):
        self.client.post(
            "/agent?user_input=giao%20duc%20hoa%20nhap&k=3&max_steps=3&timeout_sec=20"
        )
>>>>>>> dev-test-deploy
