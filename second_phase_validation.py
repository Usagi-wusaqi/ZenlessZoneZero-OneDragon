#!/usr/bin/env python3
"""
back_to_world 重构第二阶段验证脚本

验证第二阶段迁移的应用和整体重构状态
"""

import os
import sys
import json
from typing import Dict, List, Any

def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(file_path)

def read_file_content(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取失败: {e}"

def check_method_removed(file_path: str, app_name: str) -> Dict[str, Any]:
    """检查应用是否已移除 back_to_world 方法"""
    if not check_file_exists(file_path):
        return {
            'status': 'file_not_found',
            'message': f'文件不存在: {file_path}'
        }

    content = read_file_content(file_path)
    if "读取失败" in content:
        return {
            'status': 'read_error',
            'message': content
        }

    # 检查是否还有 back_to_world 方法定义
    has_method = 'def back_to_world(' in content

    if has_method:
        return {
            'status': 'method_exists',
            'message': f'{app_name} 仍有 bacrld 方法，需要移除'
        }
    else:
        return {
            'status': 'method_removed',
            'message': f'{app_name} 已成功移除 back_to_world 方法'
        }

def check_charge_plan_parameterized(file_path: str) -> Dict[str, Any]:
    """检查 ChargePlanApp 是否已转换为参数化调用"""
    if not check_file_exists(file_path):
        return {
            'status': 'file_not_found',
            'message': f'文件不存在: {file_path}'
        }

    content = read_file_content(file_path)
    if "读取失败" in content:
        return {
            'status': 'read_error',
            'message': content
        }

    # 检查是否有参数化调用
    has_parameterized_call = 'super().back_to_world(' in content and 'self.charge_power' in content
    has_method = 'def back_to_world(' in content

    if has_method and has_parameterized_call:
        return {
            'status': 'parameterized',
            'message': 'ChargePlanApp 已成功转换为参数化调用'
        }
    elif has_method and not has_parameterized_call:
        return {
            'status': 'not_parameterized',
            'message': 'ChargePlanApp 仍有方法但未参数化'
        }
    else:
        return {
            'status': 'method_removed',
            'message': 'ChargePlanApp 方法已移除（可能使用默认实现）'
        }

def check_special_apps_preserved() -> Dict[str, Dict[str, Any]]:
    """检查特殊应用的自定义逻辑是否保留"""
    special_apps = {
        'TransportByCompendium': 'src/zzz_od/operation/compendium/tp_by_compendium.py',
        'LostVoidLottery': 'src/zzz_od/application/hollow_zero/lost_void/lost_void_lottery_app.py',
        'LostVoidRouteChange': 'src/zzz_od/application/hollow_zero/lost_void/lost_void_route_change_app.py'
    }

    results = {}

    for app_name, file_path in special_apps.items():
        if not check_file_exists(file_path):
            results[app_name] = {
                'status': 'file_not_found',
                'message': f'文件不存在: {file_path}'
            }
            continue

        content = read_file_content(file_path)
        if "读取失败" in content:
            results[app_name] = {
                'status': 'read_error',
                'message': content
            }
            continue

        has_method = 'def back_to_world(' in content

        if has_method:
            results[app_name] = {
                'status': 'preserved',
                'message': f'{app_name} 的特殊逻辑已保留'
            }
        else:
            results[app_name] = {
                'status': 'missing',
                'message': f'{app_name} 缺少 back_to_world 方法'
            }

    return results

def check_test_results() -> Dict[str, Any]:
    """检查测试结果文件"""
    test_files = [
        'complete_refactor_test_results.json',
        'refactor_baseline.json'
    ]

    results = {}

    for test_file in test_files:
        if check_file_exists(test_file):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results[test_file] = {
                        'status': 'exists',
                        'size': len(str(data)),
                        'message': f'{test_file} 存在且有效'
                    }
            except Exception as e:
                results[test_file] = {
                    'status': 'invalid',
                    'message': f'{test_file} 存在但无效: {e}'
                }
        else:
            results[test_file] = {
                'status': 'missing',
                'message': f'{test_file} 不存在'
            }

    return results

def main():
    """主验证函数"""
    print("=== back_to_world 重构第二阶段验证 ===\n")

    # 第二阶段迁移的应用
    second_phase_apps = {
        'LifeOnLineApp': 'src/zzz_od/application/life_on_line/life_on_line_app.py',
        'CityFundApp': 'src/zzz_od/application/city_fund/city_fund_app.py',
        'CoffeeApp': 'src/zzz_od/application/coffee/coffee_app.py'
    }

    print("1. 检查第二阶段迁移应用...")
    second_phase_results = {}
    for app_name, file_path in second_phase_apps.items():
        result = check_method_removed(file_path, app_name)
        second_phase_results[app_name] = result

        status_icon = "✓" if result['status'] == 'method_removed' else "✗"
        print(f"   {status_icon} {app_name}: {result['message']}")

    print("\n2. 检查 ChargePlanApp 参数化...")
    charge_plan_result = check_charge_plan_parameterized('src/zzz_od/application/charge_plan/charge_plan_app.py')
    status_icon = "✓" if charge_plan_result['status'] == 'parameterized' else "✗"
    print(f"   {status_icon} ChargePlanApp: {charge_plan_result['message']}")

    print("\n3. 检查特殊应用保留...")
    special_results = check_special_apps_preserved()
    for app_name, result in special_results.items():
        status_icon = "✓" if result['status'] == 'preserved' else "✗"
        print(f"   {status_icon} {app_name}: {result['message']}")

    print("\n4. 检查测试结果文件...")
    test_results = check_test_results()
    for file_name, result in test_results.items():
        status_icon = "✓" if result['status'] == 'exists' else "✗"
        print(f"   {status_icon} {file_name}: {result['message']}")

    # 计算总体状态
    print("\n=== 第二阶段验证总结 ===")

    # 统计结果
    second_phase_success = sum(1 for r in second_phase_results.values() if r['status'] == 'method_removed')
    second_phase_total = len(second_phase_results)

    charge_plan_success = 1 if charge_plan_result['status'] in ['parameterized', 'method_removed'] else 0

    special_success = sum(1 for r in special_results.values() if r['status'] == 'preserved')
    special_total = len(special_results)

    test_success = sum(1 for r in test_results.values() if r['status'] == 'exists')
    test_total = len(test_results)

    print(f"第二阶段迁移: {second_phase_success}/{second_phase_total} 成功")
    print(f"参数化转换: {charge_plan_success}/1 成功")
    print(f"特殊应用保留: {special_success}/{special_total} 成功")
    print(f"测试结果文件: {test_success}/{test_total} 存在")

    # 总体评估
    total_success = second_phase_success + charge_plan_success + special_success + test_success
    total_items = second_phase_total + 1 + special_total + test_total
    success_rate = total_success / total_items if total_items > 0 else 0

    print(f"\n总体成功率: {success_rate:.1%} ({total_success}/{total_items})")

    if success_rate >= 0.8:
        print("✓ 第二阶段验证成功！")
        return 0
    else:
        print("✗ 第二阶段验证存在问题，需要修复。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)