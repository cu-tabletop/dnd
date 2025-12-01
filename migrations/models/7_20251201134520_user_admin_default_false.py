from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "admin" SET DEFAULT False;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "admin" DROP DEFAULT;"""


MODELS_STATE = (
    "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"
    "ivr9yXRgoWSMGWv708/Q9wueKw"
)
