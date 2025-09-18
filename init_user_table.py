import psycopg2
import bcrypt

# 创建初始化数据库用户表的函数
def init_user_table():
    try:
        # 使用提供的连接信息连接到数据库
        conn = psycopg2.connect(
            host="10.208.112.57",
            database="quant_db",
            user="quant_user",
            password="quant_pass"
        )
        
        # 创建游标对象
        cur = conn.cursor()
        
        print("成功连接到数据库!")
        
        # 创建用户表，如果不存在
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active'
        )
        """
        cur.execute(create_table_query)
        print("用户表创建成功!")
        
        # 检查是否已经存在管理员用户
        check_admin_query = "SELECT id FROM users WHERE username = 'admin'"
        cur.execute(check_admin_query)
        admin_exists = cur.fetchone()
        
        if not admin_exists:
            # 为管理员密码创建哈希值
            # 注意：在实际生产环境中，应该使用更安全的密码策略
            admin_password = "123456"
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            
            # 插入管理员用户数据
            insert_admin_query = """
            INSERT INTO users (username, email, password, phone, role)
            VALUES (%s, %s, %s, %s, %s)
            """
            admin_data = (
                'admin',
                'admin@example.com',
                hashed_password.decode('utf-8'),
                '13800138000',
                'admin'
            )
            cur.execute(insert_admin_query, admin_data)
            print("管理员用户插入成功!")
        else:
            print("管理员用户已存在，跳过插入!")
        
        # 提交事务
        conn.commit()
        
        # 关闭游标和连接
        cur.close()
        conn.close()
        
        print("数据库初始化完成!")
        return True
    except psycopg2.OperationalError as e:
        print(f"连接数据库失败: {e}")
        return False
    except psycopg2.Error as e:
        print(f"数据库操作错误: {e}")
        # 发生错误时回滚事务
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        # 发生错误时回滚事务
        if conn:
            conn.rollback()
        return False

# 执行初始化函数
if __name__ == "__main__":
    print("正在初始化远程数据库用户表...")
    success = init_user_table()
    exit_code = 0 if success else 1
    import sys
    sys.exit(exit_code)