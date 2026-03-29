"""异步任务执行服务 - 基于 asyncio"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional, Callable, List, Any
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncTaskExecutor:
    """
    异步任务执行服务
    
    基于 asyncio 和 subprocess 异步执行外部脚本。
    支持实时日志输出、任务取消、状态查询。
    
    使用示例:
        executor = AsyncTaskExecutor(log_callback=print)
        
        # 异步执行
        await executor.execute("script.py", ["--arg", "value"])
        
        # 或在线程中运行（Tkinter 应用）
        executor.execute_in_thread("script.py", ["--arg", "value"])
    """
    
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        初始化异步任务执行器
        
        Args:
            log_callback: 日志输出回调函数
        """
        self.log_callback = log_callback or print
        self._process: Optional[asyncio.subprocess.Process] = None
        self._task: Optional[asyncio.Task] = None
        self._status = TaskStatus.IDLE
        self._return_code: Optional[int] = None
    
    @property
    def status(self) -> TaskStatus:
        """获取当前任务状态"""
        return self._status
    
    @property
    def is_running(self) -> bool:
        """任务是否正在运行"""
        return self._status == TaskStatus.RUNNING
    
    @property
    def return_code(self) -> Optional[int]:
        """获取任务返回码"""
        return self._return_code
    
    async def execute(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        script_dir: Optional[Path] = None,
        cwd: Optional[Path] = None
    ) -> int:
        """
        异步执行脚本
        
        Args:
            script_name: 脚本文件名
            args: 命令行参数列表
            script_dir: 脚本所在目录，默认为项目 scripts 目录
            cwd: 工作目录
        
        Returns:
            进程返回码
        """
        if self._status == TaskStatus.RUNNING:
            self.log_callback("错误：已有任务正在运行\n")
            return -1
        
        args = args or []
        
        # 确定脚本路径
        if script_dir is None:
            current = Path(__file__).resolve()
            project_root = current.parent.parent.parent
            
            if not (project_root / 'scripts').exists() and (project_root.parent / 'scripts').exists():
                project_root = project_root.parent
            
            script_dir = project_root / 'scripts'
        
        script_path = script_dir / script_name
        
        # 调试信息
        self.log_callback(f"脚本目录：{script_dir}\n")
        self.log_callback(f"脚本路径：{script_path}\n")
        
        if not script_path.exists():
            self.log_callback(f"错误：找不到脚本 '{script_name}'\n")
            self._status = TaskStatus.FAILED
            return -1
        
        # 构建命令
        command = [sys.executable, str(script_path)] + args
        
        # 显示执行的命令
        display_command = ' '.join(f'"{str(arg)}"' if ' ' in str(arg) else str(arg) for arg in command)
        self.log_callback(f"执行命令：{display_command}\n" + "=" * 80 + "\n")
        
        self._status = TaskStatus.RUNNING
        self._return_code = None
        
        try:
            # 创建子进程
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(cwd) if cwd else None
            )
            
            # 实时读取输出
            if self._process.stdout:
                async for line in self._process.stdout:
                    decoded_line = line.decode('utf-8', errors='replace')
                    self.log_callback(decoded_line)
            
            # 等待进程结束
            self._return_code = await self._process.wait()
            
            # 完成处理
            if self._return_code == 0:
                self.log_callback("\n" + "=" * 80 + "\n任务执行成功完成。\n")
                self._status = TaskStatus.COMPLETED
            else:
                self.log_callback(f"\n" + "=" * 80 + f"\n任务执行结束，返回代码：{self._return_code} (0 表示成功)。\n")
                self._status = TaskStatus.FAILED
            
            return self._return_code
            
        except asyncio.CancelledError:
            self.log_callback("\n****** 任务已取消 ******\n")
            self._status = TaskStatus.CANCELLED
            raise
            
        except Exception as e:
            self.log_callback(f"\n****** 任务执行失败 ******\n{e}\n")
            self._status = TaskStatus.FAILED
            self._return_code = -1
            return -1
            
        finally:
            self._process = None
    
    def execute_in_thread(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        script_dir: Optional[Path] = None,
        cwd: Optional[Path] = None,
        on_complete: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        在独立线程中执行脚本（用于 Tkinter 等需要同步调用的场景）
        
        Args:
            script_name: 脚本文件名
            args: 命令行参数列表
            script_dir: 脚本所在目录
            cwd: 工作目录
            on_complete: 完成回调，接收返回码
        
        Returns:
            是否成功启动任务
        """
        if self._status == TaskStatus.RUNNING:
            self.log_callback("错误：已有任务正在运行\n")
            return False
        
        import threading
        
        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return_code = loop.run_until_complete(
                    self.execute(script_name, args, script_dir, cwd)
                )
                if on_complete:
                    on_complete(return_code)
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async_task, daemon=True)
        thread.start()
        return True
    
    async def cancel(self) -> bool:
        """
        取消当前任务
        
        Returns:
            是否成功取消
        """
        if not self._process or self._status != TaskStatus.RUNNING:
            return False
        
        self.log_callback("\n****** 正在尝试终止任务... ******\n")
        
        try:
            if sys.platform == "win32":
                # Windows: 使用 terminate 发送 CTRL_BREAK_EVENT
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._process.terminate()
            
            # 等待 2 秒
            await asyncio.wait_for(self._process.wait(), timeout=2.0)
            self.log_callback("任务已终止。\n")
            self._status = TaskStatus.CANCELLED
            return True
            
        except asyncio.TimeoutError:
            self.log_callback("无法正常终止，将强制结束。\n")
            self._process.kill()
            self._status = TaskStatus.CANCELLED
            return True
            
        except Exception as e:
            self.log_callback(f"终止任务失败：{e}\n")
            return False
    
    def cancel_sync(self) -> bool:
        """
        同步方式取消任务（用于非异步环境）
        
        Returns:
            是否成功取消
        """
        if not self._process or self._status != TaskStatus.RUNNING:
            return False
        
        self.log_callback("\n****** 正在尝试终止任务... ******\n")
        
        try:
            if sys.platform == "win32":
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._process.terminate()
            
            # 等待 2 秒
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.log_callback("无法正常终止，将强制结束。\n")
                self._process.kill()
            
            self._status = TaskStatus.CANCELLED
            return True
            
        except Exception as e:
            self.log_callback(f"终止任务失败：{e}\n")
            return False


# 兼容旧代码的包装器
class TaskExecutor:
    """
    任务执行器 - 兼容旧代码的包装器
    
    内部使用 AsyncTaskExecutor，提供与旧 API 兼容的接口。
    """
    
    def __init__(self, log_callback: Callable[[str], None]):
        """
        初始化任务执行器
        
        Args:
            log_callback: 日志输出回调函数
        """
        self._executor = AsyncTaskExecutor(log_callback)
        self.log_callback = log_callback
        self.process = None  # 兼容旧代码
        self.thread = None   # 兼容旧代码
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """任务是否正在运行"""
        return self._executor.is_running
    
    def execute(
        self,
        script_name: str,
        args: List[str],
        script_dir: Optional[Path] = None
    ) -> bool:
        """
        执行脚本（在线程中，兼容旧 API）
        
        Args:
            script_name: 脚本文件名
            args: 命令行参数列表
            script_dir: 脚本所在目录
        
        Returns:
            是否成功启动任务
        """
        def on_complete(return_code: int):
            self._is_running = False
        
        success = self._executor.execute_in_thread(
            script_name,
            args,
            script_dir,
            on_complete=on_complete
        )
        
        if success:
            self._is_running = True
            # 保存对内部进程的引用（兼容旧代码）
            self.process = self._executor._process
        return success
    
    def stop(self) -> bool:
        """
        终止当前任务
        
        Returns:
            是否成功终止
        """
        result = self._executor.cancel_sync()
        self._is_running = False
        return result


# 需要导入 signal 模块
import signal
