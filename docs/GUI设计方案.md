### PyQt方案


**1. 项目结构 (Project Structure)**

为了保持GUI代码的组织性和与现有脚本的分离，我建议采用以下目录结构：

```
poetry-annotator/
├── scripts/
│   ├── annotation_statistics.py
│   ├── distribute_tasks.py
│   └── ... (其他脚本)
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # 主窗口 (QMainWindow)
│   ├── script_panel_base.py    # 脚本面板基类
│   ├── script_panels/          # 各脚本的独立面板
│   │   ├── __init__.py
│   │   ├── annotation_statistics_panel.py
│   │   ├── distribute_tasks_panel.py
│   │   ├── export_poem_annotations_panel.py
│   │   ├── find_duplicate_poems_panel.py
│   │   ├── proofread_annotations_panel.py
│   │   ├── random_sample_panel.py
│   ├── workers.py              # 后台工作线程 (QThread)
│   ├── utils.py                # GUI辅助工具 (如日志重定向)
│   └── app.py                  # 应用程序入口
```

**2. 核心组件设计 (Core Component Design)**

*   **`app.py` (应用程序入口)**:
    *   负责创建 `QApplication` 实例。
    *   实例化 `MainWindow` 并显示。
    *   启动Qt事件循环。

*   **`main_window.py` (主窗口 - `MainWindow` 类)**:
    *   继承自 `QMainWindow`。
    *   **布局**:
        *   中央区域使用 `QTabWidget`，每个标签页对应一个脚本操作界面。
        *   底部包含 `QStatusBar` 用于显示全局状态信息。
        *   可选：顶部添加 `QMenuBar` 和 `QToolBar` 提供通用功能（如设置、关于）。
        *   可选：可停靠的 `QDockWidget` 用于显示全局日志输出。
    *   **功能**:
        *   初始化 `QTabWidget` 并添加各个 `ScriptPanel` 实例作为标签页。
        *   设置全局日志处理器，将日志输出重定向到状态栏或独立的日志显示区。
        *   管理应用程序的生命周期。

*   **`script_panel_base.py` (脚本面板基类 - `ScriptPanelBase` 类)**:
    *   继承自 `QWidget`。
    *   定义所有脚本面板的通用接口和功能，例如：
        *   `setup_ui()`: 抽象方法，用于构建特定脚本的UI。
        *   `run_script()`: 抽象方法，用于触发脚本执行。
        *   `_create_worker()`: 创建并启动 `QThread` 的方法。
        *   `_update_status()`: 更新面板内部状态或进度的方法。
        *   提供通用的文件/目录选择对话框方法。
        *   提供参数验证逻辑。

*   **`script_panels/*.py` (具体脚本面板 - 例如 `AnnotationStatisticsPanel` 类)**:
    *   每个脚本对应一个独立的类，继承自 `ScriptPanelBase`。
    *   **UI布局**:
        *   使用 `QFormLayout` 或 `QGridLayout` 组织输入控件。
        *   例如，`AnnotationStatisticsPanel` 会有：
            *   `QLineEdit` 用于 `db` 名称。
            *   `QLineEdit` 和 `QPushButton` (带 `QFileDialog`) 用于 `output` 文件路径。
            *   一个 `QPushButton` 作为 "运行统计" 按钮。
            *   一个 `QTextEdit` 或 `QTableWidget` 用于显示统计结果。
    *   **参数收集**: 从UI控件中读取用户输入，组装成字典或列表，传递给后台工作线程。
    *   **脚本执行逻辑**:
        *   当 "运行" 按钮被点击时，收集参数。
        *   实例化一个 `ScriptWorker` (见下文) 并传入脚本名称和参数。
        *   连接 `ScriptWorker` 的信号 (如 `finished`, `progress_updated`, `output_emitted`) 到面板的槽函数，以更新UI。
        *   启动 `ScriptWorker` 线程。
    *   **结果显示**: 根据脚本的输出类型，将结果显示在 `QTextEdit` (日志/Markdown) 或 `QTableWidget` (表格数据) 中。

