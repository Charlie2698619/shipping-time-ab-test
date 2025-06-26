USE ecommerce_ab_test;

-- USERS
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    sign_up_date DATETIME,
    region VARCHAR(100),
    device_type VARCHAR(20),
    channel VARCHAR(50),
    tenure_days INT,
    is_premium BOOLEAN
);

-- STORES
CREATE TABLE stores (
    store_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(100),
    location VARCHAR(100),
    store_type VARCHAR(50)
);

-- ORDERS
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    store_id INT,
    logistics_id INT,
    order_date DATETIME,
    shipped_time DATETIME,
    received_time DATETIME,
    order_status ENUM('delivered', 'cancelled', 'returned'),
    product_category VARCHAR(100),
    total_value FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- ORDER ITEMS
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_name VARCHAR(100),
    category VARCHAR(100),
    quantity INT,
    price FLOAT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- LOGISTICS
CREATE TABLE logistics (
    logistics_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    logistics_company VARCHAR(100),
    shipping_method VARCHAR(50),
    expected_delivery INT,
    actual_delivery INT,
    delay_hours INT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- USER BEHAVIORS
CREATE TABLE user_behaviors (
    behavior_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    behavior_type VARCHAR(50),
    product_category VARCHAR(100),
    referral_source VARCHAR(100),
    event_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- REVIEWS
CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    order_id INT,
    satisfaction INT,
    delivery_rating INT,
    review_text TEXT,
    review_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);