#!/usr/bin/env python3
"""
诗词情感标注统计脚本
用于统计指定数据库的标注情况
"""

import sys
import os
from pathlib import Path
import argparse
import pandas as pd

# 添加项目根目录到Python路径，确保能正确导入src下的模块
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入数据管理器和配置管理器
try:
    from src.data import get_data_manager
    from src.config import config_manager
except ImportError:
    print("错误: 无法导入数据管理器或配置管理器，请检查项目结构")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="诗词情感标注统计脚本")
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="指定项目输出目录，用于派生项目名称和数据库路径"
    )
    parser.add_argument(
        "--source_dir",
        type=str,
        required=True,
        help="指定数据源目录"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径 (CSV格式)，如果不指定则只在控制台输出"
    )
    
    args = parser.parse_args()
    
    try:
        # 获取数据管理器实例
        data_manager = get_data_manager(output_dir=args.output_dir, source_dir=args.source_dir)
        print(f"正在使用项目输出目录: {args.output_dir}, 数据源目录: {args.source_dir}")
        
        # 获取统计数据
        print("正在获取标注统计信息...")
        annotation_stats = data_manager.get_annotation_statistics()
        
        # 格式化统计数据
        data = []
        
        # 添加总体统计
        overall_stats = annotation_stats['overall']
        data.append({
            'statistic_type': 'total_poems',
            'model_identifier': 'ALL',
            'value': overall_stats['total_poems'],
            'description': '总诗词数'
        })
        data.append({
            'statistic_type': 'total_annotations',
            'model_identifier': 'ALL',
            'value': overall_stats['total_annotations'],
            'description': '总标注数'
        })
        data.append({
            'statistic_type': 'completed_annotations',
            'model_identifier': 'ALL',
            'value': overall_stats['completed_annotations'],
            'description': '已完成标注数'
        })
        data.append({
            'statistic_type': 'failed_annotations',
            'model_identifier': 'ALL',
            'value': overall_stats['failed_annotations'],
            'description': '失败标注数'
        })
        data.append({
            'statistic_type': 'success_rate',
            'model_identifier': 'ALL',
            'value': f"{overall_stats['success_rate']:.2f}%",
            'description': '总体成功率'
        })
        
        # 添加各模型统计
        for model, stats in annotation_stats['by_model'].items():
            data.append({
                'statistic_type': 'model_total',
                'model_identifier': model,
                'value': stats['total'],
                'description': f"模型 {model} 总标注数"
            })
            data.append({
                'statistic_type': 'model_completed',
                'model_identifier': model,
                'value': stats['completed'],
                'description': f"模型 {model} 已完成标注数"
            })
            data.append({
                'statistic_type': 'model_failed',
                'model_identifier': model,
                'value': stats['failed'],
                'description': f"模型 {model} 失败标注数"
            })
            data.append({
                'statistic_type': 'model_success_rate',
                'model_identifier': model,
                'value': f"{stats['success_rate']:.2f}%",
                'description': f"模型 {model} 成功率"
            })
            
        # 添加状态统计
        for status, count in annotation_stats['by_status'].items():
            data.append({
                'statistic_type': 'status_count',
                'model_identifier': status,
                'value': count,
                'description': f"状态为 {status} 的标注数"
            })
        
        df = pd.DataFrame(data)
        
        # 输出结果
        print("\n=== 标注统计结果 ===")
        print(df.to_string(index=False))
        
        # 如果指定了输出文件，则保存到CSV
        if args.output:
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"\n统计结果已保存到: {args.output}")
            
    except Exception as e:
        print(f"执行统计时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