*   **`workers.py` (后台工作线程 - `ScriptWorker` 类)**:
    *   继承自 `QThread`。
    *   **信号**:
        *   `finished`: 脚本执行完成时发出。
        *   `error_occurred(str)`: 脚本执行出错时发出错误信息。
        *   `output_emitted(str)`: 脚本产生输出时发出 (用于实时日志)。
        *   `progress_updated(int, str)`: 脚本更新进度时发出。
    *   **`run()` 方法**:
        *   在此方法中，通过 `subprocess` 模块调用实际的Python脚本。
        *   捕获脚本的 `stdout` 和 `stderr`，并通过 `output_emitted` 信号实时发送给GUI。
        *   处理脚本的退出码，根据成功或失败发出 `finished` 或 `error_occurred` 信号。
        *   **重要**: 为了避免阻塞GUI，脚本的实际执行（例如 `distribute_tasks.py` 中的 `run_distribution_task` 函数）应该被设计为可被导入和直接调用的Python函数，而不是仅仅依赖 `subprocess` 调用命令行。这样可以更灵活地传递参数和获取返回值。如果脚本只能通过命令行调用，则 `subprocess` 是唯一的选择。

*   **`utils.py` (GUI辅助工具)**:
    *   **`LogStreamHandler`**: 一个自定义的 `logging.Handler`，将Python `logging` 模块的输出重定向到 `QTextEdit` 或 `QStatusBar`。
    *   **`ConfigManager`**: 用于加载和保存GUI的配置，例如默认数据库路径、上次使用的模型等。

**3. 核心设计思路 (Core Design Ideas)**

*   **解耦 (Decoupling)**:
    *   GUI界面 (`ScriptPanel`s) 与后台脚本执行逻辑 (`ScriptWorker`s) 严格分离。
    *   脚本本身保持其命令行接口，GUI作为其上层封装。
*   **响应性 (Responsiveness)**:
    *   所有耗时操作 (脚本执行、文件I/O) 都在独立的 `QThread` 中运行，确保主GUI线程始终响应用户操作。
    *   通过Qt的信号与槽机制，安全地从工作线程向主线程传递数据和更新UI。
*   **用户体验 (User Experience)**:
    *   **统一的导航**: 使用 `QTabWidget` 提供清晰的脚本导航。
    *   **直观的输入**: 针对不同类型的参数使用最合适的GUI控件 (文本框、复选框、文件选择器等)。
    *   **实时反馈**: 通过日志区和进度条提供脚本执行的实时状态和结果。
    *   **错误处理**: 捕获脚本执行中的错误，并在GUI中以用户友好的方式显示。
*   **可扩展性 (Extensibility)**:
    *   `ScriptPanelBase` 提供了统一的接口，方便未来添加新的脚本。
    *   通过将脚本的参数定义（例如从 `argparse` 解析）作为元数据，可以考虑实现一个**参数解析器**，动态生成大部分输入表单，进一步减少重复代码。
*   **配置管理**:
    *   允许用户保存常用参数配置，例如默认的数据库名称、输出目录等，提高使用效率。

**4. 实施步骤 (Implementation Steps)**

1.  **环境准备**: 确保安装 PyQt5/PySide6 (`pip install PyQt5` 或 `pip install PySide6`)。
2.  **项目结构搭建**: 创建 `gui/` 目录及其子目录和文件。
3.  **日志重定向**: 实现 `LogStreamHandler`，将 `logging` 模块的输出重定向到GUI的 `QTextEdit`。
4.  **基类实现**: 实现 `ScriptPanelBase` 和 `ScriptWorker`。
5.  **主窗口实现**: 实现 `MainWindow`，包含 `QTabWidget` 和状态栏。
6.  **逐个脚本面板实现**:
    *   为每个 `scripts/` 下的脚本创建一个 `ScriptPanel` 类。
    *   根据脚本的 `argparse` 参数，设计并实现对应的UI控件。
    *   在 `run_script` 方法中，收集参数并启动 `ScriptWorker`。
    *   处理 `ScriptWorker` 发出的信号，更新UI显示结果和日志。
7.  **测试**: 逐个测试每个脚本面板的功能，确保参数传递正确，脚本能正常执行，并且GUI能正确显示输出和状态。

这个细化方案提供了更具体的实现路径和组件职责，为实际开发奠定了基础。

### 拓展GUI设计：配置管理与编辑

**1. 项目结构 (Project Structure) - 增补**

为了容纳配置管理功能，建议增加一个用于配置相关GUI组件的新模块：

```
poetry-annotator/
├── gui/
│   ├── ...
│   ├── config_manager.py       # GUI特定的配置逻辑（例如，加载/保存，模式处理）
│   ├── config_panels/          # 配置编辑面板
│   │   ├── __init__.py
│   │   ├── global_config_panel.py  # 全局配置编辑面板
│   │   ├── project_config_panel.py # 项目配置编辑面板
│   └── ...
```

**2. 核心组件设计 (Core Component Design) - 修改与增补**

