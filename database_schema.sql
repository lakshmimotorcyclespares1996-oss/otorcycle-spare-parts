-- Lakshmi MotorCycle Parts Database Schema
-- Updated to work with existing bot structure
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (matches your existing bot structure)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table (for additional user information)
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    wishlist JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spare parts table (your existing structure)
CREATE TABLE IF NOT EXISTS spare_parts (
    id SERIAL PRIMARY KEY,
    part_name VARCHAR(255) NOT NULL,
    description TEXT,
    part_category VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock_qty INTEGER NOT NULL DEFAULT 0,
    image_url TEXT,
    part_number VARCHAR(100),
    bike_brand VARCHAR(100) NOT NULL,
    bike_model VARCHAR(100) NOT NULL,
    year_from INTEGER NOT NULL,
    year_to INTEGER NOT NULL,
    color VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cart table (matches your existing bot structure)
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    part_name VARCHAR(255) NOT NULL,
    bike_brand VARCHAR(100) NOT NULL,
    bike_model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    color VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders table (enhanced version of your existing structure)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_id VARCHAR(100) UNIQUE,
    items JSONB NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    full_name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages table (updated to use user_id)
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    is_customer BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Part interest logs (from your existing bot)
CREATE TABLE IF NOT EXISTS part_interest_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    part_name VARCHAR(255) NOT NULL,
    bike_brand VARCHAR(100) NOT NULL,
    bike_model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    bike_info VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_spare_parts_category ON spare_parts(part_category);
CREATE INDEX IF NOT EXISTS idx_spare_parts_brand ON spare_parts(bike_brand);
CREATE INDEX IF NOT EXISTS idx_spare_parts_model ON spare_parts(bike_model);
CREATE INDEX IF NOT EXISTS idx_spare_parts_name ON spare_parts USING gin(to_tsvector('english', part_name));
CREATE INDEX IF NOT EXISTS idx_cart_user_id ON cart(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_part_interest_logs_user_id ON part_interest_logs(user_id);

-- Insert sample data (enhanced with your categories)
INSERT INTO spare_parts (part_name, description, part_category, price, stock_qty, part_number, bike_brand, bike_model, year_from, year_to, color) VALUES
('Brake Pad Set - Front', 'High-quality ceramic brake pads for front wheels', 'Brake System', 800.00, 25, 'BP001', 'Honda', 'CB350', 2020, 2024, NULL),
('Engine Oil Filter', 'Premium oil filter for 4-stroke engines', 'Engine Parts', 450.00, 15, 'OF002', 'Yamaha', 'FZ-S', 2019, 2024, NULL),
('Spark Plug Set', 'Iridium spark plugs for better performance', 'Electrical', 300.00, 50, 'SP003', 'TVS', 'Apache 160', 2018, 2024, NULL),
('Chain Set', 'Heavy-duty chain and sprocket set', 'Transmission', 1200.00, 10, 'CS004', 'Bajaj', 'Pulsar 150', 2017, 2024, NULL),
('Headlight Assembly', 'LED headlight with DRL', 'Body Parts', 2500.00, 8, 'HL005', 'Hero', 'Splendor Plus', 2019, 2024, 'Black'),
('Headlight Assembly', 'LED headlight with DRL', 'Body Parts', 2500.00, 8, 'HL005', 'Hero', 'Splendor Plus', 2019, 2024, 'Silver'),
('Rear Shock Absorber', 'Gas-filled rear shock absorber', 'Suspension', 1800.00, 12, 'SA006', 'KTM', 'Duke 200', 2020, 2024, NULL),
('Air Filter', 'High-flow air filter for better airflow', 'Engine Parts', 350.00, 30, 'AF007', 'Royal Enfield', 'Classic 350', 2018, 2024, NULL),
('Clutch Plate Set', 'Friction clutch plates for smooth operation', 'Transmission', 900.00, 18, 'CP008', 'Suzuki', 'Gixxer 150', 2019, 2024, NULL),
('Battery 12V', 'Maintenance-free motorcycle battery', 'Electrical', 1500.00, 20, 'BT009', 'Universal', 'Universal', 2015, 2024, NULL),
('Brake Disc - Rear', 'Stainless steel brake disc for rear wheel', 'Brake System', 1100.00, 15, 'BD010', 'Honda', 'CBR600RR', 2020, 2024, NULL),
('Side Panel - Left', 'OEM quality side panel', 'Body Parts', 800.00, 12, 'SP011', 'Yamaha', 'R15', 2019, 2024, 'Blue'),
('Side Panel - Left', 'OEM quality side panel', 'Body Parts', 800.00, 12, 'SP011', 'Yamaha', 'R15', 2019, 2024, 'Red'),
('Side Panel - Left', 'OEM quality side panel', 'Body Parts', 800.00, 12, 'SP011', 'Yamaha', 'R15', 2019, 2024, 'Black');

-- Insert sample user (for testing)
INSERT INTO users (user_id, username, first_name, phone) VALUES
(123456789, 'testuser', 'Test User', '+91 9876543210')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_profiles (user_id, full_name, phone, address) VALUES
(123456789, 'Test User', '+91 9876543210', '123 Test Street, Test City, Test State 12345')
ON CONFLICT (user_id) DO NOTHING;

-- Create functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_spare_parts_updated_at ON spare_parts;
CREATE TRIGGER update_spare_parts_updated_at BEFORE UPDATE ON spare_parts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for better security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE spare_parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your security requirements)
CREATE POLICY "Enable read access for all users" ON users FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON users FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON user_profiles FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON user_profiles FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON user_profiles FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON spare_parts FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON spare_parts FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON spare_parts FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON cart FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON cart FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON cart FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON cart FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON orders FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON orders FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON chat_messages FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON chat_messages FOR INSERT WITH CHECK (true);

-- Create a view for order details with customer information
CREATE OR REPLACE VIEW order_details AS
SELECT 
    o.*,
    u.first_name as customer_name,
    u.username as customer_username,
    COALESCE(up.phone, u.phone) as customer_phone,
    up.full_name as customer_full_name
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id
LEFT JOIN user_profiles up ON o.user_id = up.user_id;

-- Create a function to search parts (enhanced version)
CREATE OR REPLACE FUNCTION search_parts(
    search_term TEXT DEFAULT '', 
    category_filter TEXT DEFAULT '',
    brand_filter TEXT DEFAULT '',
    model_filter TEXT DEFAULT ''
)
RETURNS TABLE (
    id INTEGER,
    part_name VARCHAR(255),
    description TEXT,
    part_category VARCHAR(100),
    price DECIMAL(10,2),
    stock_qty INTEGER,
    image_url TEXT,
    part_number VARCHAR(100),
    bike_brand VARCHAR(100),
    bike_model VARCHAR(100),
    year_from INTEGER,
    year_to INTEGER,
    color VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.part_name, p.description, p.part_category, p.price, p.stock_qty, 
           p.image_url, p.part_number, p.bike_brand, p.bike_model, p.year_from, p.year_to, p.color
    FROM spare_parts p
    WHERE 
        (search_term = '' OR p.part_name ILIKE '%' || search_term || '%' 
         OR p.description ILIKE '%' || search_term || '%'
         OR p.part_number ILIKE '%' || search_term || '%'
         OR p.bike_brand ILIKE '%' || search_term || '%'
         OR p.bike_model ILIKE '%' || search_term || '%')
    AND (category_filter = '' OR p.part_category = category_filter)
    AND (brand_filter = '' OR p.bike_brand = brand_filter)
    AND (model_filter = '' OR p.bike_model = model_filter)
    AND p.stock_qty > 0
    ORDER BY p.part_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to get popular parts
CREATE OR REPLACE FUNCTION get_popular_parts(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    id INTEGER,
    part_name VARCHAR(255),
    bike_brand VARCHAR(100),
    bike_model VARCHAR(100),
    price DECIMAL(10,2),
    interest_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.part_name, p.bike_brand, p.bike_model, p.price, COUNT(pil.id) as interest_count
    FROM spare_parts p
    LEFT JOIN part_interest_logs pil ON p.part_name = pil.part_name 
        AND p.bike_brand = pil.bike_brand 
        AND p.bike_model = pil.bike_model
    WHERE p.stock_qty > 0
    GROUP BY p.id, p.part_name, p.bike_brand, p.bike_model, p.price
    ORDER BY interest_count DESC, p.part_name
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;