#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Apriori 情感关联规则挖掘交互式终端

本脚本提供一个基于终端/Jupyter Notebook的交互式界面，用于控制 Apriori 算法的参数，
并在云端主机上执行情感关联规则挖掘。

功能:
- 交互式选择要分析的数据库 (如 唐诗, 宋词).
- [新增] 支持单库挖掘或双库对比挖掘模式。
- 交互式设置 Apriori 算法的核心参数:
  - 分析粒度 (level: 'sentence' 或 'poem')
  - 最小支持度 (min_support)
  - 最小项集长度 (min_length)
  - 最大处理事务数 (max_transactions) 以控制计算资源消耗.
- 在终端中清晰地展示挖掘结果表格。
- 循环执行，方便用户尝试不同的参数组合。

使用方法 (在 Jupyter Notebook 中):
1. 确保已安装项目依赖 (`pip install -r requirements.txt`).
2. 在 Notebook 的一个单元格中运行:
   %run apriori_interactive_miner.py

然后根据提示输入参数即可。
"""
import os
from datetime import datetime
import pandas as pd
from data_visualizer.db_manager import DBManager
from data_visualizer.data_processor import DataProcessor
from data_visualizer.config import DB_PATHS
from data_visualizer.utils import logger

def get_user_input(prompt, type_converter=str, validator=None, default=None):
    """一个通用的用户输入获取和验证函数。"""
    while True:
        try:
            # 在提示中加入默认值
            prompt_with_default = prompt
            if default is not None:
                prompt_with_default = f"{prompt.strip(' :')} (默认: {default}): "
            
            user_str = input(prompt_with_default)
            
            if default is not None and user_str == "":
                return default
            
            value = type_converter(user_str)
            if validator is None or validator(value):
                return value
            else:
                logger.error("输入无效，请重试。")
        except ValueError:
            logger.error(f"输入格式错误，请输入一个有效的 {type_converter.__name__} 类型。")
        except Exception as e:
            logger.error(f"发生错误: {e}")

def get_common_parameters():
    """获取通用的 Apriori 参数。"""
    level = get_user_input(
        "请输入分析粒度 ('sentence' 或 'poem')",
        validator=lambda l: l in ['sentence', 'poem'],
        default='poem'
    )

    min_support = get_user_input(
        "请输入最小支持度 (例如 0.01)",
        type_converter=float,
        validator=lambda s: 0 < s <= 1.0,
        default=0.01
    )

    min_length = get_user_input(
        "请输入项集的最小长度 (例如 2)",
        type_converter=int,
        validator=lambda l: l >= 1,
        default=2
    )

    max_transactions = get_user_input(
        "请输入最大处理事务数以控制性能 (直接回车表示不限制)",
        type_converter=int,
        validator=lambda m: m > 0,
        default=None
    )
    return level, min_support, min_length, max_transactions

def execute_mining(db_key, level, min_support, min_length, max_transactions):
    """封装执行挖掘的核心逻辑"""
    try:
        db_manager = DBManager(db_path=DB_PATHS[db_key])
        processor = DataProcessor(db_manager)

        logger.info(f"[{db_key}] 正在从数据库提取事务数据并执行 Apriori 算法...")
        results_df = processor.mine_frequent_emotion_itemsets_apriori(
            level=level,
            min_support=min_support,
            min_length=min_length,
            max_transactions=max_transactions
        )
        return results_df
    except ImportError:
         logger.error("错误: mlxtend 库未安装，无法执行 Apriori 挖掘。")
         logger.error("请在您的环境中运行: pip install mlxtend")
         raise # 抛出异常以终止程序
    except Exception as e:
        logger.error(f"[{db_key}] 挖掘过程中发生严重错误: {e}", exc_info=True)
        return pd.DataFrame()

def save_results_to_csv(results_df, params, mode):
    """
    将挖掘结果 DataFrame 保存到 CSV 文件。

    Args:
        results_df (pd.DataFrame): 待保存的挖掘结果。
        params (dict): 包含本次挖掘所有参数的字典。
        mode (str): 挖掘模式，'single' 或 'comparison'。
    """
    try:
        # 1. 定义并创建输出目录
        output_dir = "results"
        os.makedirs(output_dir, exist_ok=True)

        # 2. 根据模式和参数生成一个信息丰富的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        level = params.get('level', 'unknown')
        min_support_str = str(params.get('min_support', '0')).replace('.', '_')
        min_length = params.get('min_length', '0')

        if mode == 'single':
            db_name = params.get('db_key', 'unknown_db')
            filename = f"result_{db_name}_{level}_sup{min_support_str}_len{min_length}_{timestamp}.csv"
        elif mode == 'comparison':
            db1 = params.get('db_key1', 'db1')
            db2 = params.get('db_key2', 'db2')
            filename = f"compare_{db1}_vs_{db2}_{level}_sup{min_support_str}_len{min_length}_{timestamp}.csv"
        else:
            filename = f"generic_result_{timestamp}.csv"

        # 3. 构建完整的文件路径
        filepath = os.path.join(output_dir, filename)

        # 4. 保存文件
        # 使用 utf-8-sig 编码确保在 Windows Excel 中能正确打开包含中文的CSV文件
        results_df.to_csv(filepath, index=False, encoding='utf-8-sig')

        logger.info(f"结果已成功保存到: {filepath}")

    except Exception as e:
        logger.error(f"保存结果时发生错误: {e}", exc_info=True)

def run_single_db_session():
    """为单个数据库执行挖掘会话。"""
    # 1. 选择数据库
    print("\n--- 步骤 1: 选择数据库 ---")
    db_keys = list(DB_PATHS.keys())
    prompt_db = f"请从以下数据库中选择一个进行分析 {db_keys}: "
    db_key = get_user_input(
        prompt_db,
        validator=lambda k: k in db_keys
    )
    logger.info(f"已选择数据库: '{db_key}'")

    # 2. 设置参数
    print("\n--- 步骤 2: 设置挖掘参数 ---")
    level, min_support, min_length, max_transactions = get_common_parameters()

    # 3. 执行挖掘
    print("\n--- 步骤 3: 开始执行挖掘 ---")
    logger.info(f"参数设置: db='{db_key}', level={level}, min_support={min_support}, min_length={min_length}, max_transactions={max_transactions or '无限制'}")
    
    results_df = execute_mining(db_key, level, min_support, min_length, max_transactions)

    # 4. 展示结果
    print("\n--- 步骤 4: 显示挖掘结果 ---")
    if results_df.empty:
        logger.warning("在当前参数设置下，未发现任何高频情感组合。")
        # ...
    else:
        logger.info(f"成功发现 {len(results_df)} 条高频项集。")
        print(results_df.to_string(index=False))
        # --- 新增保存逻辑 ---
        should_save = get_user_input(
            "是否要保存本次挖掘结果? (y/n)",
            default='n'
        ).lower()
        if should_save == 'y':
            # 收集参数用于生成文件名
            params = {
                'db_key': db_key,
                'level': level,
                'min_support': min_support,
                'min_length': min_length,
                'max_transactions': max_transactions
            }
            save_results_to_csv(results_df, params, mode='single')

def run_comparison_session():
    """为两个数据库执行对比挖掘会话。"""
    db_keys = list(DB_PATHS.keys())
    if len(db_keys) < 2:
        logger.error("对比模式至少需要2个数据库在 config.py 中定义。")
        return
        
    # 1. 选择数据库
    print("\n--- 步骤 1: 选择要对比的数据库 ---")
    prompt_db1 = f"请选择第一个数据库 {db_keys}: "
    db_key1 = get_user_input(prompt_db1, validator=lambda k: k in db_keys)
    
    prompt_db2 = f"请选择第二个数据库 (不能与'{db_key1}'相同) {db_keys}: "
    db_key2 = get_user_input(prompt_db2, validator=lambda k: k in db_keys and k != db_key1)
    
    logger.info(f"已选定对比数据库: '{db_key1}' vs '{db_key2}'")

    # 2. 设置统一参数
    print("\n--- 步骤 2: 设置统一的挖掘参数 ---")
    level, min_support, min_length, max_transactions = get_common_parameters()

    # 3. 执行挖掘
    print("\n--- 步骤 3: 开始对两个数据库执行挖掘 ---")
    logger.info(f"参数设置: level={level}, min_support={min_support}, min_length={min_length}, max_transactions={max_transactions or '无限制'}")
    
    logger.info(f"正在为 '{db_key1}' 进行挖掘...")
    results_df1 = execute_mining(db_key1, level, min_support, min_length, max_transactions)
    logger.info(f"'{db_key1}' 挖掘完成。")
    
    logger.info(f"正在为 '{db_key2}' 进行挖掘...")
    results_df2 = execute_mining(db_key2, level, min_support, min_length, max_transactions)
    logger.info(f"'{db_key2}' 挖掘完成。")

    # 4. 合并并展示结果
    print("\n--- 步骤 4: 显示对比结果 ---")
    if results_df1.empty and results_df2.empty:
        logger.warning("在当前参数设置下，两个数据库均未发现任何高频情感组合。")
        return

    df1_comp = results_df1[['itemsets_readable', 'support']].rename(columns={'support': f'support_{db_key1}'})
    df2_comp = results_df2[['itemsets_readable', 'support']].rename(columns={'support': f'support_{db_key2}'})

    # 使用外连接合并，并填充0
    merged_df = pd.merge(df1_comp, df2_comp, on='itemsets_readable', how='outer').fillna(0)
    
    # 计算支持度差异
    merged_df['support_diff'] = merged_df[f'support_{db_key2}'] - merged_df[f'support_{db_key1}']
    
    # 按差异的绝对值降序排序，以突出最大差异
    merged_df = merged_df.reindex(merged_df['support_diff'].abs().sort_values(ascending=False).index)
    
    # 格式化输出
    merged_df[f'support_{db_key1}'] = merged_df[f'support_{db_key1}'].map('{:.4f}'.format)
    merged_df[f'support_{db_key2}'] = merged_df[f'support_{db_key2}'].map('{:.4f}'.format)
    merged_df['support_diff'] = merged_df['support_diff'].map('{:+.4f}'.format)
    
    final_cols = ['itemsets_readable', f'support_{db_key1}', f'support_{db_key2}', 'support_diff']
    merged_df = merged_df[final_cols]

    logger.info(f"成功生成对比结果，共 {len(merged_df)} 条组合。")
    print(merged_df.to_string(index=False))
    if not merged_df.empty:
        should_save = get_user_input(
            "是否要保存本次对比结果? (y/n)",
            default='n'
        ).lower()
        if should_save == 'y':
            # 收集参数用于生成文件名
            params = {
                'db_key1': db_key1,
                'db_key2': db_key2,
                'level': level,
                'min_support': min_support,
                'min_length': min_length,
                'max_transactions': max_transactions
            }
            save_results_to_csv(merged_df, params, mode='comparison')

def run_interactive_session():
    """主函数，运行交互式会话。"""
    logger.info("欢迎使用 Apriori 交互式挖掘工具。")
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 120)

    while True:
        try:
            print("\n" + "="*50)
            print("请选择分析模式:")
            print("1. 单库挖掘 (Single Database Mining)")
            print("2. 双库对比挖掘 (Comparative Mining)")
            mode = get_user_input(
                "请输入模式编号 (1 或 2)",
                type_converter=int,
                validator=lambda m: m in [1, 2],
                default=1
            )
            
            if mode == 1:
                run_single_db_session()
            elif mode == 2:
                run_comparison_session()

        except ImportError:
            # 如果 mlxtend 未安装， execute_mining 会抛出此异常
            logger.error("依赖库缺失，程序无法继续。")
            break # 退出主循环
        except Exception as e:
            logger.error(f"会话中出现未知错误: {e}", exc_info=True)

        # 5. 循环或退出
        print("\n" + "="*50)
        another_run = get_user_input(
            "是否要进行另一次分析? (y/n)",
            default='y'
        ).lower()

        if another_run != 'y':
            logger.info("感谢使用，再见！")
            break

if __name__ == '__main__':
    # 当脚本被直接运行时，启动交互式会话
    run_interactive_session()
