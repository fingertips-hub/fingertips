"""
Bilibili热搜API模块
提供Bilibili热搜数据获取和解析功能
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class BilibiliHotspotAPI:
    """Bilibili热搜API封装类"""
    
    def __init__(self):
        self.base_url = "https://s.search.bilibili.com/main/hotword"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.bilibili.com/',
        }
        self.timeout = 10
        self.proxies = {"http": None, "https": None}
        
    def fetch_hotspots(self, limit: int = 20) -> List[Dict]:
        """
        获取Bilibili热搜数据
        
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
            raise requests.RequestException(f"Bilibili API请求失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Bilibili数据解析失败: {str(e)}")
    
    def _parse_hotspots(self, data: Dict, limit: int) -> List[Dict]:
        """
        解析Bilibili热搜数据
        
        Args:
            data: 原始API响应数据
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 解析后的热搜数据列表
        """
        hotspots = []
        
        # 检查数据结构
        if 'list' not in data:
            return hotspots
            
        hotword_list = data['list']
        
        for index, item in enumerate(hotword_list[:limit], 1):
            try:
                # 提取基本信息
                title = item.get('show_name', '').strip()
                keyword = item.get('keyword', '').strip()
                
                # 优先使用show_name，fallback到keyword
                if not title:
                    title = keyword
                if not title:
                    continue
                
                # 提取热度信息
                heat_score = item.get('heat_score', 0)
                heat_text = self._format_heat_value(heat_score)
                
                # 提取其他信息
                word_type = item.get('word_type', 0)
                pos = item.get('pos', index)
                icon = item.get('icon', '')
                
                # 提取热度层级
                heat_layer = item.get('heat_layer', '')
                
                # 提取统计数据
                stat_datas = item.get('stat_datas', {})
                is_commercial = stat_datas.get('is_commercial', '0') == '1'
                
                # 构建搜索URL，使用keyword或title
                search_keyword = keyword if keyword else title
                search_url = f"https://search.bilibili.com/all?keyword={requests.utils.quote(search_keyword)}"
                
                hotspot = {
                    'rank': index,
                    'title': title,
                    'keyword': keyword,
                    'heat': heat_text,
                    'heat_value': heat_score,
                    'word_type': word_type,
                    'pos': pos,
                    'icon': icon,
                    'heat_layer': heat_layer,
                    'is_commercial': is_commercial,
                    'url': search_url,
                    'platform': 'Bilibili'
                }
                
                hotspots.append(hotspot)
                
            except (KeyError, TypeError) as e:
                # 跳过解析失败的单条数据
                continue
                
        return hotspots
    
    def _format_heat_value(self, heat_score: int) -> str:
        """
        格式化热度数值为可读文本
        
        Args:
            heat_score: 热度分数
            
        Returns:
            str: 格式化后的热度文本
        """
        if heat_score == 0:
            return "热搜"
            
        if heat_score >= 100000000:  # 1亿
            return f"{heat_score / 100000000:.1f}亿热度"
        elif heat_score >= 10000:  # 1万
            return f"{heat_score / 10000:.1f}万热度"
        elif heat_score >= 1000:  # 1千
            return f"{heat_score / 1000:.1f}千热度"
        else:
            return f"{heat_score}热度"
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "Bilibili"
    
    def get_platform_icon(self) -> str:
        """获取平台图标"""
        return "📺"


# 便捷函数
def get_bilibili_hotspots(limit: int = 20) -> List[Dict]:
    """
    获取Bilibili热搜数据的便捷函数
    
    Args:
        limit: 获取数量限制
        
    Returns:
        List[Dict]: 热搜数据列表
    """
    api = BilibiliHotspotAPI()
    return api.fetch_hotspots(limit)


if __name__ == "__main__":
    # 测试代码
    try:
        hotspots = get_bilibili_hotspots(10)
        print(f"获取到 {len(hotspots)} 条Bilibili热搜:")
        for hotspot in hotspots[:5]:  # 显示前5条
            print(f"{hotspot['rank']}. {hotspot['title']} - {hotspot['heat']}")
    except Exception as e:
        print(f"测试失败: {e}") 