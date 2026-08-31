import collections

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import Image
from astrbot.core.star.filter.command import CommandFilter
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.star_handler import StarHandlerMetadata, star_handlers_registry

from .draw import AstrBotHelpDrawer

PLUGIN_NAME = "astrbot_plugin_fns_help"


@register(
    "fns_help", "FuLingSnow", "返回所有插件指令，可diy展示插件名称与是否显示", "v1.0.2"
)
class FnHelpPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.drawer = AstrBotHelpDrawer(config)
        # 缓存名称映射，避免每次生成帮助都重新解析配置
        self._name_mapping = self._load_name_mapping()

    def _load_name_mapping(self) -> dict[str, str]:
        """加载插件名称映射，仅从配置项 plugin_names 读取。"""
        config_mapping = getattr(self.config, "plugin_names", None)
        if isinstance(config_mapping, dict) and config_mapping:
            return dict(config_mapping)
        if isinstance(config_mapping, list) and config_mapping:
            return self._parse_config_mapping(config_mapping)
        return {}

    @staticmethod
    def _parse_config_mapping(items: list) -> dict[str, str]:
        """将配置项中的 "插件名: 显示名" 列表解析为映射字典。"""
        mapping: dict[str, str] = {}
        for item in items:
            if not isinstance(item, str):
                continue
            stripped = item.strip()
            if not stripped:
                continue
            for sep in (": ", ":"):
                if sep in stripped:
                    key, value = stripped.split(sep, 1)
                    if key.strip():
                        mapping[key.strip()] = value.strip()
                    break
        return mapping

    @filter.command("helps", alias={"帮助", "菜单", "功能"})
    async def get_help(self, event: AstrMessageEvent):
        """获取插件帮助信息"""
        help_msg = self.get_all_commands()
        if not help_msg:
            yield event.plain_result("没有找到任何插件或命令")
            return

        logger.info("尝试使用 T2I 模板生成帮助图片")
        image = await self.drawer.draw_help_image_with_t2i(help_msg, self)
        yield event.chain_result([Image.fromBytes(image)])

    def get_all_commands(self) -> dict[str, list[str]]:
        """获取所有其他插件及其命令列表, 格式为 {plugin_name: [command#desc]}"""
        plugin_commands: dict[str, list[str]] = collections.defaultdict(list)
        try:
            all_stars_metadata = [
                star for star in self.context.get_all_stars() if star.activated
            ]
        except Exception as e:
            logger.error(f"获取插件列表失败: {e}")
            return {}
        if not all_stars_metadata:
            logger.warning("没有找到任何插件")
            return {}

        # 按模块路径预索引所有处理器，避免每个插件全量遍历注册表
        handlers_by_module: dict[str, list[StarHandlerMetadata]] = (
            collections.defaultdict(list)
        )
        for handler in star_handlers_registry:
            if isinstance(handler, StarHandlerMetadata):
                handlers_by_module[handler.handler_module_path].append(handler)

        # 黑名单：支持插件原始名或显示名（别名），忽略首尾空格
        blacklist = {
            item.strip()
            for item in (getattr(self.config, "plugin_blacklist", None) or [])
            if isinstance(item, str)
        }

        for star in all_stars_metadata:
            plugin_name = self._name_mapping.get(star.name, star.name)
            # 黑名单过滤：原始名与显示名任一命中即跳过
            if star.name in blacklist or plugin_name in blacklist:
                logger.info(f"插件 '{star.name}' 在黑名单中，已跳过")
                continue
            plugin_instance = getattr(star, "star_cls", None)
            module_path = getattr(star, "module_path", None)
            if (
                not plugin_name
                or not module_path
                or not isinstance(plugin_instance, Star)
            ):
                logger.warning(
                    f"插件 '{plugin_name}' (模块: {module_path}) 的元数据无效或不完整，已跳过。"
                )
                continue
            # 排除自身
            if plugin_instance is self:
                continue
            seen_commands = set()
            for handler in handlers_by_module.get(module_path, ()):
                command_name: str | None = None
                description = handler.desc
                for filter_ in handler.event_filters:
                    if isinstance(filter_, CommandFilter):
                        command_name = filter_.command_name
                        break
                    elif isinstance(filter_, CommandGroupFilter):
                        command_name = filter_.group_name
                        break
                if command_name:
                    formatted_command = (
                        f"{command_name}#{description}" if description else command_name
                    )
                    # set 去重，避免同一条命令重复出现
                    if formatted_command not in seen_commands:
                        seen_commands.add(formatted_command)
                        plugin_commands[plugin_name].append(formatted_command)
        return dict(plugin_commands)
