import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel
from fastapi import Body
from detect_mix_service_Eth import detect

app = jsonrpc.API()
entrypoint = jsonrpc.Entrypoint('/api')

class MyError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'My error'

    class DataModel(BaseModel):
        details: str

class DetectionResult(BaseModel):
    address_status: str  # 检测状态
    risk_score: float  # 风险评分
@entrypoint.method(errors=[MyError])
def detect_mix_service(
        address: str = Body(
            ...,
            examples=['0x610B717796ad172B316836AC95a2ffad065CeaB4'],
            description='以太坊合约地址，需以0x开头',
            min_length=42,
            max_length=42,
            regex=r'^0x[a-fA-F0-9]{40}$'  # 地址格式校验[1](@ref)
        )
) -> DetectionResult:
    """
    检测以太坊混币服务

    参数：
    - address: 有效的以太坊合约地址

    返回：
    - address_status: 检测状态（safe/risky）
    - risk_score: 风险评分(0-1)
    """
    try:
        risk_score = detect(address)
        address_status = "risky" if risk_score >= 0.5 else "safe"
        return DetectionResult(
            address_status=address_status,
            risk_score=risk_score
        )
    except Exception as e:
        # 异常处理封装
        raise MyError(data={'details': str(e)})

app.bind_entrypoint(entrypoint)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', port=5000)