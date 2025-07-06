"""
微博热搜API模块
提供微博热搜数据获取和解析功能

特性：
- 支持session管理
- 自动管理cookie和认证状态
- 完整的浏览器请求头模拟
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class WeiboHotspotAPI:
    """微博热搜API封装类"""
    
    def __init__(self):
        self.base_url = "https://weibo.com/ajax/side/hotSearch"
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
            'Referer': 'https://weibo.com/',
            'Origin': 'https://weibo.com',
        }
        self.timeout = 10
        self.proxies = {"http": None, "https": None}
        
        # 创建session来管理cookie和认证状态
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)
        
    def fetch_hotspots(self, limit: int = 20) -> List[Dict]:
        """
        获取微博热搜数据
        
        Args:
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 热搜数据列表
            
        Raises:
            requests.RequestException: 网络请求异常
            ValueError: 数据解析异常
        """
        try:
            # 使用session发送请求
            response = self.session.get(
                self.base_url,
                timeout=self.timeout
            )
            response.raise_for_status()
            

            # 处理响应
            try:
                data = response.json()
            except Exception as json_error:
                print(f"❌ 微博 JSON解析失败: {json_error}")
                print(f"响应内容预览: {response.text[:200]}")
                raise ValueError(f"微博JSON解析失败: {json_error}")
            
            return self._parse_hotspots(data, limit)
            
        except requests.RequestException as e:
            raise requests.RequestException(f"微博API请求失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"微博数据解析失败: {str(e)}")
    
    def _parse_hotspots(self, data: Dict, limit: int) -> List[Dict]:
        """
        解析微博热搜数据
        
        Args:
            data: 原始API响应数据
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 解析后的热搜数据列表
        """
        hotspots = []
        
        # 检查数据结构
        if data.get('ok') != 1:
            return hotspots
            
        weibo_data = data.get('data', {})
        realtime_list = weibo_data.get('realtime', [])
        
        for index, item in enumerate(realtime_list[:limit], 1):
            try:
                # 提取基本信息
                word = item.get('word', '').strip()
                if not word:
                    continue
                    
                # 提取热度信息
                num = item.get('num', 0)
                heat_text = self._format_heat_value(num)
                
                # 提取其他信息
                note = item.get('note', '')
                realpos = item.get('realpos', index)
                rank = item.get('rank', index - 1)
                flag = item.get('flag', 0)
                label_name = item.get('label_name', '')
                icon_desc = item.get('icon_desc', '')
                icon_desc_color = item.get('icon_desc_color', '')
                topic_flag = item.get('topic_flag', 0)
                word_scheme = item.get('word_scheme', '')
                
                # 处理话题格式
                display_title = word_scheme if word_scheme else word
                if topic_flag == 1 and not display_title.startswith('#'):
                    display_title = f"#{word}#"
                
                hotspot = {
                    'rank': index,
                    'title': display_title,
                    'word': word,
                    'url': f'https://s.weibo.com/weibo?q={item["word"]}',
                    'heat': heat_text,
                    'heat_value': num,
                    'note': note,
                    'realpos': realpos,
                    'original_rank': rank,
                    'flag': flag,
                    'label_name': label_name,
                    'icon_desc': icon_desc,
                    'icon_desc_color': icon_desc_color,
                    'topic_flag': topic_flag,
                    'word_scheme': word_scheme,
                    'platform': '微博'
                }
                
                hotspots.append(hotspot)
                
            except (KeyError, TypeError) as e:
                # 跳过解析失败的单条数据
                continue
                
        return hotspots
    
    def _format_heat_value(self, num: int) -> str:
        """
        格式化热度数值为可读文本
        
        Args:
            num: 热度数值
            
        Returns:
            str: 格式化后的热度文本
        """
        if num == 0:
            return "热搜"
            
        if num >= 100000000:  # 1亿
            return f"{num / 100000000:.1f}亿热度"
        elif num >= 10000:  # 1万
            return f"{num / 10000:.1f}万热度"
        elif num >= 1000:  # 1千
            return f"{num / 1000:.1f}千热度"
        else:
            return f"{num}热度"
    
    def get_platform_name(self) -> str:
        """获取平台名称"""
        return "微博"
    
    def get_platform_icon(self) -> str:
        """获取平台图标"""
        return "🔥"
    
    def close_session(self):
        """关闭session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __del__(self):
        """析构函数，确保session被正确关闭"""
        self.close_session()


# 便捷函数
def get_weibo_hotspots(limit: int = 20) -> List[Dict]:
    """
    获取微博热搜数据的便捷函数
    
    Args:
        limit: 获取数量限制
        
    Returns:
        List[Dict]: 热搜数据列表
    """
    api = WeiboHotspotAPI()
    try:
        return api.fetch_hotspots(limit)
    finally:
        api.close_session()


if __name__ == "__main__":
    # 测试代码
    try:
        api = WeiboHotspotAPI()
        
        hotspots = api.fetch_hotspots(10)
        print(f"\n获取到 {len(hotspots)} 条微博热搜:")
        for hotspot in hotspots[:5]:  # 显示前5条
            print(f"{hotspot['rank']}. {hotspot['title']} - {hotspot['heat']}")
            if hotspot.get('icon_desc'):
                print(f"    标签: {hotspot['icon_desc']}")
        
        # 清理资源
        api.close_session()
        
    except Exception as e:
        print(f"测试失败: {e}") 