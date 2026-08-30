# 有哪些命令呢（astrbot_plugin_fns_help）

<div align="center">

基于 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的帮助图插件

自动扫描所有插件指令，一键生成美观的帮助图片

</div>

<div align="center">

![AstrBot](https://img.shields.io/badge/AstrBot-v4.x-blue)
![Version](https://img.shields.io/badge/version-v1.0.0-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0-red)

</div>

## 目录

- [简介](#简介)
- [修改声明](#修改声明)
- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装](#安装)
- [使用](#使用)
- [配置](#配置)
- [目录结构](#目录结构)
- [注意事项](#注意事项)
- [开源许可](#开源许可)

## 简介

发送 `/helps`（或「帮助」「菜单」「功能」）即可获得一张帮助图片，展示所有已激活插件的全部命令，支持 DIY 插件显示名称与是否显示。

## ⚠️ 修改声明

本插件基于 [tinkerbellqwq/astrbot_plugin_help](https://github.com/tinkerbellqwq/astrbot_plugin_help) 修改而来，自 v1.0.0 起**独立维护**，与原项目无依赖关系。

## 功能特性

- 自动扫描所有已激活插件及其命令，一键生成帮助图片
- 卡片式响应式布局，自动按「指令」分组
- 支持 `plugin_names` 自定义插件在帮助图中的**显示名称**
- 支持 `plugin_blacklist` 隐藏指定插件（支持原始名或显示名，大小写敏感）
- 支持 `custom_cmds` 补充正则 / 监听器命令等无法自动检测的命令
- 顶部标题、底部文本均可自定义

## 环境要求

- AstrBot v4.x 及以上
- Python 3.10+

## 安装

### 方式一：通过 AstrBot 插件商店

AstrBot 管理面板 → 插件管理 → 插件商店，搜索 **有哪些命令呢** 并安装。

### 方式二：通过 Git 地址安装

AstrBot 管理面板 → 插件管理 → 通过 Git 地址安装：

```
https://github.com/FuLingSnow/astrbot_plugin_fns_help.git
```

### 方式三：手动安装

将本项目克隆 / 下载到 AstrBot 的 `data/plugins/` 目录下，重启 AstrBot 即可。

## 使用

发送以下任一指令即可获取帮助图片：

```
/helps
帮助
菜单
功能
```

## 配置

在 AstrBot 管理面板 → 本插件「配置」中修改：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `header_title` | string | `悠水小筑 · 七七` | 帮助图片顶部标题 |
| `footer_text` | string | `✨ 悠水小筑 \| 持续更新中 ✨` | 帮助图片底部文本 |
| `plugin_names` | list | `["builtin_commands: 内置指令"]` | 插件名 → 显示名映射，格式 `插件名: 显示名` |
| `custom_cmds` | list | `[]` | 补充无法自动检测的命令，格式 `命令: 描述`（多个用英文逗号或 `#` 分隔） |
| `plugin_blacklist` | list | `[]` | 黑名单插件列表（原始名或显示名，区分大小写），不显示帮助 |

### 配置示例

```json
{
    "header_title": "悠水小筑 · 七七",
    "footer_text": "✨ 悠水小筑 | 持续更新中 ✨",
    "plugin_names": ["builtin_commands: 内置指令"],
    "custom_cmds": [],
    "plugin_blacklist": []
}
```

## 目录结构

```
astrbot_plugin_fns_help/
├── main.py              # 插件主逻辑（扫描命令、生成帮助）
├── draw.py              # 帮助图片渲染（HTML 模板 + T2I）
├── help_template.html   # 帮助图 HTML 模板
├── metadata.yaml        # 插件元数据（名称、版本、作者、仓库地址）
├── _conf_schema.json    # 配置项 Schema（插件配置面板定义）
├── requirements.txt     # 依赖清单
└── README.md            # 本文档
```

## 注意事项

- 仅显示**已激活**插件的命令，未激活插件不会出现在帮助图中
- 正则 / 监听器命令无法自动检测，请通过 `custom_cmds` 手动补充
- 修改配置保存后 AstrBot 会自动重载插件并应用新参数
- 帮助图片通过 AstrBot 的 T2I 服务渲染

## 开源许可

本项目基于 [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE) 协议开源。

作者：[FuLingSnow](https://github.com/FuLingSnow) · 欢迎提交 [Issue](https://github.com/FuLingSnow/astrbot_plugin_fns_help/issues) 与 PR