*   **`main_window.py` (主窗口 - `MainWindow` 类)**:
    *   **布局**:
        *   `QMenuBar`（当前设计中为可选）应设为强制，并包含一个“设置”或“配置”菜单。
        *   此菜单将包含“编辑全局配置”和“编辑项目配置”等操作。
        *   当这些操作被触发时，将打开专用的对话框或切换到特定标签页进行配置编辑。
    *   **功能**:
        *   添加方法来处理打开 `GlobalConfigPanel` 和 `ProjectConfigPanel`（可能在 `QDialog` 实例中进行模态编辑，或者如果偏好非模态编辑，则作为 `QTabWidget` 中的新标签页）。

*   **`utils.py` (GUI辅助工具) - 完善**:
    *   `utils.py` 中现有的 `ConfigManager` 可以增强，或者在 `gui/config_manager.py` 中创建一个新的 `ConfigHandler`，专门管理GUI与后端配置系统（例如 `src/config/global_config_loader.py`、`src/config/project_config_loader.py`、`src/config/manager.py`）之间的交互。
    *   此 `ConfigHandler` 将负责：
        *   加载全局和项目配置。
        *   保存修改后的配置。
        *   提供配置模式（如果后端可用）以动态构建UI表单。

*   **`gui/config_panels/global_config_panel.py` (全局配置编辑面板 - `GlobalConfigPanel` 类)**:
    *   继承自 `QWidget` 或 `QDialog`。
    *   **UI布局**:
        *   利用 `QFormLayout` 展示全局配置参数。
        *   每个配置项将有一个适当的 `QLabel` 和一个输入控件（例如，`QLineEdit` 用于字符串，`QSpinBox` 用于数字，`QCheckBox` 用于布尔值，`QComboBox` 用于枚举，`QFileDialog` 用于文件/目录路径）。
        *   包含“保存”和“取消”按钮。
    *   **功能**:
        *   使用 `ConfigHandler` 加载全局配置数据。
        *   使用当前配置值填充UI控件。
        *   实现用户输入的验证逻辑。
        *   点击“保存”时，收集UI数据，验证，并传递给 `ConfigHandler` 进行持久化。
        *   成功保存后发出信号，通知GUI的其他部分（例如 `MainWindow`）配置已更改。

*   **`gui/config_panels/project_config_panel.py` (项目配置编辑面板 - `ProjectConfigPanel` 类)**:
    *   类似于 `GlobalConfigPanel`，但专门用于项目级配置。
    *   它将与 `ConfigHandler` 交互以加载和保存项目配置。
    *   如果管理多个项目，可能包含一个下拉列表或列表来选择活动项目。

**3. 核心设计思路 (Core Design Ideas) - 增补**

*   **模式驱动UI (可选但推荐)**:
    *   如果后端配置系统（`src/config/schema.py`）为配置提供了模式（例如，JSON Schema），`ConfigPanel` 类可以根据此模式动态生成其表单。这将大大增强可扩展性，并减少配置参数更改时的维护工作。
    *   `ConfigHandler` 将负责获取和解释这些模式。
*   **配置验证**:
    *   在 `ConfigPanel` 中实现健壮的验证，以确保用户输入在保存前是有效的。向用户提供即时反馈。
*   **用户反馈**:
    *   在保存配置后，在状态栏或专用消息框中显示成功或错误消息。
*   **模块化**:
    *   将配置UI逻辑与脚本特定面板分开，以保持清晰的架构。

**4. 实施步骤 (Implementation Steps) - 增补**

1.  **扩展项目结构**: 创建 `gui/config_manager.py` 和 `gui/config_panels/` 目录，其中包含 `global_config_panel.py` 和 `project_config_panel.py`。
2.  **增强 `ConfigManager` / 创建 `ConfigHandler`**: 在 `gui/config_manager.py` 中开发逻辑，以与现有 `src/config` 模块接口，用于加载和保存配置。
3.  **修改 `MainWindow`**: 添加“设置”菜单和打开配置面板的操作。
4.  **实现 `GlobalConfigPanel`**: 使用 `QFormLayout` 设计UI，并实现加载、编辑和保存全局配置的逻辑。
5.  **实现 `ProjectConfigPanel`**: 设计项目配置的UI和逻辑。
6.  **集成验证**: 向配置面板添加输入验证。
7.  **测试**: 彻底测试全局和项目设置的配置加载、编辑、保存和验证。

此扩展设计将配置管理无缝集成到现有PyQt GUI框架中，为管理应用程序设置提供了专用且用户友好的界面。

### 拓展GUI设计：国际化 (i18n) 支持

