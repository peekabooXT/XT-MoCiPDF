# XT 阅迹：项目命名规范

本项目采用统一标识，所有新功能、构建和发布均按以下名称执行。

| 用途 | 固定名称 |
| --- | --- |
| 中文产品名 | XT 阅迹 |
| 英文项目名与仓库名 | XT-ReadTrace |
| Windows 程序 | XT阅迹.exe |
| 安装包 | XT-ReadTrace-版本号-Setup-x64.exe |
| 默认安装目录 | D:\tools\codex\XT-ReadTrace |
| 桌面与开始菜单入口 | XT 阅迹 |
| 自动验证环境变量 | READTRACE_VERIFY_DIR |
| 构建临时目录前缀 | readtrace |

中文界面使用完整产品名「XT 阅迹」，仓库、路径与发布文件使用「XT-ReadTrace」。不另造缩写代替产品或项目名称。「XT」作为个人标签保留。

运行时名称由 `src/branding.py` 集中维护。安装脚本和 Windows 资源采用相同名称；修改版本时同步更新 `branding.py`、`src/version_info.txt`、安装脚本和文档。PDF 页眉、批注作者、创建程序信息和示例必须使用当前名称。

Python 模块、函数和变量使用 `snake_case`，类名使用 `PascalCase`，常量和环境变量使用 `UPPER_SNAKE_CASE`。功能名称按行为命名，例如 `annotations.py`、`reading_export.py`、`vocabulary_export.py`，避免把品牌前缀散布到普通函数中。

第三方组件保留真实名称、来源和许可。词本功能称为「云词本导出」，外部产品名称只用于说明格式兼容性，不作为本软件的名称。

发布前检查源代码、文档、程序资源、文件名、PDF 示例、安装路径和仓库标识。打包时排除个人 `data`、`exports`、测试中间文件与 Git 历史目录。备份资料放在独立归档目录，不进入现行发布包。
