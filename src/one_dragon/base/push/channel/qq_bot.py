"""
QQ 官方机器人推送渠道

通过 QQ 开放平台的机器人接口发送单聊（C2C）与群聊消息，不需要部署 OneBot / NapCat 等协议端。
收件方用 openid / group_openid 标识。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time

import requests
from cv2.typing import MatLike

from one_dragon.base.push.push_channel import PushChannel
from one_dragon.base.push.push_channel_config import (
    FieldTypeEnum,
    PushChannelConfigField,
)
from one_dragon.utils.log_utils import log


class QqBot(PushChannel):
    """QQ 官方机器人推送渠道实现类"""

    # 换取 access_token 的地址、机器人消息接口的基础地址
    _TOKEN_URL: str = 'https://bots.qq.com/app/getAppAccessToken'
    _API_BASE_URL: str = 'https://api.sgroup.qq.com'

    _MAX_RETRY: int = 3  # 幂等请求的重试次数，首次之外最多再试 3 次
    _RETRY_DELAY: float = 1.5  # 重试基础间隔（秒），按次数翻倍
    _FILE_TYPE_IMAGE: int = 1  # 富媒体上传的文件类型：图片
    _MD5_10M_SIZE: int = 10002432  # 秒传校验用：文件前 10002432 字节

    # access_token 缓存，避免每次推送都换 token 触发限频；换了 AppID 就重新取
    _last_access_token_info: tuple[str, str, float] = ('', '', 0.0)
    _access_token_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """初始化 QQ 官方机器人推送渠道配置"""
        config_schema = [
            PushChannelConfigField(
                var_suffix="APP_ID",
                title="机器人 AppID",
                icon="APPLICATION",
                field_type=FieldTypeEnum.TEXT,
                placeholder="QQ 开放平台 -> 机器人 -> 开发设置 -> AppID",
                required=True
            ),
            PushChannelConfigField(
                var_suffix="CLIENT_SECRET",
                title="机器人 AppSecret",
                icon="VPN",
                field_type=FieldTypeEnum.TEXT,
                placeholder="QQ 开放平台 -> 机器人 -> 开发设置 -> AppSecret",
                required=True
            ),
            PushChannelConfigField(
                var_suffix="OPENID",
                title="单聊 OpenID",
                icon="PEOPLE",
                field_type=FieldTypeEnum.TEXT,
                placeholder="点上方“绑定单聊”自动填入"
            ),
            PushChannelConfigField(
                var_suffix="GROUP_OPENID",
                title="群聊 GroupOpenID",
                icon="PEOPLE",
                field_type=FieldTypeEnum.TEXT,
                placeholder="点上方“绑定群聊”自动填入"
            )
        ]

        PushChannel.__init__(
            self,
            channel_id='QQ_BOT',
            channel_name='QQ 官方机器人',
            config_schema=config_schema
        )

    @staticmethod
    def _to_int(value: object, default: int) -> int:
        """把接口返回值转成 int（可能是字符串），转换失败时用默认值"""
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return default

    def push(
        self,
        config: dict[str, str],
        title: str,
        content: str,
        image: MatLike | None = None,
        proxy_url: str | None = None,
    ) -> tuple[bool, str]:
        """
        推送消息到 QQ 官方机器人

        Args:
            config: 配置字典，包含 APP_ID、CLIENT_SECRET、OPENID、GROUP_OPENID
            title: 消息标题
            content: 消息内容
            image: 图片数据（可选，走富媒体分片上传）
            proxy_url: 代理地址

        Returns:
            tuple[bool, str]: 是否成功、错误信息
        """
        try:
            return self._send(config, title, content, image, proxy_url)
        except Exception as e:
            log.error('QQ 官方机器人推送异常', exc_info=True)
            return False, f'推送异常：{e}'

    def validate_config(self, config: dict[str, str]) -> tuple[bool, str]:
        """
        验证 QQ 官方机器人配置

        Args:
            config: 配置字典

        Returns:
            tuple[bool, str]: 验证是否通过、错误信息
        """
        app_id = config.get('APP_ID', '').strip()
        client_secret = config.get('CLIENT_SECRET', '').strip()
        openid = config.get('OPENID', '').strip()
        group_openid = config.get('GROUP_OPENID', '').strip()

        if len(app_id) == 0:
            return False, "机器人 AppID 不能为空"

        if len(client_secret) == 0:
            return False, "机器人 AppSecret 不能为空"

        if len(openid) == 0 and len(group_openid) == 0:
            return False, "请先点“绑定单聊”或“绑定群聊”获取接收方 OpenID"

        return True, "配置验证通过"

    def _send(
        self,
        config: dict[str, str],
        title: str,
        content: str,
        image: MatLike | None,
        proxy_url: str | None,
    ) -> tuple[bool, str]:
        """逐个接收目标发送消息，最后附图。单个目标失败不影响其他目标，但有接收方没收到就按失败返回，图片失败只降级为纯文本。"""
        ok, msg = self.validate_config(config)
        if not ok:
            log.error(f"QQ 官方机器人校验失败：{msg}")
            return False, msg

        proxies = self.get_proxy(proxy_url)
        access_token, err = self._get_access_token(
            config.get('APP_ID', '').strip(),
            config.get('CLIENT_SECRET', '').strip(),
            proxies,
        )
        if len(err) > 0:
            log.error(f"QQ 官方机器人{err}")
            return False, err

        targets = self._targets(config)
        ok_count = 0
        errors: list[str] = []
        payload: dict[str, object] = {
            'msg_type': 2,
            'markdown': {'content': self._to_markdown(title, content)},
        }
        for target_name, base_path in targets:
            ok, err = self._send_message(base_path, payload, access_token, proxies)
            if not ok:
                errors.append(f"{target_name}消息发送失败：{err}")
                log.warning(f"QQ 官方机器人{target_name}消息发送失败：{err}")
                continue

            ok_count += 1

            if image is None:
                continue
            ok, err = self._send_image(base_path, image, access_token, proxies)
            if not ok:
                # 文本已经送达，图片失败只记警告，不把整次推送判为失败
                log.warning(f"QQ 官方机器人{target_name}图片发送失败，已降级为纯文本：{err}")

        if len(errors) > 0:
            # 有接收方没收到就按失败返回：只返回成功的话调用方只会提示成功，错误被吞掉
            prefix = f"{ok_count}/{len(targets)} 个接收方推送成功；" if ok_count > 0 else ''
            return False, f"{prefix}{'；'.join(errors)}"

        log.info(f"QQ 官方机器人推送成功，目标数：{ok_count}")
        return True, "推送成功"

    def _targets(self, config: dict[str, str]) -> list[tuple[str, str]]:
        """构造接收目标列表，元素为 (目标名称, 接口路径前缀)。"""
        targets: list[tuple[str, str]] = []
        openid = config.get('OPENID', '').strip()
        group_openid = config.get('GROUP_OPENID', '').strip()

        if len(openid) > 0:
            targets.append(('单聊', f'/v2/users/{openid}'))
        if len(group_openid) > 0:
            targets.append(('群聊', f'/v2/groups/{group_openid}'))
        return targets

    @staticmethod
    def _to_markdown(title: str, content: str) -> str:
        """标题渲染成二级标题、正文另起一段；没有标题时只发正文"""
        if len(title.strip()) == 0:
            return content
        return f'## {title}\n\n{content}'

    def _get_access_token(
        self,
        app_id: str,
        client_secret: str,
        proxies: dict[str, str | None],
    ) -> tuple[str, str]:
        """换取 access_token，按 AppID 缓存，提前 60 秒视为过期"""
        with self._access_token_lock:
            cached_app_id, cached_token, expires_at = self._last_access_token_info
            if cached_app_id == app_id and len(cached_token) > 0 and expires_at > time.time():
                return cached_token, ''

            data, err = self._post(
                self._TOKEN_URL,
                {'appId': app_id, 'clientSecret': client_secret},
                proxies,
                retries=self._MAX_RETRY,
            )
            if data is None:
                return '', f"获取 access_token 失败：{err}"

            access_token = str(data.get('access_token') or '')
            if len(access_token) == 0:
                return '', f"获取 access_token 失败：{data}"

            # 解析失败按 60 秒处理，避免把异常响应缓存两小时
            expires_in = self._to_int(data.get('expires_in'), 60)
            self._last_access_token_info = (app_id, access_token, time.time() + max(expires_in - 60, 30))
            return access_token, ''

    def _send_message(
        self,
        base_path: str,
        payload: dict[str, object],
        access_token: str,
        proxies: dict[str, str | None],
    ) -> tuple[bool, str]:
        """发消息到目标的 /messages 接口。发消息非幂等，重试会让用户收到重复通知，只尝试一次。"""
        data, err = self._post(
            f"{self._API_BASE_URL}{base_path}/messages",
            payload,
            proxies,
            access_token=access_token,
            timeout=20,
        )
        return data is not None, err

    def _send_image(
        self,
        base_path: str,
        image: MatLike,
        access_token: str,
        proxies: dict[str, str | None],
    ) -> tuple[bool, str]:
        """发送图片消息（msg_type=7）：先分片上传换 file_info，再发富媒体消息"""
        image_io = self.image_to_bytes(image)
        if image_io is None:
            return False, '图片转换失败'

        file_info, err = self._upload_image(base_path, image_io.getvalue(), access_token, proxies)
        if len(err) > 0:
            return False, err

        ok, err = self._send_message(
            base_path,
            {'msg_type': 7, 'media': {'file_info': file_info}},
            access_token,
            proxies,
        )
        return ok, err

    def _upload_image(
        self,
        base_path: str,
        image_bytes: bytes,
        access_token: str,
        proxies: dict[str, str | None],
    ) -> tuple[str, str]:
        """
        分片上传图片换 file_info：upload_prepare 拿分片地址 -> 逐片 PUT -> upload_part_finish -> files 合并。
        单聊与群聊的上传接口不互通，必须走对应目标的路径。上传幂等，各步都可重试。
        """
        file_name = 'screenshot.jpg'
        prepared, err = self._post(
            f"{self._API_BASE_URL}{base_path}/upload_prepare",
            {
                'file_type': self._FILE_TYPE_IMAGE,
                'file_size': str(len(image_bytes)),
                'file_name': file_name,
                'md5': hashlib.md5(image_bytes).hexdigest(),
                'sha1': hashlib.sha1(image_bytes).hexdigest(),
                'md5_10m': hashlib.md5(image_bytes[: self._MD5_10M_SIZE]).hexdigest(),
            },
            proxies,
            access_token=access_token,
            retries=self._MAX_RETRY,
            timeout=20,
        )
        if prepared is None:
            return '', f'上传准备失败：{err}'

        upload_id = str(prepared.get('upload_id') or '')
        parts = prepared.get('parts')
        if len(upload_id) == 0 or not isinstance(parts, list):
            return '', f'上传准备返回不完整：{prepared}'

        default_block_size = self._to_int(prepared.get('block_size'), 0)
        offset = 0
        for part in parts:
            if not isinstance(part, dict):
                continue

            block_size = self._to_int(part.get('block_size'), default_block_size)
            chunk = image_bytes[offset: offset + block_size] if block_size > 0 else image_bytes[offset:]
            if len(chunk) == 0:
                break

            presigned_url = str(part.get('presigned_url') or '')
            if len(presigned_url) == 0:
                return '', '上传准备未返回分片地址'

            ok, err = self._put_chunk(presigned_url, chunk, proxies)
            if not ok:
                return '', err

            _, err = self._post(
                f"{self._API_BASE_URL}{base_path}/upload_part_finish",
                {
                    'upload_id': upload_id,
                    'part_index': part.get('index'),
                    'block_size': str(len(chunk)),
                    'md5': hashlib.md5(chunk).hexdigest(),
                },
                proxies,
                access_token=access_token,
                retries=self._MAX_RETRY,
                timeout=20,
            )
            if len(err) > 0:
                return '', f'分片确认失败：{err}'
            offset += len(chunk)

        # 合并分片，取回 file_info
        merged, err = self._post(
            f"{self._API_BASE_URL}{base_path}/files",
            {
                'file_type': self._FILE_TYPE_IMAGE,
                'upload_id': upload_id,
            },
            proxies,
            access_token=access_token,
            retries=self._MAX_RETRY,
            timeout=20,
        )
        if merged is None:
            return '', f'分片合并失败：{err}'

        file_info = str(merged.get('file_info') or '')
        if len(file_info) == 0:
            return '', f'分片合并未返回 file_info：{merged}'
        return file_info, ''

    def _put_chunk(
        self,
        presigned_url: str,
        chunk: bytes,
        proxies: dict[str, str | None],
    ) -> tuple[bool, str]:
        """通过预签名地址 PUT 上传单个分片，网络异常与 400/429/5xx 重试"""
        err = ''
        for attempt in range(self._MAX_RETRY + 1):
            try:
                response = requests.put(
                    presigned_url,
                    data=chunk,
                    headers={'Content-Type': 'application/octet-stream'},
                    proxies=proxies,
                    timeout=60,
                )
            except requests.RequestException as e:
                err = f'分片上传请求异常：{e}'
            else:
                if response.status_code < 300:
                    return True, ''
                detail = (response.text or '').strip() or f"HTTP {response.status_code}"
                err = f'分片上传失败（HTTP {response.status_code}）：{detail}'
                if response.status_code < 500 and response.status_code not in (400, 429):
                    return False, err

            if attempt < self._MAX_RETRY:
                delay = self._RETRY_DELAY * (2 ** attempt)
                log.warning(f'QQ 官方机器人{err}，{delay:.1f} 秒后重试')
                time.sleep(delay)

        return False, err

    def _post(
        self,
        url: str,
        payload: dict[str, object],
        proxies: dict[str, str | None],
        access_token: str | None = None,
        retries: int = 0,
        timeout: int = 15,
    ) -> tuple[dict[str, object] | None, str]:
        """
        POST JSON，返回 (响应体, 错误信息)。

        retries > 0 只给幂等请求（换 token、分片上传）用；发消息非幂等，保持默认的不重试。
        只有没拿到响应（网络异常）和服务端临时故障才重试，业务错误重试也没用。
        """
        headers = {'Content-Type': 'application/json'}
        if access_token is not None:
            headers['Authorization'] = f'QQBot {access_token}'

        err = ''
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=timeout)
            except requests.RequestException as e:
                err = f'请求异常：{e}'
            else:
                detail = (response.text or '').strip() or f"HTTP {response.status_code}"
                if response.status_code < 400:
                    try:
                        data = json.loads(detail)
                    except ValueError:
                        return None, f'响应不是 JSON 对象：{detail}'
                    if not isinstance(data, dict):
                        return None, f'响应不是 JSON 对象：{detail}'
                    # 业务错误也会随 HTTP 200 返回
                    if not data.get('code'):
                        return data, ''
                    return None, f"接口返回错误码 {data.get('code')}：{data.get('message') or detail}"

                err = f'请求失败（HTTP {response.status_code}）：{detail}'
                # 400 可能携带可重试的业务码（如分片未就绪），按可重试处理
                if response.status_code < 500 and response.status_code not in (400, 429):
                    return None, err

            if attempt < retries:
                delay = self._RETRY_DELAY * (2 ** attempt)
                log.warning(f'QQ 官方机器人{err}，{delay:.1f} 秒后重试')
                time.sleep(delay)

        return None, err
