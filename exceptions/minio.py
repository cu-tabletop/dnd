class BucketsUncreatedError(Exception):
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name

    def __str__(self) -> str:
        return f"Bucket {self.bucket_name} wasn't created."
