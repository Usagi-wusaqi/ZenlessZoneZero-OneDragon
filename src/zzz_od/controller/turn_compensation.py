from one_dragon.utils import cal_utils
from zzz_od.controller.zzz_pc_controller import ZPcController


class AngleTurnCompensator:
    """运行期角度转向补偿会话，不写回配置。"""

    _ANGLE_EPSILON: float = 1e-6
    _MIN_SCALE: float = 0.5
    _MAX_SCALE: float = 2.0
    _MAX_SCALE_CHANGE: float = 0.2
    _MIN_UNFOLD_ANGLE: float = 30

    def __init__(self, controller: ZPcController) -> None:
        """创建一份独立的运行期补偿会话。"""
        self.controller: ZPcController = controller
        self.scale: float = 1.0

    def reset(self) -> None:
        """清空补偿比例。"""
        self.scale = 1.0

    def learn(self, source_angle: float, effective_angle_diff: float, current_angle: float) -> None:
        """用转向前后的朝向变化更新运行期补偿比例。"""
        if abs(effective_angle_diff) <= self._ANGLE_EPSILON:
            return

        # 用实际朝向变化反推 scale；转少放大，转多缩小
        observed_angle_change = self._observed_angle_change(
            source_angle,
            effective_angle_diff,
            current_angle,
        )
        if abs(observed_angle_change) <= self._ANGLE_EPSILON or observed_angle_change * effective_angle_diff <= 0:
            return

        scale_change = effective_angle_diff / observed_angle_change - self.scale
        clipped_change = max(-self._MAX_SCALE_CHANGE, min(scale_change, self._MAX_SCALE_CHANGE))
        self.scale = max(self._MIN_SCALE, min(self.scale + clipped_change, self._MAX_SCALE))

    def turn(self, angle_diff: float) -> float:
        """按当前补偿比例下发转向，返回实际下发角度。"""
        effective_angle_diff = angle_diff * self.scale
        self.controller.turn_by_angle_diff(effective_angle_diff)
        return effective_angle_diff

    def _observed_angle_change(
        self,
        source_angle: float,
        effective_angle_diff: float,
        current_angle: float,
    ) -> float:
        """计算实际朝向变化，必要时展开跨 180 度的最短角。"""
        observed_angle_change = cal_utils.angle_delta(source_angle, current_angle)
        if observed_angle_change * effective_angle_diff >= 0:
            return observed_angle_change

        # 大角度过冲跨过 180 度后，最短角度会看起来反向；按指令方向展开一次再学习
        # 小角度反向更可能是识别抖动或真实反向转动，不展开
        if abs(effective_angle_diff) < self._MIN_UNFOLD_ANGLE:
            return observed_angle_change
        if effective_angle_diff > 0:
            return observed_angle_change + 360
        return observed_angle_change - 360
