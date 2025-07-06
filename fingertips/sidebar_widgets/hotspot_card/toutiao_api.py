"""
今日头条热搜API模块
提供今日头条热搜数据获取和解析功能

特性：
- 支持session管理
- 自动管理cookie和认证状态
- 完整的浏览器请求头模拟
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class ToutiaoHotspotAPI:
    """今日头条热搜API封装类"""
    
    def __init__(self):
        self.base_url = "https://www.toutiao.com/hot-event/hot-board/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Sec-CH-UA': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.toutiao.com/',
            'Origin': 'https://www.toutiao.com',
        }
        self.timeout = 10
        self.proxies = {"http": None, "https": None}
        
        # 创建session来管理cookie和认证状态
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)
        
    def fetch_hotspots(self, limit: int = 20) -> List[Dict]:
        """
        获取今日头条热搜数据
        
        Args:
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 热搜数据列表
            
        Raises:
            requests.RequestException: 网络请求异常
            ValueError: 数据解析异常
        """
        try:
            params = {
                'origin': 'toutiao_pc'
            }
            
            # 使用session发送请求
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 处理响应
            try:
                data = response.json()
            except Exception as json_error:
                print(f"❌ 今日头条 JSON解析失败: {json_error}")
                print(f"响应内容预览: {response.text[:200]}")
                raise ValueError(f"今日头条JSON解析失败: {json_error}")
            
            return self._parse_hotspots(data, limit)
            
        except requests.RequestException as e:
            raise requests.RequestException(f"今日头条API请求失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"今日头条数据解析失败: {str(e)}")
    
    def _parse_hotspots(self, data: Dict, limit: int) -> List[Dict]:
        """
        解析今日头条热搜数据
        
        Args:
            data: 原始API响应数据
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 解析后的热搜数据列表
        """
        hotspots = []
        
        # 检查数据结构
        if 'data' not in data:
            return hotspots
            
        hotspot_list = data['data']
        
        for index, item in enumerate(hotspot_list[:limit], 1):
            try:
                # 提取基本信息
                title = item.get('Title', '').strip()
                if not title:
                    continue
                    
                # 提取热度信息
                hot_value = item.get('HotValue', '0')
                heat_text = self._format_heat_value(hot_value)
                
                # 提取其他信息
                url = item.get('Url', '')
                label = item.get('Label', '')
                label_desc = item.get('LabelDesc', '')
                cluster_id = item.get('ClusterIdStr', str(item.get('ClusterId', '')))
                
                # 提取图片信息
                image_info = item.get('Image', {})
                image_url = ''
                if image_info and 'url' in image_info:
                    image_url = image_info['url']
                
                hotspot = {
                    'rank': index,
                    'title': title,
                    'heat': heat_text,
                    'heat_value': self._parse_heat_value(hot_value),
                    'url': url,
                    'label': label,
                    'label_desc': label_desc,
                    'cluster_id': cluster_id,
                    'image_url': image_url,
                    'platform': '今日头条'
                }
                
                hotspots.append(hotspot)
                
            except (KeyError, TypeError) as e:
                # 跳过解析失败的单条数据
                continue
                
        return hotspots
    
    def _parse_heat_value(self, hot_value_str: str) -> int:
        """
        解析热度数值
        
        Args:
            hot_value_str: 热度字符串
            
        Returns:
            int: 热度数值
        """
        if not hot_value_str:
            return 0
            
        try:
            # 直接转换为整数
            return int(hot_value_str)
        except (ValueError, TypeError):
            return 0
    
    def _format_heat_value(self, hot_value_str: str) -> str:
        """
        格式化热度数值为可读文本
        
        Args:
            hot_value_str: 热度字符串
            
        Returns:
            str: 格式化后的热度文本
        """
        hot_value = self._parse_heat_value(hot_value_str)
        
        if hot_value == 0:
            return "热搜"
            
        if hot_value >= 100000000:  # 1亿
            return f"{hot_value / 100000000:.1f}亿热度"
        elif hot_value >= 10000:  # 1万
            return f"{hot_value / 10000:.1f}万热度"
        elif hot_value >= 1000:  # 1千
            return f"{hot_value / 1000:.1f}千热度"
        else:
            return f"{hot_value}热度"
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "今日头条"
    
    def get_platform_icon(self) -> str:
        """获取平台图标"""
        return "📰"
    
    def close_session(self):
        """关闭session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __del__(self):
        """析构函数，确保session被正确关闭"""
        self.close_session()


# 便捷函数
def get_toutiao_hotspots(limit: int = 20) -> List[Dict]:
    """
    获取今日头条热搜数据的便捷函数
    
    Args:
        limit: 获取数量限制
        
    Returns:
        List[Dict]: 热搜数据列表
    """
    api = ToutiaoHotspotAPI()
    try:
        return api.fetch_hotspots(limit)
    finally:
        api.close_session()


if __name__ == "__main__":
    # 测试代码
    try:
        api = ToutiaoHotspotAPI()
        
        hotspots = api.fetch_hotspots(10)
        print(f"\n获取到 {len(hotspots)} 条今日头条热搜:")
        for hotspot in hotspots[:5]:  # 显示前5条
            print(f"{hotspot['rank']}. {hotspot['title']} - {hotspot['heat']}")
        
        # 清理资源
        api.close_session()
        
    except Exception as e:
        print(f"测试失败: {e}") 