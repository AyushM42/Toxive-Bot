import discord
import config
import responses
from datetime import datetime
import pytz
from astral import LocationInfo, zoneinfo
from astral.sun import sun

async def send_message(message, user_message):
    try:
            #League
            if responses.league_response(user_message):
                 await message.channel.send("https://tenor.com/view/rule11-no-league-of-legends-bruv-rules-gif-23677770")

            #Val
            if responses.val_response():
                 await message.channel.send("https://tenor.com/view/rule18-gif-23154950")


            #Night is still young
            city = LocationInfo("Irvine", "California", "America/Los_Angeles", 33.6846, 117.82656)
            timezone = zoneinfo.ZoneInfo("America/Los_Angeles")
            now = datetime.now(timezone)
            s = sun(city.observer, date=now, tzinfo=timezone)
            if now>=s['dusk'] or now<=s['dawn']:
                print("It is nighttime.")
                if responses.night_response(user_message):
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