为了使GUI适应不同语言的用户，同时避免额外安装Qt开发工具，我们将集成Python标准库中的 `gettext` 模块。

**1. 技术选型 (Technology Selection)**

*   **Python `gettext` 模块**: 利用Python内建的国际化支持，包括 `pygettext` 工具和 `gettext.translation`。这将避免对Qt开发工具链（如 `pylupdate5`, `lrelease`, `Qt Linguist`）的依赖。

**2. 项目结构 (Project Structure) - 增补**

```
poetry-annotator/
├── gui/
│   ├── ...
│   ├── locale/                 # 存放国际化文件
│   │   ├── zh_CN/
│   │   │   └── LC_MESSAGES/
│   │   │       └── app.po      # 中文翻译源文件
│   │   │       └── app.mo      # 编译后的中文翻译文件
│   └── ...
```

**3. 核心组件设计 (Core Component Design) - 修改**

*   **所有UI相关的 `.py` 文件** (例如 `main_window.py`, `script_panel_base.py`, `script_panels/*.py`, `config_panels/*.py`):
    *   所有用户可见的硬编码字符串（如窗口标题、按钮文本、标签、菜单项、状态栏消息等）都必须使用 `gettext.gettext()` 或其别名 `_()` 方法进行包装。
    *   **示例**: `self.setWindowTitle("Poetry Annotator GUI")` 应修改为 `self.setWindowTitle(_("Poetry Annotator GUI"))`。
    *   需要在每个使用 `_()` 的文件中导入 `gettext` 并定义 `_ = gettext.gettext`。

*   **`app.py` (应用程序入口)**:
    *   在创建 `QApplication` 实例后，需要设置 `gettext` 的域和路径，并根据用户或配置指定的语言加载对应的 `.mo` 翻译文件。
    *   **示例代码**:
        ```python
        import sys
        import os
        import gettext
        from PyQt5.QtWidgets import QApplication
        from .main_window import MainWindow

        # --- i18n Setup (using gettext) ---
        LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale') # 翻译文件存放目录
        gettext.bindtextdomain('app', LOCALE_DIR) # 绑定翻译域
        gettext.textdomain('app') # 设置当前翻译域
        _ = gettext.gettext # 定义翻译函数别名

        def main():
            app = QApplication(sys.argv)

            # 加载翻译
            lang = 'zh_CN' # 假设从配置或系统获取语言
            try:
                translator = gettext.translation('app', LOCALE_DIR, languages=[lang])
                translator.install() # 安装翻译器，使 _() 函数生效
            except FileNotFoundError:
                print(f"Warning: Translation file for {lang} not found in {LOCALE_DIR}")
                # 如果找不到翻译文件，则回退到默认语言（通常是英文）

            main_window = MainWindow()
            # ...
            main_window.show()
            sys.exit(app.exec_())
        ```

**4. 实施步骤 (Implementation Steps)**

1.  **代码修改**: 遍历所有GUI相关的Python文件，将所有硬编码的字符串用 `_()` 包装起来，并确保 `gettext` 导入和 `_` 函数定义正确。
2.  **提取字符串**: 在项目根目录运行 `pygettext` 命令。例如：`python -m pygettext -o gui/locale/app.po gui/*.py gui/script_panels/*.py gui/config_panels/*.py gui/utils.py gui/main_window.py gui/app.py`。这会扫描指定目录下的所有 `.py` 文件，找到所有 `_()` 包装的字符串，并生成或更新 `app.po` 文件。
3.  **翻译**: 手动编辑 `gui/locale/app.po` 文件，为每个源字符串提供中文翻译。然后将 `app.po` 复制到 `gui/locale/zh_CN/LC_MESSAGES/app.po`。
4.  **编译翻译**: 运行 `msgfmt` 命令将 `.po` 文件编译成应用程序可以读取的二进制 `.mo` 文件。例如：`msgfmt -o gui/locale/zh_CN/LC_MESSAGES/app.mo gui/locale/zh_CN/LC_MESSAGES/app.po`。请注意，`msgfmt` 是 `gettext` 工具集的一部分，可能需要单独安装，但它不是Qt特有的工具。
5.  **加载翻译**: 在 `app.py` 中实现加载 `gettext.translation` 的逻辑，如上所示。
6.  **测试**: 运行应用程序，验证所有UI元素是否已正确翻译成中文。
7.  **语言切换 (可选)**: 在设置菜单中添加一个语言选择功能，允许用户在运行时切换语言。这需要重新加载 `gettext.translation` 并可能需要重新创建UI才能完全生效。
