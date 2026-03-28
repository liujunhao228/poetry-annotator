#!/usr/bin/env python3
"""
配置迁移工具 - 将旧版三文件配置结构迁移到简化版两文件结构

旧结构:
- config/config.ini (全局配置)
- projects/<project>/config.ini (项目配置)
- projects/<project>/project_config.ini (项目额外配置)

新结构:
- config/config.ini (仅激活项目设置)
- projects/<project>/config.ini (完整项目配置，合并后唯一来源)
"""

import configparser
import shutil
import sys
from pathlib import Path
from typing import Optional


def find_project_config_files(project_root: Path, project_name: str) -> tuple[Path, Path, Optional[Path]]:
    """
    查找项目的所有配置文件
    
    Returns:
        (global_config, project_config, project_extra_config) 元组
        project_extra_config 可能为 None（如果不存在）
    """
    global_config = project_root / "config" / "config.ini"
    project_config = project_root / "projects" / project_name / "config.ini"
    project_extra_config = project_root / "projects" / project_name / "project_config.ini"
    
    if not global_config.exists():
        raise FileNotFoundError(f"全局配置文件不存在：{global_config}")
    if not project_config.exists():
        raise FileNotFoundError(f"项目配置文件不存在：{project_config}")
    
    return global_config, project_config, project_extra_config if project_extra_config.exists() else None


def merge_configs(global_config_path: Path, project_config_path: Path, project_extra_config_path: Optional[Path]) -> configparser.ConfigParser:
    """
    合并多个配置文件为单一配置
    
    优先级：project_extra_config > project_config > global_config (默认值)
    """
    merged = configparser.ConfigParser(interpolation=None)
    
    # 1. 首先读取全局配置作为默认值（但排除 Project 节的 active_project_config）
    if global_config_path.exists():
        global_config = configparser.ConfigParser(interpolation=None)
        global_config.read(global_config_path, encoding='utf-8')
        
        for section in global_config.sections():
            # Project 节只保留激活项目设置，不合并到项目配置
            if section == 'Project':
                continue
            # Model 节不合并，每个项目应该有自己的模型配置
            if section.startswith('Model.'):
                continue
            merged.add_section(section)
            for key, value in global_config.items(section):
                merged.set(section, key, value)
    
    # 2. 读取项目配置（覆盖全局配置）
    project_config = configparser.ConfigParser(interpolation=None)
    project_config.read(project_config_path, encoding='utf-8')
    
    for section in project_config.sections():
        if section == 'Project':
            continue
        if not merged.has_section(section):
            merged.add_section(section)
        for key, value in project_config.items(section):
            merged.set(section, key, value)
    
    # 3. 读取项目额外配置（最高优先级）
    if project_extra_config_path and project_extra_config_path.exists():
        extra_config = configparser.ConfigParser(interpolation=None)
        extra_config.read(project_extra_config_path, encoding='utf-8')
        
        for section in extra_config.sections():
            if not merged.has_section(section):
                merged.add_section(section)
            for key, value in extra_config.items(section):
                merged.set(section, key, value)
    
    return merged


