import sys
import psycopg2
import sys

def test_db_connection():
    try:
        # 使用用户提供的连接信息
        conn = psycopg2.connect(
            host="10.208.112.57",
            database="quant_db",
            user="quant_user",
            password="quant_pass"
        )
        
        # 创建游标对象
        cur = conn.cursor()
        
        # 执行简单的SQL查询
        cur.execute("SELECT version();")
        
        # 获取查询结果
        db_version = cur.fetchone()
        print(f"成功连接到数据库! 数据库版本: {db_version[0]}")
        
        # 关闭游标和连接
        cur.close()
        conn.close()
        
        return True
    except psycopg2.OperationalError as e:
        print(f"连接数据库失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

if __name__ == "__main__":
    print("正在尝试连接到远程PostgreSQL数据库...")
    success = test_db_connection()
    sys.exit(0 if success else 1)
