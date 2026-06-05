import pytds

server = '192.168.150.26'
database = 'EOS'
username = 'winkart'
password = 'sa@123'
port = 1433

try:
    print("Connecting to SQL Server via pure python...")
    with pytds.connect(
        server=server, 
        database=database, 
        user=username, 
        password=password, 
        port=port
    ) as conn:
        with conn.cursor() as cursor:
            # تست اجرای یک کوئری ساده
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            print("\n✅ اتصال با موفقیت برقرار شد!")
            print(f"🔹 نسخه دیتابیس سرور:\n{row[0]}")
            
except Exception as e:
    print(f"\n❌ خطا در اتصال: {e}")
