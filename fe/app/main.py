import os

import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "frontend_secret_key"
API = os.getenv("API_BASE_URL", "http://localhost:8000")

ESTADOS_ES = {
    "received": "Recibida",
    "preparing": "En preparación",
    "ready": "Lista",
    "delivered": "Entregada",
    "cancelled": "Cancelada",
}

CATEGORIAS_ES = {
    "main": "Plato fuerte",
    "drink": "Bebida",
    "dessert": "Postre",
}


def auth_headers():
    token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def require_login():
    if not session.get("token"):
        return redirect(url_for("login"))
    return None


def parse_error(response):
    try:
        payload = response.json()
        detail = payload.get("detail", "La solicitud falló")
        if isinstance(detail, list):
            return "Error de validación en los datos enviados"
        if detail == "Invalid credentials":
            return "Credenciales inválidas"
        return str(detail)
    except ValueError:
        return "La solicitud falló"


@app.context_processor
def inject_helpers():
    return {
        "estado_es": lambda value: ESTADOS_ES.get(value, value),
        "categoria_es": lambda value: CATEGORIAS_ES.get(value, value.capitalize() if isinstance(value, str) else value),
    }


@app.get("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        payload = {
            "username": request.form.get("username", "").strip(),
            "email": request.form.get("email", "").strip(),
            "password": request.form.get("password", ""),
            "full_name": request.form.get("full_name", "").strip() or None,
        }
        response = requests.post(f"{API}/auth/register", json=payload, timeout=10)
        if response.status_code == 201:
            flash("Registro exitoso. Ahora inicia sesión.", "success")
            return redirect(url_for("login"))
        flash(parse_error(response), "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        payload = {
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", ""),
        }
        response = requests.post(f"{API}/auth/login", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            session["token"] = data["access_token"]
            session["username"] = payload["username"]
            flash("¡Bienvenido de nuevo!", "success")
            return redirect(url_for("dashboard"))
        flash("Credenciales inválidas", "error")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/dashboard")
def dashboard():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    response = requests.get(f"{API}/orders/mine", headers=auth_headers(), timeout=10)
    orders = response.json() if response.ok else []
    return render_template("dashboard.html", orders=orders)


@app.route("/menu", methods=["GET"])
def menu():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    response = requests.get(f"{API}/menu/all", headers=auth_headers(), timeout=10)
    items = response.json() if response.ok else []
    return render_template("menu.html", items=items)


@app.route("/menu/add", methods=["GET", "POST"])
def add_menu_item():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        payload = {
            "name": request.form.get("name", "").strip(),
            "description": request.form.get("description", "").strip() or None,
            "price": request.form.get("price", "0"),
            "category": request.form.get("category", "").strip(),
            "is_available": request.form.get("is_available") == "on",
        }
        response = requests.post(
            f"{API}/menu/",
            headers=auth_headers(),
            json=payload,
            timeout=10,
        )
        if response.status_code == 201:
            flash("Platillo agregado correctamente.", "success")
            return redirect(url_for("menu"))
        flash(parse_error(response), "error")

    return render_template("add_menu_item.html")


@app.post("/menu/<int:item_id>/toggle")
def toggle_menu_item(item_id: int):
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    requests.patch(f"{API}/menu/{item_id}/toggle", headers=auth_headers(), timeout=10)
    flash("Disponibilidad actualizada.", "success")
    return redirect(url_for("menu"))


@app.get("/orders")
def orders():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    response = requests.get(f"{API}/orders/", headers=auth_headers(), timeout=10)
    orders_data = response.json() if response.ok else []
    return render_template("orders.html", orders=orders_data)


@app.route("/orders/new", methods=["GET", "POST"])
def new_order():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response

    menu_response = requests.get(f"{API}/menu/", headers=auth_headers(), timeout=10)
    items = menu_response.json() if menu_response.ok else []

    if request.method == "POST":
        selected_items = []
        for item in items:
            qty_raw = request.form.get(f"qty_{item['id']}", "0")
            try:
                qty = int(qty_raw)
            except ValueError:
                qty = 0
            if qty > 0:
                selected_items.append(
                    {
                        "menu_item_id": item["id"],
                        "quantity": qty,
                        "notes": request.form.get(f"note_{item['id']}") or None,
                    }
                )

        payload = {
            "table_number": int(request.form.get("table_number", "0") or 0),
            "notes": request.form.get("notes", "").strip() or None,
            "items": selected_items,
        }
        response = requests.post(
            f"{API}/orders/",
            headers=auth_headers(),
            json=payload,
            timeout=10,
        )
        if response.status_code == 201:
            flash("Orden creada correctamente.", "success")
            return redirect(url_for("dashboard"))
        if response.status_code == 422:
            flash("Algunos platillos no están disponibles o faltan datos.", "error")
        else:
            flash(parse_error(response), "error")

    return render_template("new_order.html", items=items)


@app.post("/orders/<int:order_id>/status")
def update_order_status(order_id: int):
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    status_value = request.form.get("status", "")
    response = requests.patch(
        f"{API}/orders/{order_id}/status",
        headers=auth_headers(),
        json={"status": status_value},
        timeout=10,
    )
    if response.status_code == 422:
        flash("Transición de estado inválida.", "error")
    elif response.ok:
        flash("Estado de la orden actualizado.", "success")
    else:
        flash(parse_error(response), "error")
    return redirect(request.referrer or url_for("orders"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
