import asyncio
from asyncio import sleep
from discord import Colour, Embed, AsyncWebhookAdapter, Webhook

from utils.custom_logger import logger


async def send_webhook(_dict, webhook_url, webhook_client, title, title_link):

    # sending webhook
    webhook = Webhook.from_url(
        url=webhook_url,
        adapter=AsyncWebhookAdapter(webhook_client))

    # create embed
    embed = Embed(title=title, color=Colour.green(), url=title_link)
    embed.set_footer(text='WINX4 Bots - winwinwinwin#0001',
                     icon_url='https://images6.alphacoders.com/909/thumb-1920-909641.png')
    for key, value in _dict.items():
        embed.add_field(name=f'{key}', value=f'{value}', inline=False)

    while True:
        try:
            await webhook.send(username='adidasAE Bot',
                               avatar_url=
                               'https://encrypted-tbn0.gstatic.com/'
                               'images?q=tbn:ANd9GcQnOWzgQKgSQmzHq-8Gb1QnvIM8PSjmpex1NA&usqp=CAU',
                               embed=embed,
                               )
            break
        except Exception:
            logger().exception('Webhook Failed')
            await sleep(2)