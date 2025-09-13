# GUI实施计划

本计划旨在逐步实现 `docs/GUI设计方案.md` 中描述的PyQt GUI方案。

## 阶段划分与任务

### 阶段1: 环境准备与核心GUI组件实现

**目标**: 搭建GUI开发环境，并实现应用程序的基础框架和核心通用组件。

*   **任务 1.1**: 安装PyQt5/PySide6。
    *   说明: 根据项目需求选择并安装合适的PyQt版本。
*   **任务 1.2**: 实现 `gui/utils.py` 中的 `LogStreamHandler`。
    *   说明: 创建一个自定义的 `logging.Handler`，用于将Python日志输出重定向到GUI组件（如 `QTextEdit` 或 `QStatusBar`）。
*   **任务 1.3**: 实现 `gui/script_panel_base.py` 中的 `ScriptPanelBase` 类。
    *   说明: 定义所有脚本面板的基类，提供通用接口和功能，如 `setup_ui()` (抽象方法), `run_script()` (抽象方法), `_create_worker()`, `_update_status()` 等。
*   **任务 1.4**: 实现 `gui/workers.py` 中的 `ScriptWorker` 类。
    *   说明: 继承自 `QThread`，用于在单独线程中执行脚本，确保GUI响应性。定义 `finished`, `error_occurred`, `output_emitted`, `progress_updated` 等信号。
*   **任务 1.5**: 实现 `gui/main_window.py` 中的 `MainWindow` 类。
    *   说明: 继承自 `QMainWindow`，作为主应用程序窗口。包含 `QTabWidget` 用于脚本面板，`QStatusBar` 用于状态显示，并集成日志处理器。
*   **任务 1.6**: 实现 `gui/app.py` 作为应用程序入口。
    *   说明: 负责创建 `QApplication` 实例，实例化并显示 `MainWindow`，然后启动Qt事件循环。

### 阶段2: 脚本特定面板实现与集成

**目标**: 为每个后台脚本创建独立的GUI面板，并将其集成到主窗口中。

