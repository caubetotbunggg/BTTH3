import json
import os
import random
import sys
import traceback
from datetime import datetime

import chromadb
import numpy as np
from chromadb.config import Settings

# Thêm thư mục gốc vào sys.path để import cleaner
sys.path.append(os.path.abspath("../BTTH3"))


def load_config():
    """Load configuration from JSON file."""
    try:
        with open("../BTTH3/index_config.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print(" Không tìm thấy file index_config.json")
        sys.exit(1)
    except json.JSONDecodeError:
        print(" File index_config.json không hợp lệ")
        sys.exit(1)


def initialize_client(config):
    """Initialize ChromaDB client and collection."""
    try:
        client = chromadb.PersistentClient(path=config["persist_directory"])

        # Kiểm tra collection có tồn tại không
        try:
            collection = client.get_collection(config["collection_name"])
            print(f" Kết nối thành công với collection: {config['collection_name']}")
            return client, collection
        except Exception as e:
            print(
                f" Không thể kết nối với collection '{config['collection_name']}': {e}"
            )
            print(" Hãy chắc chắn rằng bạn đã chạy script indexing trước đó")
            sys.exit(1)

    except Exception as e:
        print(f" Lỗi khi khởi tạo ChromaDB client: {e}")
        sys.exit(1)


def load_sample_data(embedding_dir, n_samples=10):
    """Load sample data from embedding files."""
    if not os.path.exists(embedding_dir):
        print(f" Thư mục embedding không tồn tại: {embedding_dir}")
        sys.exit(1)

    files = [f for f in os.listdir(embedding_dir) if f.endswith(".npy")]
    if not files:
        print(f" Không tìm thấy file embedding nào trong: {embedding_dir}")
        sys.exit(1)

    print(f"📂 Tìm thấy {len(files)} file embedding")

    samples = []
    selected_files = random.sample(files, min(n_samples, len(files)))

    for file in selected_files:
        file_id = file.replace(".npy", "")
        path = os.path.join(embedding_dir, file)

        try:
            vectors = np.load(path)

            # Xử lý shape của vectors
            if len(vectors.shape) == 1:
                vectors = [vectors.tolist()]
            else:
                vectors = vectors.tolist()

            # Lấy random một vector từ file này
            if vectors:
                random_idx = random.randint(0, len(vectors) - 1)
                chunk_id = f"{file_id}_{random_idx}"
                samples.append((chunk_id, vectors[random_idx]))

                if len(samples) >= n_samples:
                    break

        except Exception as e:
            print(f" Lỗi khi load file {file}: {e}")
            continue

    print(f" Đã chuẩn bị {len(samples)} sample queries")
    return samples


def perform_search(collection, samples, k=5):
    """Perform similarity search for all samples."""
    results = []

    print(f"🔍 Bắt đầu truy vấn {len(samples)} samples...")

    for i, (chunk_id, vec) in enumerate(samples, 1):
        try:
            print(f"  [{i}/{len(samples)}] Truy vấn: {chunk_id}")

            query_result = collection.query(
                query_embeddings=[vec],
                n_results=k,
                include=["distances", "metadatas", "documents"],
            )

            # Xử lý kết quả
            ids = query_result["ids"][0]
            distances = query_result["distances"][0]
            metadatas = query_result["metadatas"][0]
            documents = query_result["documents"][0]

            search_results = []
            for rank, (res_id, score, meta, doc) in enumerate(
                zip(ids, distances, metadatas, documents)
            ):
                similarity = 1 - score
                law_id = meta.get("law_id", "N/A")
                title = meta.get("title", "N/A")
                date = meta.get("date", "N/A")
                chunk_num = res_id.split("_")[-1]

                search_results.append(
                    {
                        "rank": rank + 1,
                        "id": res_id,
                        "law_id": law_id,
                        "title": title,
                        "date": date,
                        "chunk_num": chunk_num,
                        "similarity": similarity,
                        "distance": score,
                        "document": (
                            doc[:200] + "..." if len(doc) > 200 else doc
                        ),  # Truncate long documents
                    }
                )

            results.append({"query_id": chunk_id, "results": search_results})

        except Exception as e:
            print(f" Lỗi khi truy vấn {chunk_id}: {e}")
            continue

    print(f" Hoàn thành truy vấn {len(results)} samples thành công")
    return results


def generate_markdown_report(results, output_path):
    """Generate markdown report from search results."""
    results_md = [
        "#  Kết quả Truy vấn Tương tự (Top-5)\n",
        f"**Thời gian tạo:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Tổng số truy vấn:** {len(results)}\n",
        "---\n",
    ]

    for i, result in enumerate(results, 1):
        query_id = result["query_id"]
        search_results = result["results"]

        results_md.append(f"## 🔹 Query {i}: `{query_id}`\n")

        if not search_results:
            results_md.append(" Không có kết quả nào được tìm thấy\n")
            continue

        # Thêm bảng kết quả
        results_md.append(
            "| Rank | ID | Luật | Tiêu đề | Ngày | Chunk | Similarity | Distance |"
        )
        results_md.append(
            "|------|----|----- |---------|------|-------|------------|----------|"
        )

        for res in search_results:
            results_md.append(
                f"| {res['rank']} | `{res['id']}` | `{res['law_id']}` | **{res['title'][:50]}{'...' if len(res['title']) > 50 else ''}** | {res['date']} | {res['chunk_num']} | {res['similarity']:.4f} | {res['distance']:.4f} |"
            )

        results_md.append("")

        # Thêm nội dung document đầu tiên
        if search_results:
            best_match = search_results[0]
            results_md.append(f"**Nội dung tương tự nhất:**")
            results_md.append(f"```")
            results_md.append(best_match["document"])
            results_md.append(f"```")
            results_md.append("")

        results_md.append("---\n")

    # Thêm thống kê tổng quan
    results_md.append("## Thống kê Tổng quan\n")

    # Thống kê similarity scores
    all_similarities = []
    for result in results:
        for res in result["results"]:
            all_similarities.append(res["similarity"])

    if all_similarities:
        avg_similarity = np.mean(all_similarities)
        max_similarity = np.max(all_similarities)
        min_similarity = np.min(all_similarities)

        results_md.append(f"- **Similarity trung bình:** {avg_similarity:.4f}")
        results_md.append(f"- **Similarity cao nhất:** {max_similarity:.4f}")
        results_md.append(f"- **Similarity thấp nhất:** {min_similarity:.4f}")
        results_md.append("")

    # Thống kê theo luật
    law_counts = {}
    for result in results:
        for res in result["results"]:
            law_id = res["law_id"]
            law_counts[law_id] = law_counts.get(law_id, 0) + 1

    if law_counts:
        results_md.append("### 📚 Phân bố theo Luật:")
        sorted_laws = sorted(law_counts.items(), key=lambda x: x[1], reverse=True)
        for law_id, count in sorted_laws[:10]:  # Top 10
            results_md.append(f"- **{law_id}:** {count} kết quả")

    # Lưu file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results_md))

    print(f" Đã lưu báo cáo tại: {output_path}")


def main():
    """Main function to run the search test."""
    print(" Bắt đầu kiểm tra tìm kiếm tương tự...")

    # Cấu hình
    config = load_config()
    embedding_dir = "../BTTH3/data/processed/embeddings"
    k = 5  # top-k
    n_samples = 10  # số sample query

    # Khởi tạo client và collection
    client, collection = initialize_client(config)

    # Kiểm tra số lượng documents trong collection
    try:
        total_docs = collection.count()
        print(f" Collection hiện có {total_docs:,} documents")

        if total_docs == 0:
            print(" Collection trống! Hãy chạy script indexing trước")
            sys.exit(1)

    except Exception as e:
        print(f" Không thể đếm documents: {e}")

    # Load sample data
    samples = load_sample_data(embedding_dir, n_samples)

    if not samples:
        print(" Không thể tạo sample data")
        sys.exit(1)

    # Perform search
    results = perform_search(collection, samples, k)

    if not results:
        print(" Không có kết quả nào")
        sys.exit(1)

    # Generate report
    output_path = "../BTTH3/docs/search_results.md"
    generate_markdown_report(results, output_path)

    print(" Hoàn thành kiểm tra tìm kiếm!")
    print(f" Đã test {len(results)} queries với {k} kết quả mỗi query")
    print(f" Xem báo cáo chi tiết tại: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n Lỗi không mong muốn: {e}")
        traceback.print_exc()
