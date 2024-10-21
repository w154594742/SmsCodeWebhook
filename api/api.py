from ninja import NinjaAPI
from django.core.cache import cache
import time
from .schemas import SendSmsMsgRequest, GetCodeRequest, ResponseSchema
import re
from SmsCodeWebhook.const import (
    code_key,
    CODE_TIMEOUT,
    WAIT_TIME,
    MAX_WAIT_TIME,
    sms_code_pattern
)
api = NinjaAPI()


@api.post("/getCode", response=ResponseSchema)
def get_code(request, request_body: GetCodeRequest):
    start_time = time.time()
     # 将手机号与code_key拼接
    phone_number = request_body.phone_number
    full_code_key = f"{code_key}_{phone_number}"
    while True:
        code = cache.get(full_code_key)
        if code:
            cache.delete(full_code_key)  # 删除已使用的验证码
            return ResponseSchema(err_code=0, message="Success", data={"code": code})

        if time.time() - start_time > MAX_WAIT_TIME:
            return ResponseSchema(err_code=408, message="获取验证码超时")

        time.sleep(WAIT_TIME)


@api.post("/sendSmsMsg", response=ResponseSchema)
def send_sms_msg(request, request_body: SendSmsMsgRequest):
    # 获取手机号和短信内容
    phone_number = request_body.phone_number
    sms_msg = request_body.sms_msg
    # 这里来解析的短信内容
    re_pattern = re.compile(sms_code_pattern)
    match = re_pattern.search(sms_msg)
    if match:
        code = match.group(0)
        # 将手机号与code_key拼接
        full_code_key = f"{code_key}_{phone_number}"
        cache.set(full_code_key, code, timeout=CODE_TIMEOUT)
        return ResponseSchema(err_code=0, message="Set code successfully.")
    return ResponseSchema(err_code=400, message="Set code fail.")