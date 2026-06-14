import asyncio


async def _translate(text):
    from googletrans import Translator

    async with Translator() as translator:
        result = await translator.translate(text, dest="pt")
    return result.text


def translate_to_portuguese(text):
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("Não há descrição disponível para traduzir.")
    if len(text) > 5000:
        raise ValueError("A descrição é muito longa para tradução.")
    return asyncio.run(_translate(text))
