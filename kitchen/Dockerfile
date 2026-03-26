FROM python:3.11-slim

WORKDIR /app

COPY kitchen/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/kitchen.proto /proto/kitchen.proto
COPY kitchen/ .

RUN mkdir -p app/generated && \
    python -m grpc_tools.protoc \
      -I /proto \
      --python_out=app/generated \
      --grpc_python_out=app/generated \
      /proto/kitchen.proto && \
    sed -i 's/^import kitchen_pb2/from . import kitchen_pb2/' app/generated/kitchen_pb2_grpc.py && \
    touch app/generated/__init__.py

CMD ["python", "-m", "app.server"]