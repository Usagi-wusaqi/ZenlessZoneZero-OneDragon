#!/usr/bin/env python3
"""
简单的第一阶段验证测试

验证基类实现和方法签名的正确性
"""

import sys
import os
import inspect

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_base_class():
    """测试基类实现"""
    print("=== 测试基类实现 ===")

    try:
        from zzz_od.application.zzz_application import ZApplication

        # 检查基类是否有 back_to_world 方法
        has_method = hasattr(ZApplication, 'back_to_world')
        print(f"✓ 基类有 back_to_world 方法: {has_method}")

        if has_method:
            # 检查方法签名
            sig = inspect.signature(ZApplication.back_to_world)
            params = list(sig.parameters.keys())
            print(f"✓ 方法参数: {params}")

            # 检查是否支持 custom_status 参数
            has_custom_status = 'custom_status' in params
            print(f"✓ 支持 custom_status 参数: {has_custom_status}")

            return has_method and has_custom_status

        return False

    except Exception as e:
        print(f"✗ 测试基类实现时出错: {e}")
        return False


def test_migrated_apps_signatures():
    """测试已迁移应用的方法签名"""
    print("\n=== 测试已迁移应用的方法签名 ===")

    migrated_apps = [
        ('EmailApp', 'zzz_od.application.email_app.email_app', 'EmailApp'),
        ('ScratchCardApp', 'zzz_od.application.scratch_card.scratch_card_app', 'ScratchCardApp'),
        ('RandomPlayApp', 'zzz_od.application.random_play.random_play_app', 'RandomPlayApp'),
        ('NotoriousHuntApp', 'zzz_od.application.notorious_hunt.notorious_hunt_app', 'NotoriousHuntApp'),
    ]

    results = {}

    for app_name, module_path, class_name in migrated_apps:
        try:
            # 动态导入应用类
            module = __import__(module_path, fromlist=[class_name])
            app_class = getattr(module, class_name)

            # 检查是否有 back_to_world 方法
            has_method = hasattr(app_class, 'back_to_world')

            if has_method:
                # 检查方法签名
                sig = inspect.signature(app_class.back_to_world)
                params = list(sig.parameters.keys())
                has_custom_status = 'custom_status' in params

                # 检查方法源码，看是否调用了 super()
                source = inspect.getsource(app_class.back_to_world)
                calls_super = 'super()' in source

                results[app_name] = {
                    'has_method': has_method,
                    'has_custom_status': has_custom_status,
                    'calls_super': calls_super,
                    'params': params,
                    'success': has_method and has_custom_status and calls_super
                }

                status = "✓" if results[app_name]['success'] else "✗"
                print(f"  {status} {app_name}:")
                print(f"    - 有方法: {has_method}")
                print(f"    - 有 custom_status 参数: {has_custom_status}")
                print(f"    - 调用 super(): {calls_super}")
                print(f"    - 参数: {params}")

            else:
                results[app_name] = {
                    'has_method': False,
                    'success': False
                }
                print(f"  ✗ {app_name}: 没有 back_to_world 方法")

        except Exception as e:
            results[app_name] = {
                'success': False,
                'error': str(e)
            }
            print(f"  ✗ {app_name}: 错误 - {e}")

    return results


def test_remaining_apps():
    """测试仍有重复实现的应用"""
    print("\n=== 测试仍有重复实现的应用 ===")

    remaining_apps = [
        ('LifeOnLineApp', 'zzz_od.application.life_on_line.life_on_line_app', 'LifeOnLineApp'),
        ('CityFundApp', 'zzz_od.application.city_fund.city_fund_app', 'CityFundApp'),
        ('CoffeeApp', 'zzz_od.application.coffee.coffee_app', 'CoffeeApp'),
    ]

    results = {}

    for app_name, module_path, class_name in remaining_apps:
        try:
            # 动态导入应用类
            module = __import__(module_path, fromlist=[class_name])
            app_class = getattr(module, class_name)

            # 检查是否有 back_to_world 方法
            has_method = hasattr(app_class, 'back_to_world')

            if has_method:
                # 检查方法源码，看是否有重复实现
                source = inspect.getsource(app_class.back_to_world)
                has_duplicate_code = 'BackToNormalWorld' in source and 'super()' not in source

                results[app_name] = {
                    'has_method': has_method,
                    'has_duplicate_code': has_duplicate_code,
                    'needs_migration': has_duplicate_code
                }

                status = "⚠" if has_duplicate_code else "✓"
                print(f"  {status} {app_name}:")
                print(f"    - 有方法: {has_method}")
                print(f"    - 有重复代码: {has_duplicate_code}")
                print(f"    - 需要迁移: {has_duplicate_code}")

            else:
                results[app_name] = {
                    'has_method': False,
                    'needs_migration': False
                }
                print(f"  ✓ {app_name}: 没有 back_to_world 方法（将使用基类实现）")

        except Exception as e:
            results[app_name] = {
                'error': str(e)
            }
            print(f"  ✗ {app_name}: 错误 - {e}")

    return results


def main():
    """主函数"""
    print("开始第一阶段验证测试\n")

    # 测试基类实现
    base_class_ok = test_base_class()

    # 测试已迁移应用的方法签名
    migrated_results = test_migrated_apps_signatures()
    migrated_success = sum(1 for r in migrated_results.values() if r.get('success', False))
    migrated_total = len(migrated_results)

    # 测试仍有重复实现的应用
    remaining_results = test_remaining_apps()

    # 总体结果
    print(f"\n=== 第一阶段验证总结 ===")
    print(f"基类实现: {'✓' if base_class_ok else '✗'}")
    print(f"已迁移应用: {migrated_success}/{migrated_total} 正确")

    remaining_needs_migration = sum(1 for r in remaining_results.values() if r.get('needs_migration', False))
    print(f"仍需迁移的应用: {remaining_needs_migration}")

    overall_success = base_class_ok and migrated_success == migrated_total

    if overall_success:
        print("\n🎉 第一阶段验证成功！")
        print("- ✓ 基类 back_to_world 实现正常")
        print("- ✓ 已迁移应用方法签名正确")
        print("- ✓ 已迁移应用正确调用基类方法")

        if remaining_needs_migration > 0:
            print(f"\n📋 下一步: 还有 {remaining_needs_migration} 个应用需要迁移")
        else:
            print("\n🎯 所有应用都已迁移完成！")
    else:
        print("\n❌ 第一阶段验证存在问题！")
        if not base_class_ok:
            print("- ✗ 基类实现有问题")
        if migrated_success < migrated_total:
            print(f"- ✗ {migrated_total - migrated_success} 个已迁移应用有问题")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())