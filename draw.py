import os
from typing import Any

import aiohttp
from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig


class HelpDrawError(Exception):
    pass


class AstrBotHelpDrawer:
    def __init__(self, config: AstrBotConfig) -> None:
        self.config = config
        self._load_template()

    def _load_template(self) -> None:
        """加载 HTML 模板"""
        template_path = os.path.join(os.path.dirname(__file__), "help_template.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                self.template_html = f.read()
            logger.info("成功加载 HTML 模板")
        except Exception as e:
            logger.error(f"加载 HTML 模板失败: {e}")
            raise

    @staticmethod
    def _parse_single_command_list(
        text_list: str | list[str],
    ) -> list[tuple[str, str | None]]:
        """解析命令文本列表，支持 " : "、" # "、"#"、":" 分隔描述"""
        commands = []
        lines = (
            text_list.strip().splitlines()
            if isinstance(text_list, str)
            else [ln for ln in text_list if ln.strip()]
        )

        for line in lines:
            raw = line
            stripped = line.strip()
            if not stripped or (stripped.startswith("[") and stripped.endswith("]")):
                continue
            # 缩进行视为上一条命令描述的续行
            if raw.startswith(("  ", "\t")) and commands:
                cmd, desc = commands[-1]
                commands[-1] = (cmd, (desc or "") + stripped)
                continue

            parts = None
            for sep in (" : ", " # ", "#", ":"):
                if sep in stripped:
                    parts = stripped.split(sep, 1)
                    break
            if parts and len(parts) == 2:
                cmd = (
                    parts[0][2:].strip()
                    if parts[0].startswith("- ")
                    else parts[0].strip()
                )
                desc = parts[1].strip()
            else:
                cmd = stripped[2:].strip() if stripped.startswith("- ") else stripped
                desc = None
            commands.append((cmd, desc))

        # 只保留描述第一行
        return [(c, (d.splitlines()[0].strip() if d else None)) for c, d in commands]

    def _parse_plugin_commands_sorted_grouped(
        self, plugin_dict: dict[str, Any]
    ) -> list[tuple[str, list[tuple[str, str | None]]]]:
        large_plugins, small_plugins = [], []
        for name, cmds_raw in plugin_dict.items():
            if not cmds_raw:
                continue
            cmds = self._parse_single_command_list(cmds_raw)
            if not cmds:
                continue
            (small_plugins if len(cmds) == 1 else large_plugins).append((name, cmds))

        large_plugins.sort(key=lambda x: len(x[1]), reverse=True)

        grouped_small_plugin = None
        if small_plugins:
            all_small = [c for _, cmds in small_plugins for c in cmds]
            if all_small:
                grouped_small_plugin = ("简易指令", all_small)
                logger.info(f"-> 创建 '简易指令' ({len(all_small)} 条)")

        result = []
        result.extend(large_plugins)
        if grouped_small_plugin:
            result.append(grouped_small_plugin)

        # 追加自定义命令
        custom_list = []
        if getattr(self.config, "custom_cmds", None):
            custom_list = self._parse_single_command_list(self.config.custom_cmds)
            if custom_list:
                result.append(("自定义命令", custom_list))
                logger.info(f"-> 创建 '自定义命令' ({len(custom_list)} 条)")

        return result

    def _build_sections_data(self, plugin_commands_dict: dict[str, Any]) -> list[dict]:
        """将命令字典转换为模板需要的数据结构"""
        sections = self._parse_plugin_commands_sorted_grouped(plugin_commands_dict)

        result = []
        for section_name, cmds in sections:
            commands = []
            for cmd, desc in cmds:
                commands.append({"name": cmd, "desc": desc or ""})
            result.append({"name": section_name, "commands": commands})
        return result

    @staticmethod
    def _get_astrbot_version() -> str:
        """获取 AstrBot 版本号，失败时返回空字符串。"""
        try:
            from astrbot import __version__

            return __version__ or ""
        except (ImportError, AttributeError):
            return ""

    async def draw_help_image_with_t2i(
        self, plugin_commands_dict: dict[str, Any], star_instance
    ) -> bytes:
        """使用 HTML 模板生成帮助图片"""
        if not self.template_html:
            raise HelpDrawError("HTML 模板未加载")

        sections_data = self._build_sections_data(plugin_commands_dict)
        data = {
            "sections": sections_data,
            "version": self._get_astrbot_version(),
            "header_title": getattr(self.config, "header_title", "悠水小筑 · 七七"),
            "footer_text": getattr(
                self.config, "footer_text", "✨ 悠水小筑 | 持续更新中 ✨"
            ),
        }

        logger.info(f"正在使用 T2I 模板生成帮助图片，包含 {len(sections_data)} 个分组")

        image_url = await star_instance.html_render(
            self.template_html,
            data,
            options={
                "full_page": True,
                "type": "png",
                "quality": 90,
                "viewport": {"width": 1080, "height": 1920},
            },
        )

        # 从 URL 下载图片并返回 bytes
        async with aiohttp.ClientSession() as session, session.get(image_url) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                logger.info(f"T2I 图片生成成功，大小: {len(image_data)} bytes")
                return image_data
            raise HelpDrawError(f"下载图片失败，状态码: {resp.status}")
