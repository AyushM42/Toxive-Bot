import discord
from discord.ext import commands
import config
import responses
from datetime import datetime, timezone
import asyncio


async def send_special_message(message, user_message):
    try:
        if user_message == "Junior, is everything okay?":
            await message.reply("I shall have my revenge.")
        

    except Exception as e:
        print(e)

async def send_message(message, user_message):
    try:
            #League
            if responses.league_response(user_message):
                print("League mentioned")
                await message.reply("https://tenor.com/view/rule11-no-league-of-legends-bruv-rules-gif-23677770")

            #Val
            if responses.val_response(user_message):
                print("Val mentioned")
                await message.reply("https://tenor.com/view/rule18-gif-23154950")

            #one piece
            if responses.one_piece_response(user_message):
                print("One piece mentioned")
                await message.reply("https://tenor.com/view/rule154-no-one-piece-gif-23700813")

            #LowTierGod
            if responses.kys_response(user_message):
                await message.channel.send("https://tenor.com/view/ltg-low-tier-god-yskysn-ltg-thunder-thunder-gif-23523876")

            #JJK
            if responses.jjk_response(user_message):
                print("jjk mentioned")
                await message.reply("https://tenor.com/view/rule137-no-jujutsu-kaisen-gif-23697731")

            #toxivejr
            if responses.toxjr_response(user_message):
                await message.reply("Ready to comply.", file=discord.File('toxivejunior.png'))

            if responses.honkai_response(user_message):
                print("honkai mentioned")
                await message.reply("https://tenor.com/view/honkai-gif-14136885181316463224")


            #joever
            if responses.joever_response(user_message):
                print("Joever mentioned")
                await message.reply(file=discord.File('itsjoever.jpeg'))

            #hi = hi
            if (responses.hi_response(user_message) == 1) or (responses.hi_response(user_message) == 2):
                print("hi mentioned")
                await message.channel.send(user_message)




            #Night is still young
            now = datetime.now()
            if now.hour<7 or now.hour>=19.5:
                if responses.night_response(user_message):
                    print("Night mentioned")
                    if "the night is still young" not in user_message.lower():
                        await message.reply("The night is still young...")
                    await message.channel.send("https://cdn.discordapp.com/attachments/1216832432037298419/1230412824807997460/IMG_1386.gif?ex=66333a3d&is=6620c53d&hm=b56c5670ac3b3972712586ecd47dd409715b9e67d521041c6ed64c605daee954&")

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
        user_message = str(message.content).strip("!")
        channel = str(message.channel)
        print(f"{username} said: '{user_message}' ({channel})")
        await send_message(message, user_message)
        #await message.channel.send("i really fw your energy")
        if username == "toxive":
            await send_special_message(message, user_message)

    client.run(TOKEN)