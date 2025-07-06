"""
抖音热搜API模块
提供抖音热搜数据获取和解析功能
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class DouyinHotspotAPI:
    """抖音热搜API封装类"""
    
    def __init__(self):
        self.base_url = "https://aweme.snssdk.com/aweme/v1/hot/search/list/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.douyin.com/',
        }
        self.timeout = 10
        self.proxies = {"http": None, "https": None}
        
    def fetch_hotspots(self, limit: int = 20) -> List[Dict]:
        """
        获取抖音热搜数据
        
        Args:
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 热搜数据列表
            
        Raises:
            requests.RequestException: 网络请求异常
            ValueError: 数据解析异常
        """
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=self.timeout,
                proxies=self.proxies
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_hotspots(data, limit)
            
        except requests.RequestException as e:
            raise requests.RequestException(f"抖音API请求失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"抖音数据解析失败: {str(e)}")
    
    def _parse_hotspots(self, data: Dict, limit: int) -> List[Dict]:
        """
        解析抖音热搜数据
        
        Args:
            data: 原始API响应数据
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 解析后的热搜数据列表
        """
        hotspots = []
        
        # 检查数据结构
        if 'data' not in data or 'trending_list' not in data['data']:
            return hotspots
            
        trending_list = data['data']['trending_list']
        
        for index, item in enumerate(trending_list[:limit], 1):
            try:
                # 提取基本信息
                title = item.get('word', '').strip()
                if not title:
                    continue
                    
                # 提取热度信息
                hot_value = item.get('hot_value', 0)
                heat_text = self._format_heat_value(hot_value)
                
                # 提取其他信息
                video_count = item.get('video_count', 0)
                word_type = item.get('word_type', 0)
                
                # 提取封面图片
                word_cover = item.get('word_cover', {})
                cover_url = ''
                if word_cover and 'url_list' in word_cover:
                    url_list = word_cover['url_list']
                    if url_list:
                        cover_url = url_list[0]
                
                # 构建搜索URL
                search_url = f"https://www.douyin.com/search/{requests.utils.quote(title)}"
                
                hotspot = {
                    'rank': index,
                    'title': title,
                    'heat': heat_text,
                    'heat_value': hot_value,
                    'video_count': video_count,
                    'cover_url': cover_url,
                    'word_type': word_type,
                    'url': search_url,
                    'platform': '抖音'
                }
                
                hotspots.append(hotspot)
                
            except (KeyError, TypeError) as e:
                # 跳过解析失败的单条数据
                continue
                
        return hotspots
    
    def _format_heat_value(self, hot_value: int) -> str:
        """
        格式化热度数值为可读文本
        
        Args:
            hot_value: 热度数值
            
        Returns:
            str: 格式化后的热度文本
        """
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
        return "抖音"
    
    def get_platform_icon(self) -> str:
        """获取平台图标"""
        return "🎵"


# 便捷函数
def get_douyin_hotspots(limit: int = 20) -> List[Dict]:
    """
    获取抖音热搜数据的便捷函数
    
    Args:
        limit: 获取数量限制
        
    Returns:
        List[Dict]: 热搜数据列表
    """
    api = DouyinHotspotAPI()
    return api.fetch_hotspots(limit)


if __name__ == "__main__":
    # 测试代码
    try:
        hotspots = get_douyin_hotspots(10)
        print(f"获取到 {len(hotspots)} 条抖音热搜:")
        for hotspot in hotspots[:5]:  # 显示前5条
            print(f"{hotspot['rank']}. {hotspot['title']} - {hotspot['heat']}")
    except Exception as e:
        print(f"测试失败: {e}") 