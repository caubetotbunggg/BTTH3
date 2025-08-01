from FlagEmbedding import FlagReranker

reranker = FlagReranker(
    "BAAI/bge-reranker-v2-m3", use_fp16=False
)  # base model, chạy được trên CPU
scores = reranker.compute_score(
    [
        ["what is panda?", "hi"],
        [
            "what is panda?",
            "The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.",
        ],
    ]
)
print(scores)