def migrate_project(project_root: Path, project_name: str, backup: bool = True) -> Path:
    """
    迁移单个项目的配置到简化结构
    
    Args:
        project_root: 项目根目录
        project_name: 项目名称
        backup: 是否备份旧配置文件
        
    Returns:
        新的项目配置文件路径
    """
    print(f"\n{'='*60}")
    print(f"迁移项目配置：{project_name}")
    print(f"{'='*60}")
    
    # 查找配置文件
    global_config, project_config, project_extra_config = find_project_config_files(
        project_root, project_name
    )
    
    print(f"找到配置文件:")
    print(f"  - 全局配置：{global_config}")
    print(f"  - 项目配置：{project_config}")
    if project_extra_config:
        print(f"  - 项目额外配置：{project_extra_config}")
    
    # 备份旧文件
    if backup:
        timestamp = Path(project_config).stem
        backup_path = Path(project_config).with_suffix(f".ini.backup")
        shutil.copy2(project_config, backup_path)
        print(f"已备份项目配置：{backup_path}")
        
        if project_extra_config:
            extra_backup = Path(project_extra_config).with_suffix(f".backup")
            shutil.copy2(project_extra_config, extra_backup)
            print(f"已备份项目额外配置：{extra_backup}")
    
    # 合并配置
    print("\n合并配置...")
    merged_config = merge_configs(global_config, project_config, project_extra_config)
    
    # 添加项目元数据
    if not merged_config.has_section('Project'):
        merged_config.add_section('Project')
    merged_config.set('Project', 'name', project_name)
    
    # 写入新的项目配置文件（覆盖原 project_config.ini）
    new_config_path = project_config
    with open(new_config_path, 'w', encoding='utf-8') as f:
        merged_config.write(f)
    
    print(f"\n✓ 配置已合并到：{new_config_path}")
    
    # 如果存在 project_extra_config，建议删除或保留为备份
    if project_extra_config:
        print(f"\n提示：{project_extra_config} 已合并，可以安全删除或保留作为备份")
    
    return new_config_path


def update_global_config(project_root: Path, project_name: str) -> Path:
    """
    更新全局配置文件，仅保留激活项目设置
    """
    global_config_path = project_root / "config" / "config.ini"
    
    if not global_config_path.exists():
        raise FileNotFoundError(f"全局配置文件不存在：{global_config_path}")
    
    # 读取现有全局配置
    config = configparser.ConfigParser(interpolation=None)
    config.read(global_config_path, encoding='utf-8')
    
    # 保留 Project 节，更新激活项目配置路径
    if not config.has_section('Project'):
        config.add_section('Project')
    
    # 更新激活项目配置路径
    active_project_config = f"projects/{project_name}/config.ini"
    config.set('Project', 'active_project_config', active_project_config)
    
    # 写入更新后的全局配置
    with open(global_config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"✓ 全局配置已更新：{global_config_path}")
    print(f"  激活项目配置：{active_project_config}")
    
    return global_config_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="将旧版三文件配置结构迁移到简化版两文件结构"
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        help="要迁移的项目名称（默认：迁移所有项目）"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不备份旧配置文件"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要执行的操作，不实际修改文件"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    project_root = Path(__file__).resolve().parent.parent
    
    print(f"项目根目录：{project_root}")
    
    # 确定要迁移的项目
    projects_dir = project_root / "projects"
    if not projects_dir.exists():
        print(f"错误：项目目录不存在：{projects_dir}")
        sys.exit(1)
    
    if args.project:
        projects_to_migrate = [args.project]
        if not (projects_dir / args.project).exists():
            print(f"错误：项目不存在：{args.project}")
            sys.exit(1)
    else:
        projects_to_migrate = [
            d.name for d in projects_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]
    
    print(f"\n将要迁移的项目：{', '.join(projects_to_migrate)}")
    
    if args.dry_run:
        print("\n[干运行模式] 不会修改任何文件")
        for project_name in projects_to_migrate:
            print(f"\n项目：{project_name}")
            try:
                global_config, project_config, project_extra_config = find_project_config_files(
                    project_root, project_name
                )
                print(f"  将合并:")
                print(f"    - {global_config}")
                print(f"    - {project_config}")
                if project_extra_config:
                    print(f"    - {project_extra_config}")
                print(f"  输出到：{project_config}")
            except FileNotFoundError as e:
                print(f"  错误：{e}")
        return
    
    # 执行迁移
    for project_name in projects_to_migrate:
        try:
            migrate_project(
                project_root,
                project_name,
                backup=not args.no_backup
            )
            update_global_config(project_root, project_name)
        except FileNotFoundError as e:
            print(f"\n跳过项目 {project_name}: {e}")
        except Exception as e:
            print(f"\n迁移项目 {project_name} 失败：{e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("迁移完成!")
    print(f"{'='*60}")
    print("\n下一步:")
    print("1. 验证配置文件内容是否正确")
    print("2. 运行程序测试配置是否正常工作")
    print("3. 确认无误后，可以删除 .backup 文件")


if __name__ == "__main__":
    main()
