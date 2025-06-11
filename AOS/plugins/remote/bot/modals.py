# pyxfluff 2025

from discord import ui
from httpx import get, HTTPError

from . import processor

from AOS import AOSError
from AOS.plugins.database import db

import discord


class RegisterModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Link Game")

        self.place = ui.InputText(
            label="Place ID",
            placeholder="Use `print(game.PlaceId)` to find yours",
            max_length=25,
            required=True
        )

        self.token = ui.InputText(
            label="Access Token", placeholder="xxxxxxxxxx", required=True
        )

        # self.api_url = ui.InputText(
        #     label="API URL",
        #     placeholder="https://aos-us-2.admsoftware.org",
        #     required=True
        # )

        self.add_item(self.place)
        self.add_item(self.token)
        # self.add_item(self.api_url)

    async def callback(self, interaction: discord.Interaction):
        # api_url = self.api_url.value
        api_url = "localhost:8020"
        place_id = self.place.value
        token = self.token.value
        response = {}

        print(f"register: {place_id} {token} on {api_url}")

        try:
            r = get(
                f"{api_url}/remote/api/ping",
                headers={"Roblox-Id": place_id, "X-Adm-Secret": token}
            )

            response = r.json()
            r.raise_for_status()

        except Exception as e:
            e = str(e).replace(
                "For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/",
                ""
            )
            await interaction.response.send_message(
                f":x: Something went wrong, please refer to the error below.\n{response} ({e})"
            )

            return

        db.set(
            interaction.guild_id,
            {"api_url": api_url, "place_id": place_id, "api_token": token},
            db.BOT_STORE,
        )

        await interaction.response.send_message(
            f":white_check_mark: Saved! You can now make moderation actions with commands."
        )


class BanModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Ban user")

        self.user = ui.InputText(
            label="User ID",
            placeholder="123456",
            max_length=20,
            min_length=4,
            required=True
        )

        self.time = ui.InputText(
            label="Ban Duration (seconds)", placeholder="86400", required=True
        )

        self.message = ui.InputText(
            label="Moderation Message", placeholder="Being rude to staff", required=True
        )

        self.log = ui.InputText(
            label="Log reason",
            placeholder="Called @staff_member a vulgar word",
            required=False
        )

        self.add_item(self.user)
        self.add_item(self.time)
        self.add_item(self.message)
        self.add_item(self.log)

    async def callback(self, interaction: discord.Interaction):
        print(
            f"BAN: {self.user.value} {self.message.value} {self.log.value} {self.time.value}"
        )

        try:
            controller = processor.APIController(interaction.guild_id)

            controller.ban(
                {
                    "user": self.user.value,
                    "reason": self.message.value,
                    "log_reason": self.log.value,
                    "duration": self.time.value
                }
            )
        except AOSError as e:
            await interaction.response.send_message(
                f":x: AOSError was raised: {e}", ephemeral=True
            )
            return
        except Exception as e:
            await interaction.response.send_message(
                f":x: Exception was raised: {e}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f":white_check_mark: Ban for {self.user.value} added to the processing queue"
        )
