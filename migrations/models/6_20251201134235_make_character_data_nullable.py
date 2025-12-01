from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "character" ALTER COLUMN "data" DROP NOT NULL;
        ALTER TABLE "user" ALTER COLUMN "data" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "data" SET NOT NULL;
        ALTER TABLE "character" ALTER COLUMN "data" SET NOT NULL;"""


MODELS_STATE = (
    "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"
    "IZUrD5by/P/wOtYeJg"
)
