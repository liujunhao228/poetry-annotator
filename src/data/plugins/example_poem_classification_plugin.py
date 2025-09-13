"""
示例诗词分类插件
展示如何实现自定义诗词分类逻辑
"""

import re
from typing import Dict, Any, List
from src.config.schema import PluginConfig
from src.plugin_system.interfaces import PreprocessingPlugin # Import the generic PreprocessingPlugin


class ExamplePoemClassificationPlugin(PreprocessingPlugin):
    """示例诗词分类插件"""
    
    def __init__(self, plugin_config: PluginConfig):
        self.plugin_config = plugin_config
        self.settings = plugin_config.settings
        
    def get_name(self) -> str:
        """获取插件名称"""
        return "ExamplePoemClassificationPlugin"
    
    def get_description(self) -> str:
        """获取插件描述"""
        return "示例诗词分类插件"
    
    def classify_poem(self, poem_data: Dict[str, Any]) -> List[str]:
        """
        对单首诗词进行分类
        
        Args:
            poem_data: 诗词数据
            
        Returns:
            分类标签列表
        """
        categories = []
        title = poem_data.get("title", "").lower()
        content = poem_data.get("full_text", "").lower()
        text = title + " " + content
        
        # 咏史怀古类 - 通过关键词识别
        historical_keywords = ["怀古", "咏史", "金陵", "长安", "洛阳", "开元", "贞观"]
        if any(keyword in text for keyword in historical_keywords):
            categories.append("咏史怀古")
            
        # 山水田园类
        landscape_keywords = ["山水", "田园", "隐居", "山居", "水边", "林间"]
        if any(keyword in text for keyword in landscape_keywords):
            categories.append("山水田园")
            
        # 边塞征战类
        frontier_keywords = ["边塞", "征战", "战场", "边关", "烽火"]
        if any(keyword in text for keyword in frontier_keywords):
            categories.append("边塞征战")
            
        # 羁旅思乡类
        travel_keywords = ["羁旅", "思乡", "思归", "怀乡", "异乡", "漂泊"]
        if any(keyword in text for keyword in travel_keywords):
            categories.append("羁旅思乡")
            
        # 送别离情类
        farewell_keywords = ["送别", "离别", "分别", "告别", "离散", "相思"]
        if any(keyword in text for keyword in farewell_keywords):
            categories.append("送别离情")
            
        # 咏物言志类
        object_keywords = ["咏物", "言志", "托物", "借物", "梅花", "竹子", "菊花", "松树"]
        if any(keyword in text for keyword in object_keywords):
            categories.append("咏物言志")
            
        # 爱情闺怨类
        love_keywords = ["爱情", "闺怨", "相思", "离愁", "思君", "怨情"]
        if any(keyword in text for keyword in love_keywords):
            categories.append("爱情闺怨")
            
        # 节令民俗类
        festival_keywords = ["春节", "元宵", "清明", "端午", "中秋", "重阳", "除夕", "民俗"]
        if any(keyword in text for keyword in festival_keywords):
            categories.append("节令民俗")
            
        # 哲理人生类
        philosophy_keywords = ["哲理", "人生", "感悟", "启示", "感慨"]
        if any(keyword in text for keyword in philosophy_keywords):
            categories.append("哲理人生")
            
        # 忧国忧民类
        concern_keywords = ["忧国", "忧民", "爱国", "民生", "社会", "现实"]
        if any(keyword in text for keyword in concern_keywords):
            categories.append("忧国忧民")
            
        return categories
    
    def get_supported_categories(self) -> List[str]:
        """
        获取插件支持的分类列表
        
        Returns:
            支持的分类标签列表
        """
        return [
            "咏史怀古",
            "山水田园",
            "边塞征战",
            "羁旅思乡",
            "送别离情",
            "咏物言志",
            "爱情闺怨",
            "节令民俗",
            "哲理人生",
            "忧国忧民"
        ]
    
    def preprocess(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预处理操作（实现预处理插件接口）
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            处理后的数据
        """
        action = kwargs.get("action")
        
        if action == "classify_poem":
            poem_data = kwargs.get("poem_data")
            if poem_data:
                return self.classify_poem(poem_data)
            else:
                raise ValueError("Missing 'poem_data' for 'classify_poem' action.")
        elif action == "get_supported_categories":
            return self.get_supported_categories()
        else:
            # Default behavior or raise an error for unsupported actions
            return data
