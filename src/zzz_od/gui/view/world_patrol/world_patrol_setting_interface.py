from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon, PushSettingCard, SpinBox

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils.log_utils import log
from one_dragon_qt.services.app_setting.app_setting_provider import GroupIdMixin
from one_dragon_qt.utils.config_utils import get_prop_adapter
from one_dragon_qt.widgets.combo_box import ComboBox
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.help_card import HelpCard
from one_dragon_qt.widgets.setting_card.multi_push_setting_card import (
    MultiPushSettingCard,
)
from one_dragon_qt.widgets.setting_card.spin_box_setting_card import SpinBoxSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from zzz_od.application.battle_assistant.auto_battle_config import (
    get_auto_battle_op_config_list,
)
from zzz_od.application.world_patrol import world_patrol_const
from zzz_od.application.world_patrol.world_patrol_config import WorldPatrolConfig
from zzz_od.application.world_patrol.world_patrol_run_record import WorldPatrolRunRecord

if TYPE_CHECKING:
    from zzz_od.context.zzz_context import ZContext


class WorldPatrolSettingInterface(VerticalScrollInterface, GroupIdMixin):

    def __init__(self, ctx: ZContext):
        super().__init__(
            content_widget=None,
            object_name="world_patrol_setting_interface",
            nav_text_cn="锄大地配置",
        )

        self.ctx: ZContext = ctx
        self.config: WorldPatrolConfig | None = None
        self.run_record: WorldPatrolRunRecord | None = None

    def get_content_widget(self) -> QWidget:
        widget = QWidget(self)
        col_layout = QHBoxLayout(widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(col_layout)

        # 将左侧和右侧的 widget 添加到主布局中，并均分空间
        col_layout.addWidget(self._get_left_opts(), stretch=1)
        col_layout.addWidget(self._get_right_opts(), stretch=1)

        return widget

    def _get_left_opts(self) -> QWidget:
        # 创建左侧的垂直布局容器
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        self.help_opt = HelpCard(url='',
                                 content='使用此功能前，建议勘域编队中要有一名合适的行走位')
        layout.addWidget(self.help_opt)

        self.auto_battle_opt = ComboBoxSettingCard(icon=FluentIcon.SEARCH, title='自动战斗')
        layout.addWidget(self.auto_battle_opt)

        self.ui_disappear_action_combo = ComboBox()
        self.ui_disappear_action_combo.setMinimumWidth(180)
        self.ui_disappear_action_combo.currentIndexChanged.connect(self._on_ui_disappear_action_changed)

        self.ui_disappear_seconds_spin = SpinBox()
        self.ui_disappear_seconds_spin.setRange(1, 600)
        self.ui_disappear_seconds_spin.setSingleStep(1)
        self.ui_disappear_seconds_spin.setSuffix(' 秒')
        self.ui_disappear_seconds_spin.setMinimumWidth(100)
        self.ui_disappear_seconds_spin.setMaximumWidth(140)
        self.ui_disappear_seconds_spin.valueChanged.connect(self._on_ui_disappear_seconds_changed)

        self.ui_disappear_opt = MultiPushSettingCard(
            icon=FluentIcon.SETTING,
            title='界面消失处理（卡电梯）',
            content='检测到疑似卡电梯时的处理方式和持续时间',
            btn_list=[self.ui_disappear_action_combo, self.ui_disappear_seconds_spin],
        )
        layout.addWidget(self.ui_disappear_opt)

        layout.addStretch(1)
        return widget

    def _get_right_opts(self) -> QWidget:
        # 创建右侧的垂直布局容器
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        self.run_record_opt = PushSettingCard(
            icon=FluentIcon.SYNC,
            title='运行记录',
            text='重置记录'
        )
        self.run_record_opt.clicked.connect(self._on_reset_record_clicked)
        layout.addWidget(self.run_record_opt)

        self.route_list_opt = ComboBoxSettingCard(icon=FluentIcon.SEARCH, title='路线名单')
        layout.addWidget(self.route_list_opt)

        self.route_retry_times_opt = SpinBoxSettingCard(
            icon=FluentIcon.SYNC,
            title='路线重试次数',
            content='普通卡住和卡电梯重试共用；0 表示不重试',
            minimum=0,
            maximum=10,
        )
        layout.addWidget(self.route_retry_times_opt)

        layout.addStretch(1)
        return widget

    def on_interface_shown(self) -> None:
        super().on_interface_shown()

        self.config = self.ctx.run_context.get_config(
            app_id=world_patrol_const.APP_ID,
            instance_idx=self.ctx.current_instance_idx,
            group_id=self.group_id,
        )
        self.run_record = self.ctx.run_context.get_run_record(
            app_id=world_patrol_const.APP_ID,
            instance_idx=self.ctx.current_instance_idx,
        )

        config_list = [
            ConfigItem(i.name)
            for i in self.ctx.world_patrol_service.get_world_patrol_route_lists()
        ]
        self.route_list_opt.set_options_by_list(
            [ConfigItem('全部', value='')]
            +
            config_list
        )
        self.route_list_opt.init_with_adapter(get_prop_adapter(self.config, 'route_list'))

        self.auto_battle_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))
        self.auto_battle_opt.init_with_adapter(get_prop_adapter(self.config, 'auto_battle'))

        self.ui_disappear_action_combo.set_items(
            [
                ConfigItem('静默失败', WorldPatrolConfig.UI_DISAPPEAR_SILENT_FAIL),
                ConfigItem('重开游戏并跳过路线', WorldPatrolConfig.UI_DISAPPEAR_RESTART_SKIP),
                ConfigItem('重开游戏并重试路线', WorldPatrolConfig.UI_DISAPPEAR_RESTART_RETRY),
            ],
            self.config.ui_disappear_action,
        )

        self.ui_disappear_seconds_spin.blockSignals(True)
        self.ui_disappear_seconds_spin.setValue(self.config.ui_disappear_seconds)
        self.ui_disappear_seconds_spin.blockSignals(False)

        self.route_retry_times_opt.init_with_adapter(get_prop_adapter(self.config, 'route_retry_times'))

    def _on_reset_record_clicked(self) -> None:
        if self.run_record is None:
            log.warning('运行记录未初始化')
            return
        self.run_record.reset_record()
        log.info('已重置记录')

    def _on_ui_disappear_action_changed(self, idx: int) -> None:
        if self.config is None:
            return
        self.config.ui_disappear_action = self.ui_disappear_action_combo.itemData(idx)

    def _on_ui_disappear_seconds_changed(self, value: int) -> None:
        if self.config is None:
            return
        self.config.ui_disappear_seconds = value
