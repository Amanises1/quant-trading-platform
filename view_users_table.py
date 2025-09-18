import psycopg2
import json

# 数据库连接参数
db_params = {
    'host': '10.208.112.57',
    'database': 'quant_db',
    'user': 'quant_user',
    'password': 'quant_pass'
}

def view_users_table():
    """查看users表中的所有数据"""
    try:
        # 连接到数据库
        conn = psycopg2.connect(**db_params)
        print("成功连接到数据库")
        
        # 创建游标对象
        cur = conn.cursor()
        
        # 检查users表是否存在
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        )
        """
        cur.execute(check_table_query)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("users表不存在")
            return
        
        # 查询users表中的所有数据（注意：为了安全，不显示密码字段）
        # 实际生产环境中不应该显示敏感信息
        query = "SELECT id, username, email, phone, role, created_at, updated_at FROM users"
        cur.execute(query)
        
        # 获取列名
        columns = [desc[0] for desc in cur.description]
        
        # 获取查询结果
        rows = cur.fetchall()
        
        # 格式化结果
        users_data = []
        for row in rows:
            user_dict = dict(zip(columns, row))
            # 转换时间戳为字符串格式，方便查看
            if 'created_at' in user_dict and user_dict['created_at']:
                user_dict['created_at'] = user_dict['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'updated_at' in user_dict and user_dict['updated_at']:
                user_dict['updated_at'] = user_dict['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            users_data.append(user_dict)
        
        # 打印用户数量
        print(f"users表中共有 {len(users_data)} 条记录")
        
        # 打印详细用户信息（格式化JSON输出）
        if users_data:
            print("\n用户详细信息：")
            print(json.dumps(users_data, ensure_ascii=False, indent=4))
        else:
            print("users表中没有数据")
        
        # 关闭游标和连接
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"数据库连接失败: {e}")
    except Exception as e:
        print(f"查询过程中发生错误: {e}")

if __name__ == "__main__":
    print("开始查询users表数据...")
    view_users_table()
    print("查询完成")