FROM python:3.11-slim

WORKDIR /app

COPY be/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/kitchen.proto /proto/kitchen.proto
COPY be/ .

RUN mkdir -p app/grpc && \
    python -m grpc_tools.protoc \
      -I /proto \
      --python_out=app/grpc \
      --grpc_python_out=app/grpc \
      /proto/kitchen.proto && \
    sed -i 's/^import kitchen_pb2/from . import kitchen_pb2/' app/grpc/kitchen_pb2_grpc.py && \
    touch app/grpc/__init__.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
