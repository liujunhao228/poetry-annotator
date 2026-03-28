"""任务执行服务"""

import subprocess
import threading
import queue
import sys
import os
from typing import Optional, Callable, List, Any
from pathlib import Path


class TaskExecutor:
    """
    统一的任务执行服务
    
    负责异步执行外部脚本，管理子进程生命周期，处理输出日志。
    替代原来 TaskExecutorTab 中的任务执行逻辑。
    """
    
    def __init__(self, log_callback: Callable[[str], None]):
        """
        初始化任务执行器
        
        Args:
            log_callback: 日志输出回调函数，用于将日志发送到 UI
        """
        self.log_callback = log_callback
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.output_queue: queue.Queue = queue.Queue()
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """任务是否正在运行"""
        return self._is_running
    
    def execute(
        self,
        script_name: str,
        args: List[str],
        script_dir: Optional[Path] = None
    ) -> bool:
        """
        异步执行脚本

        Args:
            script_name: 脚本文件名
            args: 命令行参数列表
            script_dir: 脚本所在目录，默认为项目 scripts 目录

        Returns:
            是否成功启动任务
        """
        if self._is_running:
            self.log_callback("错误：已有任务正在运行\n")
            return False

        # 确定脚本路径
        if script_dir is None:
            # 使用 resolve() 确保获取绝对路径
            # task_executor.py 位于 src/gui/services/，需要往上三层到达项目根目录
            current = Path(__file__).resolve()
            project_root = current.parent.parent.parent  # src/gui/services -> src/gui -> src -> project_root
            
            # 验证：如果 project_root 下没有 scripts 目录，说明可能在 src 目录下运行
            # 此时需要再往上一层
            if not (project_root / 'scripts').exists() and (project_root.parent / 'scripts').exists():
                project_root = project_root.parent
            
            script_dir = project_root / 'scripts'

        script_path = script_dir / script_name

        # 调试信息：显示脚本查找路径
        self.log_callback(f"脚本目录：{script_dir}\n")
        self.log_callback(f"脚本路径：{script_path}\n")

        if not script_path.exists():
            self.log_callback(f"错误：找不到脚本 '{script_name}'\n")
            self.log_callback(f"脚本目录存在：{script_dir.exists()}\n")
            if script_dir.exists():
                scripts_in_dir = list(script_dir.glob('*.py'))
                self.log_callback(f"scripts 目录下的文件：{[f.name for f in scripts_in_dir]}\n")
            return False
        
        # 构建命令
        command = [sys.executable, str(script_path)] + args
        
        # 显示执行的命令
        display_command = ' '.join(f'"{str(arg)}"' if ' ' in str(arg) else str(arg) for arg in command)
        self.log_callback(f"执行命令：{display_command}\n" + "=" * 80 + "\n")
        
        # 启动任务线程
        self._is_running = True
        self.thread = threading.Thread(
            target=self._run_task,
            args=(command,),
            daemon=True
        )
        self.thread.start()
        
        # 启动队列处理
        self._start_queue_processing()
        
        return True
    
    def _run_task(self, command: List[str]) -> None:
        """在后台线程中执行子进程"""
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=creation_flags
            )
            
            if self.process.stdout is not None:
                for line in iter(self.process.stdout.readline, ''):
                    self.output_queue.put(line)
                self.process.stdout.close()
            
            self.process.wait()
            
        except Exception as e:
            self.output_queue.put(f"\n****** 任务执行失败 ******\n{e}\n")
        
        finally:
            self.output_queue.put(None)  # 任务结束信号
    
    def _start_queue_processing(self) -> None:
        """启动队列消息处理（需在主线程中调用）"""
        # 这里使用 after 延迟调用，确保在主线程执行
        if hasattr(self, 'master') and hasattr(self.master, 'after'):
            self.master.after(100, self._process_queue)
        else:
            # 如果没有 master，直接在当前线程处理（不推荐）
            self._process_queue()
    
    def _process_queue(self) -> None:
        """从队列批量获取消息并回调"""
        messages_to_log = []
        task_finished = False
        
        try:
            for _ in range(200):
                line = self.output_queue.get_nowait()
                if line is None:
                    task_finished = True
                    break
                messages_to_log.append(line)
        except queue.Empty:
            pass
        
        # 批量回调
        if messages_to_log:
            self.log_callback("".join(messages_to_log))
        
        # 任务完成处理
        if task_finished:
            self._on_task_finished()
            return
        
        # 继续处理队列
        if hasattr(self, 'master') and hasattr(self.master, 'after'):
            self.master.after(100, self._process_queue)
    
    def _on_task_finished(self) -> None:
        """任务完成回调"""
        return_code = self.process.returncode if self.process else -1
        
        final_message = "\n" + "=" * 80 + "\n"
        if return_code == 0:
            final_message += "任务执行成功完成。\n"
        else:
            final_message += f"任务执行结束，返回代码：{return_code} (0 表示成功)。\n"
        
        self.log_callback(final_message)
        
        self.process = None
        self._is_running = False
    
    def stop(self) -> bool:
        """
        终止当前任务
        
        Returns:
            是否成功终止
        """
        if not self.process:
            return False
        
        self.log_callback("\n****** 正在尝试终止任务... ******\n")
        
        try:
            self.process.terminate()
            self.process.wait(timeout=2)
            self.log_callback("任务已终止。\n")
            return True
        except subprocess.TimeoutExpired:
            self.log_callback("无法正常终止，将强制结束。\n")
            self.process.kill()
            return True
        except Exception as e:
            self.log_callback(f"终止任务失败：{e}\n")
            return False
        finally:
            self.output_queue.put(None)
            self._is_running = False
