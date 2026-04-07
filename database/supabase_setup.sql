-- This script sets up the necessary tables for the TGMarket bot in your Supabase project

-- 1. Create Channels Table
CREATE TABLE public.channels (
    id SERIAL PRIMARY KEY,
    category VARCHAR NOT NULL UNIQUE,
    channel_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL
);

-- 2. Create Listings Table
CREATE TABLE public.listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    category VARCHAR NOT NULL,
    region VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    price VARCHAR NOT NULL,
    contact VARCHAR NOT NULL,
    photos TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Note: We disable RLS (Row Level Security) for now so the bot can freely access the tables
-- In a production environment with web clients, you would want to configure specific RLS policies
ALTER TABLE public.channels DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.listings DISABLE ROW LEVEL SECURITY;

-- Insert initial empty channels (You can update the channel_id later once you create them)
-- Replace @your_tech_channel with the actual channel usernames
INSERT INTO public.channels (category, channel_id, name) VALUES 
('phones', '@your_phones_channel', '📱 Телефоны'),
('cars', '@your_cars_channel', '🚗 Автомобили'),
('realty', '@your_realty_channel', '🏠 Недвижимость');
