"""
策略数据处理测试
"""
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.strategy_processor import StrategyAnnotationProcessor
from src.data.models import SentenceAnnotation
from src.data.models_sentence_strategy_link import SentenceStrategyLink


def test_strategy_processor():
    """测试策略数据处理器"""
    print("=== 测试策略数据处理器 ===")
    
    # 测试数据
    sentences = [
        {"id": 4, "sentence": "丞相祠堂何处寻？"}
    ]
    
    strategy_data = {
        "id": 4,
        "relationship_action": "RA03",
        "emotional_strategy": "ES02",
        "context_analysis": {
            "communication_scene": ["SC03"],
            "risk_level": "RS01"
        },
        "brief_rationale": "以提问开启公共话题，将个人凭吊升华为集体文化记忆寻根。"
    }
    
    # 创建标注记录
    annotation = StrategyAnnotationProcessor.create_annotation_record(poem_id=1, model_identifier="strategy_model_v1")
    print(f"创建标注记录: {annotation}")
    
    # 创建句子标注记录（需要设置ID以供测试）
    sentence_annotations = StrategyAnnotationProcessor.create_sentence_annotations(
        annotation_id=1, 
        poem_id=1, 
        sentences=sentences
    )
    # 手动设置ID以供测试
    sentence_annotations[0].id = 1
    print(f"创建句子标注记录: {sentence_annotations[0]}")
    
    # 创建策略链接记录
    strategy_links = StrategyAnnotationProcessor.create_strategy_links(
        sentence_annotation_id=1, 
        strategy_data=strategy_data
    )
    print(f"创建策略链接记录数量: {len(strategy_links)}")
    for link in strategy_links:
        print(f"  - {link}")
    
    # 转换为标注结果
    annotation_result = StrategyAnnotationProcessor.convert_to_annotation_result(
        sentence_annotations, 
        strategy_links
    )
    print(f"标注结果:\n{annotation_result}")
    
    # 验证结果
    expected_result = {
        "id": 4,
        "sentence": "丞相祠堂何处寻？",
        "relationship_action": "RA03",
        "emotional_strategy": "ES02",
        "context_analysis": {
            "communication_scene": ["SC03"],
            "risk_level": "RS01"
        }
    }
    
    result_data = json.loads(annotation_result)
    actual_result = result_data[0]
    
    # 逐项验证结果
    tests_passed = True
    
    if actual_result["id"] != expected_result["id"]:
        print(f"❌ ID不匹配: 期望 {expected_result['id']}, 实际 {actual_result['id']}")
        tests_passed = False
        
    if actual_result["sentence"] != expected_result["sentence"]:
        print(f"❌ 句子不匹配: 期望 {expected_result['sentence']}, 实际 {actual_result['sentence']}")
        tests_passed = False
        
    if "relationship_action" not in actual_result or actual_result["relationship_action"] != expected_result["relationship_action"]:
        print(f"❌ 关系动作不匹配: 期望 {expected_result['relationship_action']}, 实际 {actual_result.get('relationship_action')}")
        tests_passed = False
        
    if "emotional_strategy" not in actual_result or actual_result["emotional_strategy"] != expected_result["emotional_strategy"]:
        print(f"❌ 情感策略不匹配: 期望 {expected_result['emotional_strategy']}, 实际 {actual_result.get('emotional_strategy')}")
        tests_passed = False
        
    if "context_analysis" not in actual_result:
        print(f"❌ 缺少context_analysis")
        tests_passed = False
    else:
        if "communication_scene" not in actual_result["context_analysis"] or actual_result["context_analysis"]["communication_scene"] != expected_result["context_analysis"]["communication_scene"]:
            print(f"❌ 传播场景不匹配: 期望 {expected_result['context_analysis']['communication_scene']}, 实际 {actual_result['context_analysis'].get('communication_scene')}")
            tests_passed = False
            
        if "risk_level" not in actual_result["context_analysis"] or actual_result["context_analysis"]["risk_level"] != expected_result["context_analysis"]["risk_level"]:
            print(f"❌ 风险等级不匹配: 期望 {expected_result['context_analysis']['risk_level']}, 实际 {actual_result['context_analysis'].get('risk_level')}")
            tests_passed = False
    
    if tests_passed:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
        print(f"期望结果: {expected_result}")
        print(f"实际结果: {actual_result}")


if __name__ == "__main__":
    test_strategy_processor()