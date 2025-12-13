#!/usr/bin/env python3
"""
第一阶段验证测试

验证已迁移应用的 back_to_world 功能正常工作
"""

import sys
import os
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from one_dragon.base.operation.operation_round_result import OperationRoundResult, OperationRoundResultEnum
from one_dragon.base.operation.operation_base import OperationResult


class MockZContext:
    """模拟的 ZContext"""
    def __init__(self):
        self.controller = Mock()
        self.screen_loader = Mock()
        self.ocr = Mock()
        self.world_patrol_service = Mock()
        self.compendium_service = Mock()
        self.lost_void = Mock()
        self.logger = Mock()
        self.run_context = Mock()
        self.unlisten_all_event = Mock()
        self.listen_event = Mock()
        self.dispatch_event = Mock()

        # 添加应用可能需要的其他属性
        self.current_instance_idx = 0
        self.instance_count = 1
        self.project_config = Mock()
        self.env_config = Mock()
        self.game_config = Mock()


def test_migrated_applications():
    """测试已迁移的应用"""
    print("=== 第一阶段验证：测试已迁移应用的 back_to_world 功能 ===\n")

    # 创建模拟上下文
    mock_ctx = MockZContext()

    # 测试已迁移的应用
    migrated_apps = [
        ('EmailApp', 'zzz_od.application.email_app.email_app', 'EmailApp'),
        ('ScratchCardApp', 'zzz_od.application.scratch_card.scratch_card_app', 'ScratchCardApp'),
        ('RandomPlayApp', 'zzz_od.application.random_play.random_play_app', 'RandomPlayApp'),
        ('NotoriousHuntApp', 'zzz_od.application.notorious_hunt.notorious_hunt_app', 'NotoriousHuntApp'),
    ]

    results = {}

    for app_name, module_path, class_name in migrated_apps:
        print(f"测试 {app_name}...")

        try:
            # 动态导入应用类
            module = __import__(module_path, fromlist=[class_name])
            app_class = getattr(module, class_name)

            # 创建应用实例
            app = app_class(mock_ctx)

            # 模拟 BackToNormalWorld 操作
            with patch('zzz_od.operation.back_to_normal_world.BackToNormalWorld') as mock_class:
                mock_instance = Mock()
                mock_result = OperationResult(success=True, status="返回大世界成功")
                mock_instance.execute.return_value = mock_result
                mock_class.return_value = mock_instance

                # 测试默认调用
                result1 = app.back_to_world()

                # 测试带自定义状态的调用
                result2 = app.back_to_world(custom_status="测试状态")

                # 验证结果
                success1 = result1.is_success
                success2 = result2.is_success
                status2 = result2.status

                results[app_name] = {
                    'success': success1 and success2,
                    'default_call': success1,
                    'custom_status_call': success2,
                    'custom_status_correct': status2 == "测试状态",
                    'error': None
                }

                status = "✓" if results[app_name]['success'] else "✗"
                print(f"  {status} {app_name}: 默认调用={success1}, 自定义状态调用={success2}, 状态正确={status2 == '测试状态'}")

        except Exception as e:
            results[app_name] = {
                'success': False,
                'error': str(e)
            }
            print(f"  ✗ {app_name}: 错误 - {e}")

    # 汇总结果
    print(f"\n=== 第一阶段验证结果 ===")
    total_apps = len(migrated_apps)
    successful_apps = sum(1 for r in results.values() if r['success'])

    print(f"已测试应用: {total_apps}")
    print(f"成功应用: {successful_apps}")
    print(f"成功率: {successful_apps/total_apps:.1%}")

    if successful_apps == total_apps:
        print("\n✓ 第一阶段验证通过！所有已迁移应用的 back_to_world 功能正常。")
        return True
    else:
        print(f"\n✗ 第一阶段验证部分失败。{total_apps - successful_apps} 个应用存在问题。")
        return False


def test_base_class_implementation():
    """测试基类实现"""
    print("\n=== 测试基类实现 ===")

    try:
        from zzz_od.application.zzz_application import ZApplication

        # 检查基类是否有 back_to_world 方法
        has_method = hasattr(ZApplication, 'back_to_world')
        print(f"基类有 back_to_world 方法: {has_method}")

        if has_method:
            # 检查方法签名
            import inspect
            sig = inspect.signature(ZApplication.back_to_world)
            params = list(sig.parameters.keys())
            print(f"方法参数: {params}")

            # 检查是否支持 custom_status 参数
            has_custom_status = 'custom_status' in params
            print(f"支持 custom_status 参数: {has_custom_status}")

            return has_method and has_custom_status

        return False

    except Exception as e:
        print(f"测试基类实现时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始第一阶段验证测试\n")

    # 测试基类实现
    base_class_ok = test_base_class_implementation()

    # 测试已迁移的应用
    migrated_apps_ok = test_migrated_applications()

    # 总体结果
    overall_success = base_class_ok and migrated_apps_ok

    print(f"\n=== 总体验证结果 ===")
    print(f"基类实现: {'✓' if base_class_ok else '✗'}")
    print(f"已迁移应用: {'✓' if migrated_apps_ok else '✗'}")
    print(f"总体状态: {'✓ 通过' if overall_success else '✗ 失败'}")

    if overall_success:
        print("\n🎉 第一阶段验证成功！")
        print("- 基类 back_to_world 实现正常")
        print("- 已迁移应用功能正常")
        print("- 可以继续进行第二阶段迁移")
    else:
        print("\n❌ 第一阶段验证失败！")
        print("请修复问题后重新验证。")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())