import discord
from discord.ext import commands


# =========================================================
# CONFIG
# =========================================================

TOKEN = "MTU0ODk3MTIwNjA1NTY5ODQ3Mg.Gtqyoj.C_Bjlp8tKheU6DD0XxLZQFPwVQltHYra05qfM4"

TICKET_CATEGORY_ID = 1533481557602340914
STAFF_ROLE_ID = 1549146970847711295


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# EMOJIS
# =========================================================

TICKET_EMOJI = "🎟️"
SUPPORT_EMOJI = "🛠️"
PURCHASE_EMOJI = "🛒"
PARTNERSHIP_EMOJI = "🤝"
REPORT_EMOJI = "🚨"
BAN_EMOJI = "🔨"
CLOSE_EMOJI = "🔒"


# =========================================================
# TICKET TYPES
# =========================================================

TICKET_TYPES = {
    "support": "Support",
    "purchase": "Purchase",
    "partnership": "Partnership",
    "report": "Report",
    "ban-appeal": "Ban Appeal"
}


# =========================================================
# CREATE TICKET
# =========================================================

async def create_ticket(
    interaction: discord.Interaction,
    ticket_type: str
):

    guild = interaction.guild
    user = interaction.user

    category = guild.get_channel(
        TICKET_CATEGORY_ID
    )

    staff_role = guild.get_role(
        STAFF_ROLE_ID
    )

    # Check category
    if category is None:
        await interaction.response.send_message(
            "❌ The ticket category was not found.",
            ephemeral=True
        )
        return

    # Check staff role
    if staff_role is None:
        await interaction.response.send_message(
            "❌ The staff role was not found.",
            ephemeral=True
        )
        return

    # Check existing ticket
    existing_ticket = discord.utils.find(
        lambda channel:
        channel.topic == f"ticket_owner:{user.id}",
        guild.text_channels
    )

    if existing_ticket:
        await interaction.response.send_message(
            f"❌ You already have an open ticket: "
            f"{existing_ticket.mention}",
            ephemeral=True
        )
        return

    # Channel name
    safe_name = (
        user.name
        .lower()
        .replace(" ", "-")
    )

    channel_name = f"{ticket_type}-{safe_name}"

    # Permissions
    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

        staff_role:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                manage_messages=True
            ),

        guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
                embed_links=True
            )
    }

    # Create channel
    channel = await guild.create_text_channel(
        name=f"🎫・{channel_name}",
        category=category,
        topic=f"ticket_owner:{user.id}",
        overwrites=overwrites,
        reason=f"Ticket created by {user}"
    )

    # Ticket name
    ticket_name = TICKET_TYPES.get(
        ticket_type,
        ticket_type
    )

    # Ticket embed
    embed = discord.Embed(
        title=f"{TICKET_EMOJI} Ticket Created",

        description=(
            f"Hello {user.mention}!\n\n"

            f"Your **{ticket_name}** ticket has been "
            "successfully created.\n\n"

            "Please explain your concern clearly "
            "and provide any necessary information.\n\n"

            f"{SUPPORT_EMOJI} A staff member will assist "
            "you as soon as possible.\n\n"

            f"{CLOSE_EMOJI} Use the button below when "
            "you want to close this ticket."
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

    # Send ticket message
    await channel.send(
        content=(
            f"{user.mention} "
            f"{staff_role.mention}"
        ),
        embed=embed,
        view=CloseTicketView()
    )

    # Confirmation
    await interaction.response.send_message(
        f"✅ Your ticket has been created: "
        f"{channel.mention}",
        ephemeral=True
    )


# =========================================================
# CREATE TICKET BUTTON
# =========================================================

class CreateTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Create Ticket",
            emoji=TICKET_EMOJI,
            style=discord.ButtonStyle.primary,
            custom_id="ticket_create"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(
            interaction,
            "support"
        )


# =========================================================
# CATEGORY DROPDOWN
# =========================================================

class TicketSelect(
    discord.ui.Select
):

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
                description="Report a user or issue"
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

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(
            interaction,
            self.values[0]
        )


# =========================================================
# TICKET PANEL
# =========================================================

class TicketPanelView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            CreateTicketButton()
        )

        self.add_item(
            TicketSelect()
        )


# =========================================================
# CLOSE TICKET BUTTON
# =========================================================

class CloseTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Close Ticket",
            emoji=CLOSE_EMOJI,
            style=discord.ButtonStyle.danger,
            custom_id="ticket_close"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            "🔒 Closing this ticket...",
            ephemeral=True
        )

        await interaction.channel.delete(
            reason=(
                f"Ticket closed by "
                f"{interaction.user}"
            )
        )


# =========================================================
# CLOSE VIEW
# =========================================================

class CloseTicketView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            CloseTicketButton()
        )


# =========================================================
# TICKET PANEL COMMAND
# =========================================================

@bot.tree.command(
    name="ticketpanel",
    description="Send the CYBERIX SHOP ticket panel"
)
async def ticketpanel(
    interaction: discord.Interaction
):

    embed = discord.Embed(

        title="⚙️ CYBERIX SHOP TICKET",

        description=(
            "**NEED HELP?? OPEN A TICKET BELOWN**\n\n"

            f"{TICKET_EMOJI} **CREATE TICKET**\n"
            "**CREATE A GENERAL SUPPORT TICKET**\n\n"


            "**WELCOME TO CYBERIX SHOP**\n\n"

            f"{SUPPORT_EMOJI} SUPPORT\n"
            f"{PURCHASE_EMOJI} PURCHASE\n"
            f"{PARTNERSHIP_EMOJI} PARTNERSHIP\n"
            f"{REPORT_EMOJI} REPORT\n"
            f"{BAN_EMOJI} BAN APPEAL"
        ),

        # RED SIDEBAR
        color=discord.Color.red()
    )

    # WALANG FOOTER DITO

    await interaction.response.send_message(
        embed=embed,
        view=TicketPanelView()
    )


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print("=================================")
    print(f"Bot: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("Ticket System: ONLINE")
    print("=================================")


# =========================================================
# START BOT
# =========================================================

bot.run(TOKEN)
