VERIFY_TIME = 60
MSG_PUBLIC = """您好，我发现此群组为公开群组，您需要联系创建者打开 `管理员批准后才能入群` 功能，我才能更好地工作。"""
MSG_SUCCESS = """验证成功，您已经成为群组的一员了！

The verification was successful, and you are now a member of the group!
"""
MSG_FAILURE = """验证失败，请重试。

Verification failed; please try again.
"""
MSG = f"""您好 %s ，当前群组开启了验证功能。

您需要在 {VERIFY_TIME} 秒内发送任意一个 贴纸 来完成验证。

Hello, %s . The group's verification is presently enabled.

You must transmit any sticker within {VERIFY_TIME} seconds to complete the verification.
"""
ADMIN_MSG = """管理员邀请，自动放行。

Administrator's invitation for automatic release.
"""
RE_MSG = f"""您好 %s ，您被管理员要求重新验证。

您需要在 {VERIFY_TIME} 秒内发送任意一个 贴纸 来完成验证。

Hello, %s . The administrator has requested you to re-verify.

You must transmit any sticker within {VERIFY_TIME} seconds to complete the verification.
"""
