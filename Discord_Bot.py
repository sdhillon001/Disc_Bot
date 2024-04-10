import discord
from discord.ext import commands
import os
import random
import requests
import pandas as pd
from datetime import datetime, timedelta

# Load tokens and hosts from a text file
def load_tokens(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        tokens = {}
        for line in lines:
            key, value = line.strip().split('=')
            tokens[key] = value
        return tokens

TOKENS_FILE_PATH = "tokens.txt"
TOKENS = load_tokens(TOKENS_FILE_PATH)

required_keys = ["DISCORD_TOKEN", "RAPIDAPI_KEY", "RAPIDAPI_HOST_JOKES", "RAPIDAPI_HOST_FACTS",
                 "RAPIDAPI_HOST_STOCK", "RAPIDAPI_HOST_FGI", "RAPIDAPI_HOST_ALPHA"]
missing_keys = [key for key in required_keys if key not in TOKENS]

if missing_keys:
    raise ValueError(f"Missing token(s) in tokens file: {', '.join(missing_keys)}")

bot = commands.Bot(command_prefix='$')
greetings = ["hello", "hi", "yo", "wys"]
greeting_responses = ["Nice to meet you!", "Hello there!", "Hey long time no see!"]

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('Nothing'))
    print("Bot is online!")
    print('Logged in as {0.user}'.format(bot.user))

@bot.command()
async def date(ctx):
    current_time = datetime.now()
    await ctx.send(f"Date: {current_time.strftime('%B %d, %Y')}\nTime: {current_time.strftime('%H:%M:%S')}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"{ctx.author.name}'s ping is {round(bot.latency * 1000)}ms")

@bot.command()
async def joke(ctx):
    url = "https://{}/v1/jokes".format(TOKENS["RAPIDAPI_HOST_JOKES"])
    headers = {
        'x-rapidapi-host': TOKENS["RAPIDAPI_HOST_JOKES"],
        'x-rapidapi-key': TOKENS["RAPIDAPI_KEY"]
    }
    response = requests.get(url, headers=headers).json()
    await ctx.send(response[0]['joke'])

@bot.command()
async def fact(ctx):
    url = "https://{}/v1/facts".format(TOKENS["RAPIDAPI_HOST_FACTS"])
    headers = {
        'x-rapidapi-host': TOKENS["RAPIDAPI_HOST_FACTS"],
        'x-rapidapi-key': TOKENS["RAPIDAPI_KEY"]
    }
    response = requests.get(url, headers=headers).json()
    await ctx.send(response[0]['fact'])

@bot.command()
async def trade(ctx):
    embed = discord.Embed(title="Trading Commands")
    embed.add_field(name="$ticker", value="Prints stock info E.G $NIO", inline=False)
    embed.add_field(name="%ticker", value="Prints past 5 days opening price", inline=False)
    embed.add_field(name="/fgi", value="Prints greed and fear index ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def fgi(ctx):
    url = "https://{}/v1/fgi".format(TOKENS["RAPIDAPI_HOST_FGI"])
    headers = {
        'x-rapidapi-host': TOKENS["RAPIDAPI_HOST_FGI"],
        'x-rapidapi-key': TOKENS["RAPIDAPI_KEY"]
    }
    response = requests.get(url, headers=headers).json()
    fgi_value = response['fgi']['now']['valueText']
    await ctx.send(f"The current market sentiment is: {'Fear' if fgi_value == 'F' else 'Neutral' if fgi_value == 'N' else 'Greed'}")

@bot.command()
async def ticker(ctx, symbol: str):
    url = "https://{}/stock/v2/get-chart".format(TOKENS["RAPIDAPI_HOST_STOCK"])
    querystring = {"interval": "5m", "symbol": symbol, "range": "1d", "region": "US"}
    headers = {
        'x-rapidapi-host': TOKENS["RAPIDAPI_HOST_STOCK"],
        'x-rapidapi-key': TOKENS["RAPIDAPI_KEY"]
    }
    response = requests.get(url, headers=headers, params=querystring).json()
    meta = response['chart']['result'][0]['meta']
    embed = discord.Embed(title=meta['symbol'], description="")
    embed.add_field(name="Current Price", value=f"${meta['regularMarketPrice']}", inline=False)
    embed.add_field(name="Previous Close", value=f"${meta['previousClose']}", inline=False)
    embed.add_field(name="Trading Period", value=meta['currentTradingPeriod'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def opening_prices(ctx, symbol: str):
    current_date = pd.Timestamp.now().date()
    url = "https://{}/query".format(TOKENS["RAPIDAPI_HOST_ALPHA"])
    querystring = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact", "datatype": "json"}
    headers = {
        'x-rapidapi-host': TOKENS["RAPIDAPI_HOST_ALPHA"],
        'x-rapidapi-key': TOKENS["RAPIDAPI_KEY"]
    }
    response = requests.get(url, headers=headers, params=querystring).json()
    time_series = response["Time Series (Daily)"]
    dates = [current_date - timedelta(days=i) for i in range(5)]
    prices = [float(time_series[str(date)]["1. open"]) for date in dates if str(date) in time_series]
    prices_str = [f"{date.strftime('%A')} closing price: ${price:.2f}" for date, price in zip(dates, prices)]
    await ctx.send("\n".join(prices_str))

bot.run(TOKENS["DISCORD_TOKEN"])
