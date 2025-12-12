from typing import Any

from aiogram_dialog import DialogManager

from states.academy_campaigns import AcademyCampaignPreview, AcademyCampaigns

states = {  # Костыль
    "AcademyCampaigns.campaigns": AcademyCampaigns.campaigns,
    "AcademyCampaignPreview.preview": AcademyCampaignPreview.preview,
}


async def redirect(start_data: Any, dialog_manager: DialogManager):
    if isinstance(start_data, dict) and (go_to := start_data.get("redirect_to")):
        if isinstance(go_to, str):
            go_to = states[go_to]

        path = start_data.get("path", [])
        start_data["redirect_to"] = path[0] if path else None
        start_data["path"] = path[1:]
        await dialog_manager.start(state=go_to, data=start_data)
