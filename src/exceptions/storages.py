class BaseS3Error(Exception):
    """Base class for all S3-related errors."""

    def __init__(self, message: str) -> None:
        if message is None:
            message = "An S3 storage error occurred."
        super().__init__(message)


class S3ConnectionError(BaseS3Error):
    """Raised when there is an issue connecting to the S3 storage."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "Failed to connect to S3 storage."
        super().__init__(message)


class S3BucketNotFoundError(BaseS3Error):
    """Raised when the specified bucket does not exist."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "S3 bucket not found."
        super().__init__(message)


class S3FileUploadError(BaseS3Error):
    """Raised when a file upload operation fails."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "Failed to upload file to S3."
        super().__init__(message)


class S3FileNotFoundError(BaseS3Error):
    """Raised when the requested file is not found in S3 storage."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "Requested file not found in S3."
        super().__init__(message)


class S3PermissionError(BaseS3Error):
    """Raised when the client lacks permission to access a resource."""

    def __init__(self, message: str) -> None:
        if not message:
            message = "Insufficient permissions to access S3 resource."
        super().__init__(message)