*   **任务 2.1**: 创建 `gui/script_panels/__init__.py`。
*   **任务 2.2**: 实现 `AnnotationStatisticsPanel` (`gui/script_panels/annotation_statistics_panel.py`)。
    *   说明: 为 `scripts/annotation_statistics.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.3**: 实现 `DistributeTasksPanel` (`gui/script_panels/distribute_tasks_panel.py`)。
    *   说明: 为 `scripts/distribute_tasks.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.4**: 实现 `ExportPoemAnnotationsPanel` (`gui/script_panels/export_poem_annotations_panel.py`)。
    *   说明: 为 `scripts/export_poem_annotations.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.5**: 实现 `FindDuplicatePoemsPanel` (`gui/script_panels/find_duplicate_poems_panel.py`)。
    *   说明: 为 `scripts/find_duplicate_poems.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.6**: 实现 `ProofreadAnnotationsPanel` (`gui/script_panels/proofread_annotations_panel.py`)。
    *   说明: 为 `scripts/proofread_annotations.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.7**: 实现 `RandomSamplePanel` (`gui/script_panels/random_sample_panel.py`)。
    *   说明: 为 `scripts/random_sample.py` 脚本设计UI，收集参数，并触发 `ScriptWorker` 执行。
*   **任务 2.8**: 将所有 `ScriptPanel` 实例集成到 `MainWindow` 的 `QTabWidget` 中。
    *   说明: 在 `MainWindow` 初始化时，创建并添加各个脚本面板作为标签页。

### 阶段3: 配置管理功能实现

**目标**: 实现全局和项目配置的GUI编辑功能。

*   **任务 3.1**: 增强 `gui/config_manager.py`。
    *   说明: 开发GUI特定的配置逻辑，与后端配置系统 (`src/config` 模块) 交互，负责加载、保存和处理配置模式。
*   **任务 3.2**: 修改 `gui/main_window.py`。
    *   说明: 添加 `QMenuBar` 和“设置”菜单，包含“编辑全局配置”和“编辑项目配置”等操作。
*   **任务 3.3**: 实现 `GlobalConfigPanel` (`gui/config_panels/global_config_panel.py`)。
    *   说明: 继承自 `QWidget` 或 `QDialog`，使用 `QFormLayout` 展示全局配置参数，实现加载、编辑、保存和验证逻辑。
*   **任务 3.4**: 实现 `ProjectConfigPanel` (`gui/config_panels/project_config_panel.py`)。
    *   说明: 类似于 `GlobalConfigPanel`，但专注于项目级配置，并可能包含项目选择功能。
*   **任务 3.5**: 将配置面板集成到 `MainWindow`。
    *   说明: 根据设计选择以模态对话框或新标签页的形式打开配置面板。
*   **任务 3.6**: 实现配置验证和用户反馈机制。
    *   说明: 在配置面板中添加健壮的输入验证，并在保存后提供成功或错误消息。

### 阶段4: 测试与优化

**目标**: 确保GUI的稳定性、功能完整性和用户体验。

*   **任务 4.1**: 逐个测试每个脚本面板的功能。
    *   说明: 验证参数传递、脚本执行、结果显示和日志输出是否正确。
*   **任务 4.2**: 测试全局和项目配置的加载、编辑、保存和验证功能。
    *   说明: 确保配置能够正确持久化，并且验证逻辑有效。
*   **任务 4.3**: 确保GUI的响应性和错误处理。
    *   说明: 验证耗时操作不会阻塞GUI，并且错误信息能够友好地显示给用户。
*   **任务 4.4**: 根据测试反馈进行UI/UX优化和代码重构。
    *   说明: 改进界面布局、交互流程，并优化代码结构以提高可维护性。

### 阶段5: 国际化 (i18n) 支持

**目标**: 为GUI添加多语言支持，不依赖Qt开发工具，并提供中文作为示例。

*   **任务 5.1**: 创建 `gui/locale` 目录。
    *   说明: 用于存放 `.po` (Portable Object) 和 `.mo` (Machine Object) 文件。例如 `gui/locale/zh_CN/LC_MESSAGES/app.po`。
*   **任务 5.2**: 修改所有UI相关代码以支持 `gettext` 翻译。
    *   说明: 遍历所有GUI组件 (`main_window.py`, `script_panels/*.py` 等)，将用户可见的字符串用 `gettext.gettext()` 或其别名 `_()` 包装。
*   **任务 5.3**: 提取待翻译字符串。
    *   说明: 使用 `pygettext` 工具扫描 `gui` 目录，生成 `app.po` 文件。
    *   示例命令: `python -m pygettext -o gui/locale/app.po gui/*.py gui/script_panels/*.py gui/config_panels/*.py gui/utils.py gui/main_window.py gui/app.py`
*   **任务 5.4**: 翻译字符串。
    *   说明: (手动任务) 使用任何文本编辑器或兼容 `gettext` 的翻译工具打开 `gui/locale/app.po` 文件并填入中文翻译。然后将 `app.po` 复制到 `gui/locale/zh_CN/LC_MESSAGES/app.po`。
*   **任务 5.5**: 编译翻译文件。
    *   说明: 使用 `msgfmt` 工具将 `.po` 编译成 `.mo`。如果 `msgfmt` 不可用，可以考虑使用纯Python的 `.po` 到 `.mo` 编译器或直接加载 `.po` 文件（如果 `gettext` 模块支持）。
    *   示例命令: `msgfmt -o gui/locale/zh_CN/LC_MESSAGES/app.mo gui/locale/zh_CN/LC_MESSAGES/app.po`
*   **任务 5.6**: 在应用程序中加载翻译。
    *   说明: 修改 `gui/app.py`，在启动时创建并安装 `gettext.translation` 实例。
    *   示例代码:
        ```python
        import sys
        import os
        import gettext
        from PyQt5.QtWidgets import QApplication
        from .main_window import MainWindow

        LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')
        gettext.bindtextdomain('app', LOCALE_DIR)
        gettext.textdomain('app')
        _ = gettext.gettext

        def main():
            app = QApplication(sys.argv)
            lang = 'zh_CN' # 从配置或系统获取语言
            try:
                translator = gettext.translation('app', LOCALE_DIR, languages=[lang])
                translator.install()
            except FileNotFoundError:
                print(f"Warning: Translation file for {lang} not found in {LOCALE_DIR}")

            main_window = MainWindow()
            main_window.show()
            sys.exit(app.exec_())

        if __name__ == '__main__':
            main()
        ```
*   **任务 5.7**: 测试国际化功能。
    *   说明: 运行应用，验证UI是否已正确显示为中文。
