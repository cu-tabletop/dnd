from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "invitation" ALTER COLUMN "user_id" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "invitation" ALTER COLUMN "user_id" SET NOT NULL;"""


MODELS_STATE = (
    "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"
)
