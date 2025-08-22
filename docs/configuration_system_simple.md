# 程序配置说明（简易版）

## 📁 配置文件在哪里？

所有的配置文件都放在 `config` 文件夹里，采用了新的清晰目录结构：

```
config/
├── metadata/
│   └── config_metadata.json          # 配置元数据文件
├── system/
│   ├── active_project.json           # 激活的项目配置
│   └── system_settings.json          # 系统级设置
├── global/
│   └── config.ini                    # 全局配置文件
├── projects/
│   ├── tangshi/
│   │   └── project.ini               # 唐诗项目配置
│   ├── songci/
│   │   └── project.ini               # 宋词项目配置
│   └── default/
│       └── project.ini               # 默认项目配置
├── rules/
│   ├── validation/
│   │   └── global_rules.yaml         # 全局校验规则
│   ├── preprocessing/
│   │   └── global_rules.yaml         # 全局预处理规则
│   └── cleaning/
│       └── global_rules.yaml         # 全局清洗规则
└── templates/
    └── prompt/                       # 提示词模板目录
```

主要的文件有：

- `config/global/config.ini`: 这是**全局设置**文件，里面是一些通用的、默认的配置，对所有项目都有效。
- `config/projects/{project_name}/project.ini`: 这是**项目设置**文件，用来指定当前正在处理的项目（比如唐诗还是宋词）用哪些具体的设置。
- `config/system/active_project.json`: 这个文件用来告诉程序，现在应该使用哪个项目配置。

## ⚙️ 怎么修改配置？

### 1. 修改全局设置 (`config/global/config.ini`)

这个文件里的设置通常是通用的，比如：

- **你的AI模型账号和密码 (API Key)**：程序需要用它来连接到AI模型。
- **数据保存在哪里**：诗词原文、标注结果等数据保存的位置。
- **日志文件**：程序运行时的记录文件保存在哪里。

**操作步骤:**

1. 打开 `config/global` 文件夹。
2. 用记事本（或任何文本编辑器）打开 `config.ini` 文件。
3. 找到你需要修改的部分，比如 `[Model.qwen-max]` 这一段是关于一个叫 `qwen-max` 的AI模型的设置。
4. 修改其中的 `api_key = YOUR_API_KEY`，把 `YOUR_API_KEY` 替换成你从AI服务商那里获得的真正的密钥。
5. 保存文件。

**示例：配置一个阿里云的模型**

```ini
[Model.qwen-plus]
provider = dashscope
model_name = qwen-plus
api_key = sk-xxxxxxxxxxxxxxxxxxxxxxxx # 请替换为你自己的密钥
```

### 2. 选择当前项目 (`config/system/active_project.json`)

如果你有多个项目（比如一个处理唐诗，一个处理宋词），你可以通过修改这个文件来切换。

**操作步骤:**

1. 用记事本打开 `config/system/active_project.json` 文件。
2. 你会看到类似这样的内容：
    ```json
    {
      "active_project": "tangshi/project.ini",
      "available_projects": [
        "default/project.ini",
        "tangshi/project.ini",
        "songci/project.ini"
      ]
    }
    ```
3. 如果你想用宋词项目配置，就把 `"active_project"` 的值 `"tangshi/project.ini"` 改成 `"songci/project.ini"`。
4. 保存文件。

### 3. 修改项目设置 (`config/projects/{project_name}/project.ini`)

项目设置文件用来指定当前项目具体用哪些配置。它会引用全局配置里的名字，或者直接写明路径。

**操作步骤:**

1. 打开 `config/projects/{project_name}` 文件夹（例如 `config/projects/tangshi`）。
2. 用记事本打开 `project.ini` 文件。
3. 你可以在这里指定：
    - **用哪个数据库**：比如指定用存放唐诗的数据库。
    - **用哪个AI模型**：比如指定用 `qwen-max` 和 `gemini-2.5-flash` 这两个模型。
    - **用哪个提示词**：告诉AI如何进行分类的"口令"。
4. 通常你只需要修改 `[Model]` 部分的 `model_names`，来选择你想用的模型。例如：
    ```ini
    [Model]
    model_names = qwen-max,gemini-2.5-flash
    ```
5. 保存文件。

## ✅ 配置优先级

当全局设置和项目设置有冲突时，程序会优先听项目设置的。

**例如：**
- 全局设置里，日志文件保存在 `logs/app.log`。
- 项目设置里，日志文件保存在 `logs/my_project.log`。
- 那么程序运行时，会使用 `logs/my_project.log`。

## 📝 总结

- `config/global/config.ini`: 全局通用设置。
- `config/projects/{project_name}/project.ini`: 当前项目具体设置。
- `config/system/active_project.json`: 选择使用哪个项目设置文件。
- 修改这些文件，就可以让程序按照你的要求工作了。