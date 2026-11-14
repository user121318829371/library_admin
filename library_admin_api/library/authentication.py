from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """支持 `Authorization: Bearer <token>` 的 Token 认证（DRF 默认关键字为 Token）"""

    keyword = 'Bearer'
