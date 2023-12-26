import discord
import responses
import datetime
import pytz
from astral import LocationInfo, zoneinfo
from astral.sun import sun

async def send_message(message, user_message):
    try:
            city = LocationInfo("Irvine", "California", "America/Los Angeles", 33.6846, 117.82656)
            timezone = zoneinfo.ZoneInfo("America/Los Angeles")
            now = datetime.now(pytz.pst)
            s = sun(city.observer, date=now, tzinfo=timezone)
            if now>=s['dusk'] or now<=s['dawn']:
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