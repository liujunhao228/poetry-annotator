import sqlite3

try:
    conn = sqlite3.connect('poetry.db')
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # 如果poems表存在，检查数据
    if ('poems',) in tables:
        cursor.execute("SELECT COUNT(*) FROM poems")
        count = cursor.fetchone()[0]
        print(f"Poems count: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM poems LIMIT 3")
            rows = cursor.fetchall()
            print("Sample data:")
            for row in rows:
                print(row)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}") 