-- ============================================================================
--  TableFlow — MySQL 8 Database Schema
--  Engine: InnoDB | Charset: utf8mb4 | Collation: utf8mb4_unicode_ci
-- ============================================================================

CREATE DATABASE IF NOT EXISTS tableflow
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE tableflow;

-- ----------------------------------------------------------------------------
--  USERS
--  role distinguishes waiters (order-takers) from managers (menu editors).
--  password_hash stores only the result of a one-way hashing algorithm.
--  Plain-text passwords must never be persisted.
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id            INT          NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100)     NULL,
    role          ENUM('waiter','manager') NOT NULL DEFAULT 'waiter',
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_users          PRIMARY KEY (id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email)
);

-- ----------------------------------------------------------------------------
--  MENU ITEMS
--  Represents a dish or drink that can be added to an order.
--  is_available controls whether the item appears in the active catalog.
-- ----------------------------------------------------------------------------
CREATE TABLE menu_items (
    id            INT            NOT NULL AUTO_INCREMENT,
    name          VARCHAR(150)   NOT NULL,
    description   TEXT               NULL,
    price         DECIMAL(8, 2)  NOT NULL,
    category      VARCHAR(80)    NOT NULL,   -- e.g. appetizer, main, dessert, drink
    is_available  BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_menu_items PRIMARY KEY (id)
);

-- ----------------------------------------------------------------------------
--  ORDERS
--  Represents a table's order session. waiter_id tracks who took the order.
--  Status lifecycle: received → preparing → ready → delivered (or cancelled).
--  The Kitchen gRPC service validates status transitions; the backend
--  persists the result only after receiving a successful acknowledgement.
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    id             INT            NOT NULL AUTO_INCREMENT,
    table_number   INT            NOT NULL,
    waiter_id      INT            NOT NULL,
    status         ENUM(
                     'received',    -- order placed by waiter, awaiting kitchen
                     'preparing',   -- kitchen acknowledged and is cooking
                     'ready',       -- kitchen completed; waiting for delivery
                     'delivered',   -- waiter delivered food to the table
                     'cancelled'    -- order voided
                   )              NOT NULL DEFAULT 'received',
    notes          TEXT               NULL,
    total_amount   DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_orders       PRIMARY KEY (id),
    CONSTRAINT fk_order_waiter FOREIGN KEY (waiter_id)
        REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
