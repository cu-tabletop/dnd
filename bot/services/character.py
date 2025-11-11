from typing import Dict, List

from pydantic import BaseModel, Field


class CharacterStat(BaseModel):
    score: int = 0
    modifier: int = 0


class CharacterHP(BaseModel):
    current: int = 0
    max: int = 0
    temp: int = 0
    ac: int = 0
    speed: int = 0


class CharacterWeapon(BaseModel):
    name: str = "Неизвестно"
    mod: str = ""
    damage: str = ""
    notes: str = ""


class CharacterCoins(BaseModel):
    pp: int = 0
    gp: int = 0
    ep: int = 0
    sp: int = 0
    cp: int = 0


class CharacterData(BaseModel):
    name: str = "Неизвестно"
    klass: str = Field(default="Неизвестно", alias="class")
    subclass: str = ""
    level: int = 0
    race: str = "Неизвестно"
    background: str = "Неизвестно"
    alignment: str = "Неизвестно"
    avatar_link: str | None

    age: str = ""
    height: str = ""
    weight: str = ""
    eyes: str = ""
    skin: str = ""
    hair: str = ""

    proficiency: int = 0
    stats: Dict[str, CharacterStat] = Field(default_factory=dict)

    skills: Dict[str, Dict] = Field(default_factory=dict)
    prof_skills: List[str] = Field(default_factory=list)

    hp: CharacterHP = Field(default_factory=CharacterHP)

    weapons: List[CharacterWeapon] = Field(default_factory=list)

    traits: str = ""
    equipment: str = ""
    background_story: str = ""
    personality: str = ""
    appearance: str = ""
    allies: str = ""
    proficiencies: str = ""

    coins: CharacterCoins = Field(default_factory=CharacterCoins)

    class Config:
        validate_by_name = True


def parse_character_data(data: dict) -> CharacterData:
    """
    Превращает json персонажа Long Story Short в адекватный Pydantic объект
    """
    basic_info = data.get("info", {})
    sub_info = data.get("subInfo", {})
    vitality = data.get("vitality", {})
    coins_data = data.get("coins", {})
    prof_skills = []
    for skill_name, skill_data in data.get("skills", {}).items():
        if skill_data.get("isProf"):
            prof_skills.append(skill_name)
    stats = {}
    for stat_name, stat_data in data.get("stats", {}).items():
        stats[stat_name] = CharacterStat(
            score=stat_data.get("score", 0),
            modifier=stat_data.get("modifier", 0),
        )
    weapons = []
    for weapon in data.get("weaponsList", []):
        weapons.append(
            CharacterWeapon(
                name=weapon.get("name", {}).get("value", "Неизвестно"),
                mod=weapon.get("mod", {}).get("value", ""),
                damage=weapon.get("dmg", {}).get("value", ""),
                notes=weapon.get("notes", {}).get("value", ""),
            )
        )

    # noinspection PyArgumentList
    return CharacterData(
        # Basic info
        name=data.get("name", {}).get("value", "Неизвестно"),
        klass=basic_info.get("charClass", {}).get("value", "Неизвестно"),
        subclass=basic_info.get("charSubclass", {}).get("value", ""),
        level=basic_info.get("level", {}).get("value", 0),
        race=basic_info.get("race", {}).get("value", "Неизвестно"),
        background=basic_info.get("background", {}).get("value", "Неизвестно"),
        alignment=basic_info.get("alignment", {}).get("value", "Неизвестно"),
        avatar_link=basic_info.get("avatar", {}).get("webp")
        or basic_info.get("avatar", {}).get("jpeg"),
        # Physical characteristics
        age=sub_info.get("age", {}).get("value", ""),
        height=sub_info.get("height", {}).get("value", ""),
        weight=sub_info.get("weight", {}).get("value", ""),
        eyes=sub_info.get("eyes", {}).get("value", ""),
        skin=sub_info.get("skin", {}).get("value", ""),
        hair=sub_info.get("hair", {}).get("value", ""),
        # Stats
        proficiency=data.get("proficiency", 0),
        stats=stats,
        # Skills
        skills=data.get("skills", {}),
        prof_skills=prof_skills,
        # Vitality
        hp=CharacterHP(
            current=vitality.get("hp-current", {}).get("value", 0),
            max=vitality.get("hp-max", {}).get("value", 0),
            temp=vitality.get("hp-temp", {}).get("value", 0),
            ac=vitality.get("ac", {}).get("value", 0),
            speed=vitality.get("speed", {}).get("value", 0),
        ),
        # Weapons
        weapons=weapons,
        # Text content
        traits=extract_telegram_text(
            data.get("text", {}).get("traits", {}).get("value", {})
        ),
        equipment=extract_telegram_text(
            data.get("equipment", {}).get("value", {})
        ),
        background_story=extract_telegram_text(
            data.get("quests", {}).get("value", {})
        ),
        personality=extract_telegram_text(
            data.get("background", {}).get("value", {})
        ),
        appearance=extract_telegram_text(
            data.get("appearance", {}).get("value", {})
        ),
        allies=extract_telegram_text(data.get("allies", {}).get("value", {})),
        proficiencies=extract_telegram_text(
            data.get("prof", {}).get("value", {})
        ),
        # Currency
        coins=CharacterCoins(
            pp=coins_data.get("pp", {}).get("value", 0),
            gp=coins_data.get("gp", {}).get("value", 0),
            ep=coins_data.get("ep", {}).get("value", 0),
            sp=coins_data.get("sp", {}).get("value", 0),
            cp=coins_data.get("cp", {}).get("value", 0),
        ),
    )


def extract_telegram_text(text_data):
    """
    Превращает json документооборот в HTML
    """
    if not text_data:
        return ""

    content = text_data.get("data", {}).get("content", [])
    result = []

    for block in content:
        if block.get("type") == "paragraph" and "content" in block:
            paragraph_text = ""
            for content_item in block["content"]:
                if content_item.get("type") == "text":
                    text = content_item.get("text", "").strip()
                    if text:
                        marks = content_item.get("marks", [])
                        for mark in marks:
                            if mark.get("type") == "bold":
                                text = f"<b>{text}</b>"
                            elif mark.get("type") == "italic":
                                text = f"<i>{text}</i>"
                            elif mark.get("type") == "underline":
                                text = f"<u>{text}</u>"
                        paragraph_text += text + " "
                elif content_item.get("type") == "roller":
                    roller_text = content_item.get("content", [{}])[0].get(
                        "text", ""
                    )
                    paragraph_text += f"[{roller_text}] "

            if paragraph_text.strip():
                result.append(paragraph_text.strip())

    return "\n".join(result)
