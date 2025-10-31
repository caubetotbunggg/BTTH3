import weaviate
from weaviate.classes.query import Filter
from dotenv import load_dotenv
import os
load_dotenv()
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY),
)

try:
    collection = client.collections.get("Document")
    
    law_names_to_delete = [
        "Bộ Luật Lao động sửa đổi, bổ sung năm 2002",
        "Luật sửa đổi, bổ sung một số điều Bộ luật Lao động năm 2006",
        "Bộ luật Lao động 2012, số 10/2012/QH13",
        "Luật sửa đổi Danh mục ngành, nghề kinh doanh có điều kiện của Luật Đầu tư",
        "Luật Đầu tư 2020, số 61/2020/QH14",
        "Luật Đầu tư năm 2014",
        "Luật Phí và Lệ phí, 97/2015/QH13",
        "Luật Đất đai 2013, số 45/2013/QH13",
        "Luật sửa đổi một số điều của Luật Doanh nghiệp tư nhân số 35-L/CTN năm 1994",
        "Luật sửa đổi, bổ sung Điều 170 Luật Doanh nghiệp số 37/2013/QH13",
        "Luật sửa đổi, bổ sung Điều 73 Bộ Luật lao động năm 2007",
        "Luật ban hành văn bản quy phạm pháp luật sửa đổi, bổ sung năm 2002",
        "Luật Doanh nghiệp Nhà nước năm 1995",
        "Luật Doanh nghiệp 2014, số 68/2014/QH13",
        "Bộ luật Dân sự năm 1995",
        "Bộ luật Tố tụng hình sự 1998 số 7-LCT/HĐNN8",
        "Bộ luật Tố tụng hình sự sửa đổi, bổ sung năm 2000",
        "Luật Hôn nhân và gia đình 1986",
        "Luật Hôn nhân và Gia đình năm 2000",
        "Bộ luật Tố tụng dân sự 2004",
        "Luật sửa đổi, bổ sung Bộ Luật Tố tụng dân sự năm 2011",
        "Luật sửa đổi Bộ luật Tố tụng dân sự, Luật Tố tụng hành chính, Luật Tư pháp người chưa thành niên, Luật Phá",
        "Luật Trách nhiệm bồi thường của Nhà nước - 2009",
        "Luật Thi hành án dân sự 2008",
        "Bộ luật Dân sự 2005",
        "Luật các tổ chức tín dụng - 1997",
        "Luật Thương mại 2005",
        "Luật Giao dịch điện tử - 2005",
        "Luật sửa đổi, bổ sung một số điều của Luật các tổ chức tín dụng - 2004",
        "Luật Ngân hàng Nhà nước - 1997",
        "Luật Các tổ chức tín dụng - 2010",
        "Luật Cư trú - 2006",
        "Luật Đất đai - 1987",
        "Luật Đất đai - 1993",
        "Luật Đất đai - 2003",
        "Luật Ngân sách Nhà nước năm 2002",
        "Luật Nhà ở năm 2005",
        "Luật Thuế Sử dụng Đất Nông nghiệp - 1993",
        "Luật Bảo hiểm xã hội - 2006",
        "Luật Bảo hiểm xã hội - 2014"

    ]
    
    for law_name in law_names_to_delete:
        print(f"Đang xóa dữ liệu của: {law_name}")
        
        result = collection.data.delete_many(
            where=Filter.by_property("metadata").equal(law_name)
        )
        
        print(f"  ✅ Đã xóa {result.successful} objects")
        print(f"  ❌ Lỗi: {result.failed}\n")
    
finally:
    client.close()