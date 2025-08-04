# pyxfluff 2025

from AOS import app, AOSError
from AOS.plugins.database import db

from random import randint
from nanoid import generate
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, Request

from .bot import modals, processor, queue
from . import middleware

import asyncio
import threading

router = APIRouter(
    prefix="/remote",
    dependencies=[Depends(middleware.DiscordAuthentication)]
)


@router.get("/")
def root():
    return JSONResponse(
        {"code": 200, "data": "OK", "plugin": "DiscordRemote", "queue": queue.action_queue}, status_code=200
    )

@router.get("/api/ping")
def api_ping():
    return JSONResponse(
        {
            "code": 200, 
            "data": "OK"
        }, status_code=200
    )


@router.get("/api/action-queue")
def action_queue(req: Request):
    queue_output = queue.action_queue.get(req.headers.get("Roblox-Id"))

    if queue_output is None:
        return JSONResponse({"code": 200, "data": []}, status_code=200)

    copied_queue = queue_output[:]
    queue.action_queue[req.headers.get("Roblox-Id")] = []

    return JSONResponse({"code": 200, "data": copied_queue}, status_code=200)


@router.post("/api/queue-action")
async def create_action(req: Request):
    await req.json()

    return JSONResponse(
        {
            "code": 200, 
            "data": {}
        }, status_code=200
    )

@router.post("/secret/generate")
def generate_secret(req: Request):
    if req.headers.get("Roblox-Id") is None:
         return JSONResponse(
            {
                "code": 400, 
                "data": "You can only do that from Roblox."
            }, status_code=400
        )
    
    if db.get(req.headers.get("Roblox-Id"), db.DISCORD_REMOTE_SECRETS):
           return JSONResponse(
            {
                "code": 400, 
                "data": "You may not generate another token until you delete your first."
            }, status_code=200
        )   
    
    new_secret = generate(size=randint(30, 45))
    db.set(req.headers.get("Roblox-Id"), new_secret, db.DISCORD_REMOTE_SECRETS)

    return JSONResponse(
        {
            "code": 200, 
            "data": new_secret
        }, status_code=200
    )


app.include_router(router)

def run_bot():
    import discord
    from discord.ext import commands

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

    @bot.slash_command(name="test")
    async def test(ctx):
        await ctx.respond("sijdfgisfgijsfg")

    @bot.slash_command(name="link", description="Links a Roblox place to this server.")
    async def link(ctx):
        await ctx.send_modal(modals.RegisterModal())

    @bot.slash_command(name="ban", description="Ban a player.")
    async def ban(ctx):
        await ctx.send_modal(modals.BanModal())

    @bot.event
    async def on_ready():
        print(f"{bot.user} ready")

    loop.run_until_complete(bot.start(db.get("VERSION_BOT", db.SECRETS)))

def spawn():
    try:
        bot_thread = threading.Thread(target=run_bot, name="DiscordBot", daemon=True)
        bot_thread.start()
    except ImportError:
        print("pycord isn't installed, install it ") 

spawn()
