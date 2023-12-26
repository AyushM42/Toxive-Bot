import discord
import config
import responses
from datetime import datetime
import pytz
from astral import LocationInfo, zoneinfo
from astral.sun import sun

async def send_message(message, user_message):
    try:
            city = LocationInfo("Irvine", "California", "America/Los_Angeles", 33.6846, 117.82656)
            timezone = zoneinfo.ZoneInfo("America/Los_Angeles")
            now = datetime.now(timezone)
            s = sun(city.observer, date=now, tzinfo=timezone)
            if "league" in user_message.lower():
                 await message.channel.send("https://tenor.com/view/rule11-no-league-of-legends-bruv-rules-gif-23677770")

            if ("val" in user_message.lower()) or ("valorant" in user_message.lower()):
                 await message.channel.send("https://images-ext-2.discordapp.net/external/AjfAoSgU3g4O7OlxPl_j9IGr9OywDcRoD2TWpCwmaB8/https/media.tenor.com/4WbULfXsHfkAAAPo/rule18-no-valorant.mp4")

                 
            if now>=s['dusk'] or now<=s['dawn']:
                print("It is nighttime.")
                if responses.handle_response(user_message):
                    if "the night is still young" not in user_message.lower():
                        await message.reply("The night is still young...")
                    await message.channel.send("https://tenor.com/view/batman-gif-4439279616571508647")
    except Exception as e:
        print(e)

def run_discord_bot():
    TOKEN = config.TOKEN
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)


    @client.event
    async def on_ready():
        print(f'{client.user} is now running.')


    @client.event
    async def on_message(message):
         if message.author == client.user:
              return
         
         username = str(message.author)
         user_message = str(message.content)
         channel = str(message.channel)
         print(f"{username} said: '{user_message}' ({channel})")

         await send_message(message, user_message)
    client.run(TOKEN)