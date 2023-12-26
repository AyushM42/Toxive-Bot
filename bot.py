import discord
import pytz
import responses
import datetime
from astral import Astral

async def send_message(message, user_message):
    try:

        a = Astral()
        city = a['Irvine']
        now = datetime.now(pytz.pst)
        sun = city.sun(date=now, local=True)
        if now >=sun['dusk'] or now <= sun['dawn']:
            if responses.handle_response(user_message):
                await message.channel.send("The night is still young...")
                await message.channel.send("https://tenor.com/view/batman-gif-4439279616571508647")
    except Exception as e:
        print(e)

def run_discord_bot():
    TOKEN = 'MTE4OTAyODA5ODMwMjI4Mzk1Nw.GcA7Ge.vRP4DUo_5oEzrFyMwEhCPlRjFirvd8umWH6im0'
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f'{client.user} is now running.')

    client.run(TOKEN)