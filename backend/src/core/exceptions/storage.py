class StorageError(Exception):
    pass


class UnsupportedFileTypeError(StorageError):
    pass


class EmptyFileError(StorageError):
    pass


class FileTooLargeError(StorageError):
    pass


class StorageUploadError(StorageError):
    pass