from db.models.base import CharacterData


async def update_char_data(holder: CharacterData, data):
    # TODO: add validation
    holder.data = data
    await holder.save()