--  ORDER ITEMS
--  Each row is one line item within an order. unit_price is captured at
--  order time so future price changes to menu_items do not distort history.
-- ----------------------------------------------------------------------------
CREATE TABLE order_items (
    id             INT           NOT NULL AUTO_INCREMENT,
    order_id       INT           NOT NULL,
    menu_item_id   INT           NOT NULL,
    quantity       INT           NOT NULL DEFAULT 1,
    unit_price     DECIMAL(8, 2) NOT NULL,
    notes          VARCHAR(255)      NULL,

    CONSTRAINT pk_order_items    PRIMARY KEY (id),
    CONSTRAINT fk_oi_order       FOREIGN KEY (order_id)
        REFERENCES orders(id)     ON DELETE CASCADE  ON UPDATE CASCADE,
    CONSTRAINT fk_oi_menu_item   FOREIGN KEY (menu_item_id)
        REFERENCES menu_items(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
--  NOTIFICATIONS
--  Persisted for every order-lifecycle event. When an order is marked "ready"
--  by the kitchen gRPC service, the backend immediately pushes the notification
--  through the open WebSocket channel so the waiter's page updates in real time.
-- ----------------------------------------------------------------------------
CREATE TABLE notifications (
    id               INT          NOT NULL AUTO_INCREMENT,
    user_id          INT          NOT NULL,
    title            VARCHAR(255) NOT NULL,
    message          TEXT         NOT NULL,
    type             ENUM(
                       'order_received',    -- sent to waiter confirming order was queued
                       'order_ready',       -- sent to waiter when kitchen marks order ready
                       'order_cancelled',   -- sent to waiter when order is cancelled
                       'general'
                     )            NOT NULL DEFAULT 'general',
    is_read          BOOLEAN      NOT NULL DEFAULT FALSE,
    related_order_id INT              NULL,   -- optional reference to the order involved
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_notifications       PRIMARY KEY (id),
    CONSTRAINT fk_notif_user          FOREIGN KEY (user_id)
        REFERENCES users(id)  ON DELETE CASCADE  ON UPDATE CASCADE,
    CONSTRAINT fk_notif_order         FOREIGN KEY (related_order_id)
        REFERENCES orders(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------------
--  INDEXES  — tuned for the most common application queries
-- ----------------------------------------------------------------------------

-- Fetch all orders placed by a specific waiter (dashboard)
CREATE INDEX idx_orders_waiter      ON orders (waiter_id);

-- Filter orders by current status (kitchen queue view)
CREATE INDEX idx_orders_status      ON orders (status);

-- Fetch all line items belonging to an order
CREATE INDEX idx_order_items_order  ON order_items (order_id);

-- Fetch available menu items by category (menu catalog)
CREATE INDEX idx_menu_available     ON menu_items (is_available, category);

-- Fetch unread notifications for a user (notification badge)
CREATE INDEX idx_notif_user_unread  ON notifications (user_id, is_read);

-- ============================================================================


-- ----------------------------------------------------------------------------
--  SEED DATA
--  Demo users, menu items, orders, order items, and notifications for
--  classroom walkthroughs and quick testing.
-- ----------------------------------------------------------------------------
INSERT INTO users (id, username, email, password_hash, full_name, role)
VALUES
    (1, 'admin', 'admin@tableflow.local', '$2b$12$CvUjgWJeE2Er92BREXjKleRzyOEptsn.TUBuqQAv0zo24OxqsbnNy', 'Andrea Manager', 'manager'),
    (2, 'mesero1', 'mesero1@tableflow.local', '$2b$12$KgNDLvzLBAwrB/LlnYaMvOv5UFifpf05eRb0LHuS1lnPguZIHqmdK', 'Carlos Mesero', 'waiter')
ON DUPLICATE KEY UPDATE
    username = VALUES(username),
    email = VALUES(email),
    password_hash = VALUES(password_hash),
    full_name = VALUES(full_name),
    role = VALUES(role);

INSERT INTO menu_items (id, name, description, price, category, is_available)
VALUES
    (1, 'Hamburguesa Clásica', 'Carne a la parrilla, queso cheddar, lechuga y tomate.', 8.50, 'main', TRUE),
    (2, 'Pasta Alfredo con Pollo', 'Pasta cremosa con pollo salteado y parmesano.', 10.25, 'main', TRUE),
    (3, 'Tacos de Birria', 'Tres tacos con consomé y cebolla morada.', 9.75, 'main', TRUE),
    (4, 'Limonada Natural', 'Limonada fresca endulzada con jarabe de caña.', 2.75, 'drink', TRUE),
    (5, 'Cheesecake de Fresa', 'Porción individual con salsa de fresa.', 4.50, 'dessert', TRUE)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    price = VALUES(price),
    category = VALUES(category),
    is_available = VALUES(is_available);

INSERT INTO orders (id, table_number, waiter_id, status, notes, total_amount)
VALUES
    (1, 3, 2, 'ready', 'Mesa con cliente alérgico a la cebolla. Confirmar antes de entregar.', 14.00),
    (2, 7, 2, 'delivered', 'Celebración de cumpleaños. Llevar servilletas extra.', 19.50)
ON DUPLICATE KEY UPDATE
    table_number = VALUES(table_number),
    waiter_id = VALUES(waiter_id),
    status = VALUES(status),
    notes = VALUES(notes),
    total_amount = VALUES(total_amount);

INSERT INTO order_items (id, order_id, menu_item_id, quantity, unit_price, notes)
VALUES
    (1, 1, 1, 1, 8.50, 'Sin cebolla'),
    (2, 1, 4, 2, 2.75, 'Poco hielo'),
    (3, 2, 2, 1, 10.25, NULL),
    (4, 2, 5, 1, 4.50, 'Con vela de cumpleaños'),
    (5, 2, 4, 2, 2.75, NULL)
ON DUPLICATE KEY UPDATE
    order_id = VALUES(order_id),
    menu_item_id = VALUES(menu_item_id),
    quantity = VALUES(quantity),
    unit_price = VALUES(unit_price),
    notes = VALUES(notes);

INSERT INTO notifications (id, user_id, title, message, type, is_read, related_order_id)
VALUES
    (1, 2, 'Orden #1 lista', 'La cocina marcó la orden #1 como lista para entregar a la mesa 3.', 'order_ready', FALSE, 1),
    (2, 2, 'Orden #2 entregada', 'La orden #2 ya fue entregada correctamente a la mesa 7.', 'general', TRUE, 2),
    (3, 1, 'Demo cargada', 'La base de datos de demostración se cargó con usuarios, menú y órdenes.', 'general', FALSE, NULL)
ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id),
    title = VALUES(title),
    message = VALUES(message),
    type = VALUES(type),
    is_read = VALUES(is_read),
    related_order_id = VALUES(related_order_id);

ALTER TABLE users AUTO_INCREMENT = 3;
ALTER TABLE menu_items AUTO_INCREMENT = 6;
ALTER TABLE orders AUTO_INCREMENT = 3;
ALTER TABLE order_items AUTO_INCREMENT = 6;
ALTER TABLE notifications AUTO_INCREMENT = 4;
