TableFlow corregido y listo para demostración.

Cómo ejecutar:
1. Abre Docker Desktop.
2. En la raíz del proyecto ejecuta: docker compose down -v
3. Luego ejecuta: docker compose up --build
4. Frontend: http://localhost:5001
5. Documentación del backend: http://localhost:8000/docs
6. Servicio gRPC de cocina: localhost:50051

Datos demo incluidos:
- Usuario administrador: admin / Admin123
- Usuario mesero: mesero1 / Mesero123
- 5 platillos precargados
- 2 órdenes de ejemplo
- 3 notificaciones de ejemplo

Notas:
- Los archivos gRPC se generan durante el build de Docker.
- El proyecto sigue la arquitectura por capas solicitada.
- Si deseas recargar la base con los datos demo, debes borrar el volumen con docker compose down -v.
