import asyncio
import asyncpg

async def main():
    dsn = "postgresql://postgres.zxdfjroqonxochnoyujn:LeadGen2026Password@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    print("Connecting to Supabase database...")
    conn = await asyncpg.connect(dsn)
    try:
        print("Creating tables...")
        # 1. Create product_service_type
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.product_service_type (
                id SERIAL PRIMARY KEY,
                type TEXT NOT NULL,
                category_type TEXT NOT NULL
            );
        """)
        
        # 2. Create product_service_name
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.product_service_name (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                product_service_type_id INT REFERENCES public.product_service_type(id) ON DELETE CASCADE,
                category_type TEXT NOT NULL
            );
        """)
        
        # 3. Create product_services
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.product_services (
                id SERIAL PRIMARY KEY,
                category_type TEXT,
                product_service_type TEXT,
                product_service_name TEXT
            );
        """)
        
        # 4. Create leads
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.leads (
                id SERIAL PRIMARY KEY,
                name TEXT,
                title TEXT,
                company TEXT,
                email TEXT,
                phone TEXT,
                website TEXT,
                location TEXT,
                linkedin TEXT,
                segment TEXT,
                priority TEXT,
                channel TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT TRUE,
                email_sent BOOLEAN DEFAULT FALSE,
                email_sent_date TIMESTAMP WITHOUT TIME ZONE,
                email_status VARCHAR(50),
                email_error TEXT
            );
        """)
        
        # 5. Create email_templates
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.email_templates (
                id SERIAL PRIMARY KEY,
                template_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. Seed data
        print("Seeding mock data...")
        await conn.execute("""
            INSERT INTO public.product_service_type (id, type, category_type) VALUES
            (1, 'Software', 'PACKAGE'),
            (2, 'Consulting', 'SERVICE'),
            (3, 'Maintenance', 'SERVICE')
            ON CONFLICT (id) DO NOTHING;
        """)
        
        await conn.execute("""
            DELETE FROM public.product_service_name;
            INSERT INTO public.product_service_name (name, product_service_type_id, category_type) VALUES
            ('Basic Package', 1, 'PACKAGE'),
            ('Pro Package', 1, 'PACKAGE'),
            ('IT Strategy', 2, 'SERVICE'),
            ('Security Audit', 2, 'SERVICE'),
            ('Server Maintenance', 3, 'SERVICE');
        """)
        
        await conn.execute("""
            DELETE FROM public.product_services;
            INSERT INTO public.product_services (category_type, product_service_type, product_service_name) VALUES
            ('PACKAGE', 'Software', 'Basic Package'),
            ('PACKAGE', 'Software', 'Pro Package'),
            ('SERVICE', 'Consulting', 'IT Strategy'),
            ('SERVICE', 'Consulting', 'Security Audit'),
            ('SERVICE', 'Maintenance', 'Server Maintenance');
        """)
        print("Successfully created tables and seeded data!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
