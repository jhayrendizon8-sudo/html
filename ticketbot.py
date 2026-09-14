import os
import discord
from discord.ext import commands

# ============================================================
# CYBERIX SHOP - TICKET BOT
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Discord IDs
TICKET_CATEGORY_ID = 1545614583731986494
STAFF_ROLE_ID = 1545619088884113468

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. Add your bot token as an environment variable."
    )

# Intents
intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Emojis
TICKET_EMOJI = "🎟️"
SUPPORT_EMOJI = "🛠️"
PURCHASE_EMOJI = "🛒"
PARTNERSHIP_EMOJI = "🤝"
REPORT_EMOJI = "🚨"
BAN_EMOJI = "🔨"
CLOSE_EMOJI = "🔒"

TICKET_TYPES = {
    "support": "Support",
    "purchase": "Purchase",
    "partnership": "Partnership",
    "report": "Report",
    "ban-appeal": "Ban Appeal"
}


# ============================================================
# CREATE TICKET
# ============================================================

async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    guild = interaction.guild
    user = interaction.user

    if guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return

    category = guild.get_channel(TICKET_CATEGORY_ID)
    staff_role = guild.get_role(STAFF_ROLE_ID)

    if category is None or not isinstance(category, discord.CategoryChannel):
        await interaction.response.send_message(
            "❌ The ticket category was not found. Check TICKET_CATEGORY_ID.",
            ephemeral=True
        )
        return

    if staff_role is None:
        await interaction.response.send_message(
            "❌ The staff role was not found. Check STAFF_ROLE_ID.",
            ephemeral=True
        )
        return

    # Prevent duplicate tickets
    existing_ticket = discord.utils.find(
        lambda channel: (
            isinstance(channel, discord.TextChannel)
            and channel.topic == f"ticket_owner:{user.id}"
        ),
        guild.text_channels
    )

    if existing_ticket:
        await interaction.response.send_message(
            f"❌ You already have an open ticket: {existing_ticket.mention}",
            ephemeral=True
        )
        return

    safe_name = "".join(
        c for c in user.name.lower().replace(" ", "-")
        if c.isalnum() or c == "-"
    )[:30]

    if not safe_name:
        safe_name = f"user-{user.id}"

    channel_name = f"{ticket_type}-{safe_name}"

    # Permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),

        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        ),

        staff_role: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
            manage_messages=True
        ),

        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
            manage_messages=True,
            embed_links=True
        )
    }

    try:
        channel = await guild.create_text_channel(
            name=f"🎫・{channel_name}",
            category=category,
            topic=f"ticket_owner:{user.id}",
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to create ticket channels.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(
            f"❌ Discord error while creating the ticket: `{e}`",
            ephemeral=True
        )
        return

    ticket_name = TICKET_TYPES.get(ticket_type, ticket_type)

    embed = discord.Embed(
        title=f"{TICKET_EMOJI} Ticket Created",
        description=(
            f"Hello {user.mention}!\n\n"
            f"Your **{ticket_name}** ticket has been successfully created.\n\n"
            "Please explain your concern clearly and provide any "
            "necessary information.\n\n"
            f"{SUPPORT_EMOJI} A staff member will assist you as soon as possible.\n\n"
            f"{CLOSE_EMOJI} Use the button below when you want to close this ticket."
        ),
        color=discord.Color.red()
    )

    embed.add_field(
        name="📂 Category",
        value=f"`{ticket_name}`",
        inline=True
    )

    embed.add_field(
        name="👤 Ticket Owner",
        value=user.mention,
        inline=True
    )

    try:
        await channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
            view=CloseTicketView()
        )
    except discord.HTTPException:
        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}\n"
            "⚠️ I couldn't send the ticket message.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"✅ Your ticket has been created: {channel.mention}",
        ephemeral=True
    )


# ============================================================
# CREATE TICKET BUTTON
# ============================================================

class CreateTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Create Ticket",
            emoji=TICKET_EMOJI,
            style=discord.ButtonStyle.primary,
            custom_id="ticket_create"
        )

    async def callback(self, interaction: discord.Interaction):
        await create_ticket(interaction, "support")


# ============================================================
# TICKET CATEGORY SELECT
# ============================================================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Support",
                value="support",
                emoji=SUPPORT_EMOJI,
                description="Get help from our staff"
            ),
            discord.SelectOption(
                label="Purchase",
                value="purchase",
                emoji=PURCHASE_EMOJI,
                description="Questions about a purchase"
            ),
            discord.SelectOption(
                label="Partnership",
                value="partnership",
                emoji=PARTNERSHIP_EMOJI,
                description="Partnership inquiries"
            ),
            discord.SelectOption(
                label="Report",
                value="report",
                emoji=REPORT_EMOJI,
                description="Submit a report"
            ),
            discord.SelectOption(
                label="Ban Appeal",
                value="ban-appeal",
                emoji=BAN_EMOJI,
                description="Appeal a moderation action"
            )
        ]

        super().__init__(
            placeholder="Or choose a category...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="ticket_category"
        )

    async def callback(self, interaction: discord.Interaction):
        await create_ticket(
            interaction,
            self.values[0]
        )


# ============================================================
# TICKET PANEL VIEW
# ============================================================

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateTicketButton())
        self.add_item(TicketSelect())


# ============================================================
# CLOSE TICKET BUTTON
# ============================================================

class CloseTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Close Ticket",
            emoji=CLOSE_EMOJI,
            style=discord.ButtonStyle.danger,
            custom_id="ticket_close"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel

        await interaction.response.send_message(
            "🔒 Closing this ticket...",
            ephemeral=True
        )

        if isinstance(channel, discord.TextChannel):
            try:
                await channel.delete(
                    reason=f"Ticket closed by {interaction.user}"
                )
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())


# ============================================================
# /TICKETPANEL COMMAND
# ============================================================

@bot.tree.command(
    name="ticketpanel",
    description="Send the CYBERIX SHOP ticket panel"
)
async def ticketpanel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="⚙️ CYBERIX SHOP TICKET",
        description=(
            "Need help? Open a ticket below.\n\n"
            f"{TICKET_EMOJI} **Create Ticket**\n"
            "Create a general support ticket.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**OR SELECT A CATEGORY BELOW**\n\n"
            f"{SUPPORT_EMOJI} Support\n"
            f"{PURCHASE_EMOJI} Purchase\n"
            f"{PARTNERSHIP_EMOJI} Partnership\n"
            f"{REPORT_EMOJI} Report\n"
            f"{BAN_EMOJI} Ban Appeal"
        ),
        color=discord.Color.red()
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketPanelView()
    )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    # Register persistent views after restart
    bot.add_view(TicketPanelView())
    bot.add_view(CloseTicketView())

    try:
        await bot.tree.sync()
    except discord.HTTPException as e:
        print(f"Slash command sync error: {e}")

    print("=================================")
    print(f"Bot: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Ticket System: ONLINE")
    print("=================================")


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
