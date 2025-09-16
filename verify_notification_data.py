import sys
import psycopg2

# 数据库连接配置
DB_CONFIG = {
    "host": "10.208.112.57",
    "database": "quant_db",
    "user": "quant_user",
    "password": "quant_pass"
}

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"连接数据库失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

def count_notifications(conn):
    """统计数据库中的通知总数"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM notifications")
        count = cur.fetchone()[0]
        cur.close()
        return count
    except Exception as e:
        print(f"统计通知时发生错误: {e}")
        return -1

def get_recent_notifications(conn, limit=10):
    """获取最近的几条通知数据"""
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, type, content, is_read, created_at
            FROM notifications
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        notifications = cur.fetchall()
        cur.close()
        return notifications
    except Exception as e:
        print(f"获取通知时发生错误: {e}")
        return []

def get_notification_stats(conn):
    """获取通知类型统计数据"""
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type, COUNT(*) as count
            FROM notifications
            GROUP BY type
            ORDER BY count DESC
            """
        )
        stats = cur.fetchall()
        cur.close()
        return stats
    except Exception as e:
        print(f"获取通知统计时发生错误: {e}")
        return []

def main():
    """主函数"""
    # 获取数据库连接
    conn = get_db_connection()
    print("成功连接到数据库")
    
    # 检查通知表是否存在
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'notifications'
            """
        )
        table_exists = cur.fetchone() is not None
        cur.close()
        
        if not table_exists:
            print("错误: notifications表不存在")
            conn.close()
            sys.exit(1)
        
        print("notifications表存在")
        
        # 统计通知总数
        total_count = count_notifications(conn)
        print(f"数据库中共有 {total_count} 条通知记录")
        
        # 获取通知类型统计
        stats = get_notification_stats(conn)
        print("\n通知类型统计:")
        for type_name, count in stats:
            print(f"  {type_name}: {count}条")
        
        # 获取最近的10条通知
        recent_notifications = get_recent_notifications(conn, 10)
        print("\n最近的10条通知:")
        for notification in recent_notifications:
            id, user_id, type_name, content, is_read, created_at = notification
            read_status = "已读" if is_read else "未读"
            print(f"  ID: {id}, 用户ID: {user_id}, 类型: {type_name}, 状态: {read_status}")
            print(f"  内容: {content}")
            print(f"  创建时间: {created_at}")
            print("  " + "-" * 50)
        
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
    finally:
        # 关闭连接
        conn.close()
        print("\n数据库连接已关闭")


if __name__ == "__main__":
    print("开始验证通知数据...")
    main()
    print("验证完成！")