class BasePaymentException(Exception):
    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Payment operation failed"
        super().__init__(message)


class PaymentProviderUnavailable(BasePaymentException):
    pass


class PaymentDeclined(BasePaymentException):
    pass


class PaymentMissingExternalId(BasePaymentException):
    pass


class PaymentNotFound(BasePaymentException):
    pass


class RefundFailed(BasePaymentException):
    pass


class InvalidPaymentWebhook(BasePaymentException):
    pass


class OrderNotPayable(BasePaymentException):
    pass
