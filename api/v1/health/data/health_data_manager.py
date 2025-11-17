"""
健康数据管理器

提供健康数据的数据库操作功能，包括查询、添加、统计等
"""

import logging
import datetime
from typing import Dict, List, Optional, Any

# 导入数据库连接器
try:
    from utils.db_connector import db_connector
except ImportError:
    # 如果无法导入，创建模拟连接器用于测试
    class MockDBConnector:
        def execute_query(self, query, params=None):
            return []
        
        def execute_update(self, query, params=None):
            return 1
    
    db_connector = MockDBConnector()

logger = logging.getLogger(__name__)

class HealthDataManager:
    """健康数据管理器"""
    
    def __init__(self):
        self.table_name = "health_data"
        
    def get_health_data(self, user_uuid: str, data_type: str = 'all') -> Dict[str, Any]:
        """
        获取健康数据
        
        Args:
            user_uuid: 用户UUID
            data_type: 数据类型 (all, heart_rate, steps, sleep, weight, blood_pressure, calories)
        
        Returns:
            健康数据字典
        """
        try:
            if data_type == 'all':
                # 获取所有健康数据
                query = f"""
                SELECT data_type, value, timestamp, metadata 
                FROM {self.table_name} 
                WHERE user_uuid = %s 
                ORDER BY timestamp DESC 
                LIMIT 100
                """
                params = (user_uuid,)
            else:
                # 获取特定类型的数据
                query = f"""
                SELECT data_type, value, timestamp, metadata 
                FROM {self.table_name} 
                WHERE user_uuid = %s AND data_type = %s 
                ORDER BY timestamp DESC 
                LIMIT 50
                """
                params = (user_uuid, data_type)
            
            results = db_connector.execute_query(query, params)
            
            # 按数据类型组织数据
            health_data = {}
            for row in results:
                data_type = row[0]
                if data_type not in health_data:
                    health_data[data_type] = []
                
                health_data[data_type].append({
                    'value': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None,
                    'metadata': row[3] or {}
                })
            
            # 为每种数据类型添加统计信息
            for data_type, records in health_data.items():
                if records:
                    values = [float(r['value']) for r in records if r['value'] is not None]
                    if values:
                        health_data[data_type] = {
                            'records': records[:10],  # 只返回最近10条记录
                            'stats': {
                                'count': len(records),
                                'latest': values[0],
                                'average': sum(values) / len(values),
                                'max': max(values),
                                'min': min(values)
                            }
                        }
            
            return health_data
            
        except Exception as e:
            logger.error(f"获取健康数据失败: {e}")
            return {}
    
    def add_health_data(self, user_uuid: str, data_type: str, value: Any, 
                       timestamp: Optional[str] = None, 
                       metadata: Optional[Dict] = None) -> bool:
        """
        添加健康数据
        
        Args:
            user_uuid: 用户UUID
            data_type: 数据类型
            value: 数据值
            timestamp: 时间戳（可选）
            metadata: 元数据（可选）
        
        Returns:
            是否添加成功
        """
        try:
            if not timestamp:
                timestamp = datetime.datetime.now()
            else:
                # 解析时间戳字符串
                timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            query = f"""
            INSERT INTO {self.table_name} 
            (user_uuid, data_type, value, timestamp, metadata, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                user_uuid, 
                data_type, 
                str(value), 
                timestamp, 
                metadata or {}, 
                datetime.datetime.now()
            )
            
            rows_affected = db_connector.execute_update(query, params)
            
            if rows_affected > 0:
                logger.info(f"健康数据添加成功: 用户 {user_uuid}, 类型 {data_type}, 值 {value}")
                return True
            else:
                logger.error(f"健康数据添加失败: 用户 {user_uuid}, 类型 {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"添加健康数据失败: {e}")
            return False
    
    def get_health_stats(self, user_uuid: str, period: str = 'week') -> Dict[str, Any]:
        """
        获取健康数据统计
        
        Args:
            user_uuid: 用户UUID
            period: 统计周期 (day, week, month)
        
        Returns:
            统计数据字典
        """
        try:
            # 计算时间范围
            end_date = datetime.datetime.now()
            if period == 'day':
                start_date = end_date - datetime.timedelta(days=1)
            elif period == 'week':
                start_date = end_date - datetime.timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - datetime.timedelta(days=30)
            else:
                start_date = end_date - datetime.timedelta(weeks=1)  # 默认一周
            
            # 查询统计数据
            query = f"""
            SELECT data_type, 
                   COUNT(*) as count,
                   AVG(CAST(value AS DECIMAL)) as avg_value,
                   MIN(CAST(value AS DECIMAL)) as min_value,
                   MAX(CAST(value AS DECIMAL)) as max_value
            FROM {self.table_name} 
            WHERE user_uuid = %s AND timestamp >= %s
            GROUP BY data_type
            """
            
            params = (user_uuid, start_date)
            results = db_connector.execute_query(query, params)
            
            # 按数据类型统计
            stats = {}
            for row in results:
                data_type = row[0]
                count = row[1]
                avg_value = float(row[2]) if row[2] is not None else None
                min_value = float(row[3]) if row[3] is not None else None
                max_value = float(row[4]) if row[4] is not None else None
                
                stats[data_type] = {
                    'stats': {
                        'count': count,
                        'average': avg_value,
                        'max': max_value,
                        'min': min_value,
                        'latest': None,  # 需要额外查询最新值
                        'trend': 'no_data'  # 需要额外计算趋势
                    }
                }
            
            # 计算统计指标（已通过SQL查询获得基本统计信息）
            # 这里可以添加获取最新值和计算趋势的逻辑
            for data_type, data in stats.items():
                # 获取最新值
                latest_query = f"""
                SELECT value 
                FROM {self.table_name} 
                WHERE user_uuid = %s AND data_type = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
                """
                latest_params = (user_uuid, data_type)
                latest_result = db_connector.execute_query(latest_query, latest_params)
                
                if latest_result:
                    data['stats']['latest'] = float(latest_result[0][0]) if latest_result[0][0] is not None else None
                
                # 计算趋势（简化版本，使用最近5个值）
                trend_query = f"""
                SELECT value 
                FROM {self.table_name} 
                WHERE user_uuid = %s AND data_type = %s 
                ORDER BY timestamp DESC 
                LIMIT 5
                """
                trend_params = (user_uuid, data_type)
                trend_results = db_connector.execute_query(trend_query, trend_params)
                
                if len(trend_results) >= 2:
                    trend_values = [float(row[0]) for row in trend_results if row[0] is not None]
                    if trend_values:
                        data['stats']['trend'] = self._calculate_trend(trend_values)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取健康数据统计失败: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算数据趋势
        
        Args:
            values: 数值列表
        
        Returns:
            趋势描述 (increasing, decreasing, stable, no_data)
        """
        if len(values) < 2:
            return 'no_data'
        
        # 取最近5个值计算趋势
        recent_values = values[-5:]
        
        # 计算斜率
        x = list(range(len(recent_values)))
        y = recent_values
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        except ZeroDivisionError:
            return 'stable'
        
        # 根据斜率判断趋势
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_recent_health_data(self, user_uuid: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的健康数据记录
        
        Args:
            user_uuid: 用户UUID
            limit: 记录数量限制
        
        Returns:
            健康数据记录列表
        """
        try:
            query = f"""
            SELECT data_type, value, timestamp, metadata 
            FROM {self.table_name} 
            WHERE user_uuid = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            
            params = (user_uuid, limit)
            results = db_connector.execute_query(query, params)
            
            records = []
            for row in results:
                records.append({
                    'data_type': row[0],
                    'value': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None,
                    'metadata': row[3] or {}
                })
            
            return records
            
        except Exception as e:
            logger.error(f"获取最近健康数据失败: {e}")
            return []
    
    def delete_health_data(self, user_uuid: str, data_id: Optional[int] = None, 
                          data_type: Optional[str] = None) -> bool:
        """
        删除健康数据
        
        Args:
            user_uuid: 用户UUID
            data_id: 数据ID（可选）
            data_type: 数据类型（可选）
        
        Returns:
            是否删除成功
        """
        try:
            if data_id:
                # 删除特定数据记录
                query = f"""
                DELETE FROM {self.table_name} 
                WHERE user_uuid = %s AND id = %s
                """
                params = (user_uuid, data_id)
            elif data_type:
                # 删除特定类型的所有数据
                query = f"""
                DELETE FROM {self.table_name} 
                WHERE user_uuid = %s AND data_type = %s
                """
                params = (user_uuid, data_type)
            else:
                # 删除用户的所有健康数据
                query = f"""
                DELETE FROM {self.table_name} 
                WHERE user_uuid = %s
                """
                params = (user_uuid,)
            
            rows_affected = db_connector.execute_update(query, params)
            
            if rows_affected > 0:
                logger.info(f"健康数据删除成功: 用户 {user_uuid}")
                return True
            else:
                logger.warning(f"未找到要删除的健康数据: 用户 {user_uuid}")
                return False
                
        except Exception as e:
            logger.error(f"删除健康数据失败: {e}")
            return False

# 创建全局实例
health_data_manager = HealthDataManager()