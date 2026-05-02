
from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.application.application_config import ApplicationConfig


class WorldPatrolUiDisappearAction(Enum):
    SILENT_FAIL = ConfigItem('静默失败', 'silent_fail')
    RESTART_AND_SKIP = ConfigItem('重开游戏并跳过路线', 'restart_and_skip')
    RESTART_AND_RETRY = ConfigItem('重开游戏并重试路线', 'restart_and_retry')


class WorldPatrolConfig(ApplicationConfig):

    def __init__(self, instance_idx: int, group_id: str):
        ApplicationConfig.__init__(
            self,
            app_id='world_patrol',
            instance_idx=instance_idx,
            group_id=group_id,
        )

    @property
    def auto_battle(self) -> str:
        return self.get('auto_battle', '全配队通用')

    @auto_battle.setter
    def auto_battle(self, new_value: str) -> None:
        self.update('auto_battle', new_value)

    @property
    def route_list(self) -> str:
        return self.get('route_list', '')

    @route_list.setter
    def route_list(self, new_value: str) -> None:
        self.update('route_list', new_value)

    @property
    def ui_disappear_action(self) -> str:
        return self.get('ui_disappear_action', WorldPatrolUiDisappearAction.RESTART_AND_SKIP.value.value)

    @ui_disappear_action.setter
    def ui_disappear_action(self, new_value: str) -> None:
        self.update('ui_disappear_action', new_value)

    @property
    def ui_disappear_seconds(self) -> int:
        return int(self.get('ui_disappear_seconds', 60))

    @ui_disappear_seconds.setter
    def ui_disappear_seconds(self, new_value: int) -> None:
        self.update('ui_disappear_seconds', new_value)

    @property
    def route_retry_times(self) -> int:
        return int(self.get('route_retry_times', 1))

    @route_retry_times.setter
    def route_retry_times(self, new_value: int) -> None:
        self.update('route_retry_times', new_value)
