import random
import json

# 模拟不同类型的有效和无效响应
FAKE_RESPONSES = {
    "valid": [
        "<annotation><emotion type='喜悦' value='3'/><emotion type='期待' value='2'/></annotation>",
        "<annotation><emotion type='悲伤' value='4'/></annotation>",
        "<annotation><emotion type='宁静' value='5'/></annotation>"
    ],
    "invalid_xml": [
        "<annotation><emotion type='喜悦' value='3'>", # 标签未闭合
        "<annotation><emotion type='未知情感' value='3'/></annotation>", # 无效的情感类型
        "这不是一个XML格式"
    ],
    "empty": [
        ""
    ]
}

def get_fake_llm_response(prompt: str, model_name: str) -> str:
    """
    根据输入生成一个模拟的LLM响应。
    可以根据 prompt 或 model_name 设计更复杂的逻辑。
    当前实现为随机返回一种响应。
    """
    # 设定一个随机种子，使得每次 dry-run 的结果在一定程度上可复现
    # 可以基于 prompt 的哈希值来设定种子
    seed = hash(prompt)
    random.seed(seed)

    # 模拟不同情况的概率
    rand_val = random.random()
    if rand_val < 0.8:  # 80% 概率返回有效响应
        response_type = "valid"
    elif rand_val < 0.95:  # 15% 概率返回无效XML
        response_type = "invalid_xml"
    else:  # 5% 概率返回空响应
        response_type = "empty"
        
    return random.choice(FAKE_RESPONSES[response_type])
