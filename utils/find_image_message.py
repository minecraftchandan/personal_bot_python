import discord

async def find_image_message(messages):
    """
    Finds the first message that contains either:
    - an attachment (file image)
    - or an embed image
    """
    for message in messages:
        if message.attachments or (message.embeds and message.embeds[0].image):
            return message
    return None

def extract_image_url(message):
    """
    Extracts the image URL from a message:
    - Prefers attachment first
    - Falls back to embed image if no attachment
    """
    if message.attachments:
        return message.attachments[0].url
    elif message.embeds and message.embeds[0].image:
        return message.embeds[0].image.url
    return ''