import weaviate
from weaviate.classes.config import Property, DataType, VectorConfig
from weaviate.classes.config import DataType, Property
from weaviate.classes.init import AdditionalConfig, Timeout

# Kết nối tới Weaviate 
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    additional_config=AdditionalConfig(
        timeout=Timeout(
            query=60, insert=60
        )  # Use Timeout object with query and insert timeouts
    ),
) 

# Kiểm tra nếu collection đã tồn tại
if "Document" not in client.collections.list_all():
    client.collections.create(
        name="Document",
        vector_config=VectorConfig.self_provided(),  # Vì bạn sẽ cung cấp vector thủ công
        properties=[
            Property(name="text", data_type=DataType.TEXT),  # Trường nội dung
            Property(name="metadata", data_type=DataType.JSON),  # Trường metadata dạng JSON
        ],
    )
    print("Collection 'Document' created successfully.")
else:
    print("Collection 'Document' already exists.")
