from concurrent import futures

import grpc

from app.generated import kitchen_pb2_grpc
from app.servicer import KitchenServicer


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kitchen_pb2_grpc.add_KitchenServiceServicer_to_server(KitchenServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Kitchen gRPC server running on port 50051", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
