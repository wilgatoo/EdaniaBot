import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

import config
import database
from garmoth import GarmothReader


# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()

intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# GARMOTH
# ============================================================

garmoth = GarmothReader()


# ============================================================
# FORMATEAR TIEMPO RESTANTE
# ============================================================

def format_remaining(milliseconds):

    total_seconds = max(
        int(milliseconds / 1000),
        0
    )

    minutes, seconds = divmod(
        total_seconds,
        60
    )

    hours, minutes = divmod(
        minutes,
        60
    )

    if hours > 0:

        return (
            f"{hours}h "
            f"{minutes:02d}m"
        )

    return (
        f"{minutes}m "
        f"{seconds:02d}s"
    )


# ============================================================
# OBTENER BUFF ACTIVO
# ============================================================

def get_active_call(domain):

    now = int(
        datetime.now(
            timezone.utc
        ).timestamp() * 1000
    )

    active_calls = []

    for call in domain["calls"]:

        started_at = call.get(
            "startedAt"
        )

        expires_at = call.get(
            "expiresAt"
        )

        if not started_at or not expires_at:
            continue

        if started_at <= now < expires_at:

            active_calls.append(call)

    if not active_calls:
        return None

    active_calls.sort(
        key=lambda x: x.get(
            "startedAt",
            0
        ),
        reverse=True
    )

    return active_calls[0]


# ============================================================
# CONSTRUIR MENSAJE DE ESTADO
# ============================================================

def build_status(data):

    lines = []

    lines.append(
        "🏰 **EDANIA — SERVER BUFFS SA**"
    )

    lines.append("")

    for domain in data["domains"].values():

        uses = domain["uses"]

        remaining = max(
            config.MAX_USES - uses,
            0
        )

        next_use = uses + 1

        lines.append(
            f"**{domain['name']}** — "
            f"{domain['boss']}"
        )

        active_call = get_active_call(
            domain
        )

        if active_call:

            now = int(
                datetime.now(
                    timezone.utc
                ).timestamp() * 1000
            )

            time_remaining = (
                active_call["expiresAt"] - now
            )

            lines.append(
                f"🟢 **ACTIVO** — "
                f"termina en "
                f"**{format_remaining(time_remaining)}**"
            )

        else:

            lines.append(
                "⚪ **INACTIVO**"
            )

        lines.append(
            f"Usado esta semana: "
            f"**{uses}/{config.MAX_USES}**"
        )

        if remaining > 0:

            lines.append(
                f"Próximo uso: **#{next_use}** "
                f"({remaining} restantes)"
            )

        else:

            lines.append(
                "Próximo uso: "
                "**Límite semanal alcanzado**"
            )

        lines.append("")

    lines.append(
        f"🔄 Actualización: "
        f"{datetime.now().strftime('%H:%M:%S')}"
    )

    return "\n".join(lines)


# ============================================================
# OBTENER CANAL DE DISCORD
# ============================================================

async def get_status_channel():

    if not config.DISCORD_CHANNEL_ID:
        return None

    channel = bot.get_channel(
        config.DISCORD_CHANNEL_ID
    )

    if channel is None:

        try:

            channel = await bot.fetch_channel(
                config.DISCORD_CHANNEL_ID
            )

        except Exception as error:

            print(
                f"No se pudo encontrar el canal: {error}"
            )

            return None

    return channel


# ============================================================
# ACTUALIZAR MENSAJE DE ESTADO
# ============================================================

async def update_status(data):

    message_id = database.get_status_message(
        config.DISCORD_CHANNEL_ID
    )

    channel = await get_status_channel()

    if channel is None:
        return

    if message_id:

        try:

            message = await channel.fetch_message(
                message_id
            )

            await message.edit(
                content=build_status(data)
            )

            return

        except discord.NotFound:

            print(
                "El mensaje anterior no existe. "
                "Se creará uno nuevo."
            )

        except discord.HTTPException as error:

            print(
                f"Error actualizando mensaje: {error}"
            )

            return

    try:

        message = await channel.send(
            build_status(data)
        )

        database.set_status_message(
            config.DISCORD_CHANNEL_ID,
            message.id
        )

    except discord.HTTPException as error:

        print(
            f"Error creando mensaje: {error}"
        )


# ============================================================
# INICIALIZAR BASE DE DATOS
# ============================================================

async def initialize_database(data):

    current_week = str(
        data.get("since")
    )

    saved_week = database.get_meta(
        "week_since"
    )

    known_ids = database.get_call_ids()

    if saved_week != current_week:

        print(
            "🔄 Nueva semana detectada. "
            "Reiniciando registros."
        )

        database.clear_calls()

        database.set_meta(
            "week_since",
            current_week
        )

        known_ids = set()

    if not known_ids:

        print(
            "📥 Guardando registros actuales "
            "de Garmoth como conocidos."
        )

        for domain in data["domains"].values():

            for call in domain["calls"]:

                call_id = call.get("id")

                if call_id is None:
                    continue

                database.save_call(
                    call_id,
                    call.get("buffId", ""),
                    call.get("startedAt", 0)
                )


# ============================================================
# DETECTAR NUEVOS EDANA
# ============================================================

async def detect_new_buffs(data):

    known_ids = database.get_call_ids()

    new_calls = []

    for domain in data["domains"].values():

        for call in domain["calls"]:

            call_id = call.get("id")

            if call_id is None:
                continue

            if call_id not in known_ids:

                new_calls.append(
                    (
                        call.get(
                            "startedAt",
                            0
                        ),
                        call,
                        domain
                    )
                )

    new_calls.sort(
        key=lambda item: item[0]
    )

    for _, call, domain in new_calls:

        call_id = call["id"]

        database.save_call(
            call_id,
            call.get("buffId", ""),
            call.get("startedAt", 0)
        )

        sorted_calls = sorted(
            domain["calls"],
            key=lambda x: x.get(
                "startedAt",
                0
            )
        )

        use_number = next(
            (
                index + 1
                for index, existing_call
                in enumerate(sorted_calls)
                if existing_call.get("id") == call_id
            ),
            domain["uses"]
        )

        # ================================================
        # MENSAJE DE ALERTA
        # ================================================

        message = (
            f"<@&{config.DISCORD_ROLE_ID}>\n\n"
            "🚨 **NUEVO EDANA'S BLESSING**\n\n"
            f"🏰 **{domain['name']}**\n"
            f"⚔️ {domain['boss']}\n"
            f"📊 Uso: **#{use_number}/"
            f"{config.MAX_USES}**"
        )

        channel = await get_status_channel()

        if channel is not None:

            try:

                await channel.send(
                    message,
                    allowed_mentions=discord.AllowedMentions(
                        roles=True
                    )
                )

            except discord.HTTPException as error:

                print(
                    f"Error enviando alerta: {error}"
                )


# ============================================================
# MONITOREO DE GARMOTH
# ============================================================

@tasks.loop(
    seconds=config.CHECK_INTERVAL
)
async def monitor_garmoth():

    try:

        data = garmoth.read()

        saved_week = database.get_meta(
            "week_since"
        )

        current_week = str(
            data.get("since")
        )

        if saved_week != current_week:

            print(
                "🔄 Nueva semana detectada."
            )

            database.clear_calls()

            database.set_meta(
                "week_since",
                current_week
            )

            for domain in data["domains"].values():

                for call in domain["calls"]:

                    call_id = call.get("id")

                    if call_id is None:
                        continue

                    database.save_call(
                        call_id,
                        call.get("buffId", ""),
                        call.get("startedAt", 0)
                    )

        else:

            await detect_new_buffs(
                data
            )

        await update_status(
            data
        )

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            "Garmoth actualizado."
        )

    except Exception as error:

        print(
            f"❌ Error consultando Garmoth: {error}"
        )


# ============================================================
# ESPERAR A QUE DISCORD ESTÉ LISTO
# ============================================================

@monitor_garmoth.before_loop
async def before_monitor():

    await bot.wait_until_ready()


# ============================================================
# BOT CONECTADO
# ============================================================

@bot.event
async def on_ready():

    print(
        f"✅ Bot conectado como {bot.user}"
    )

    try:

        database.initialize()

        data = garmoth.read()

        await initialize_database(
            data
        )

        await update_status(
            data
        )

        if not monitor_garmoth.is_running():

            monitor_garmoth.start()

    except Exception as error:

        print(
            f"❌ Error durante el inicio: {error}"
        )


# ============================================================
# COMANDO DE PRUEBA DE ALERTA
# ============================================================

@bot.command()
async def testalerta(ctx):

    message = (
        f"<@&{config.DISCORD_ROLE_ID}>\n\n"
        "🚨 **PRUEBA — NUEVO EDANA'S BLESSING**\n\n"
        "🏰 **Magaia**\n"
        "⚔️ Elion\n"
        "📊 Uso: **#4/10**"
    )

    await ctx.send(
        message,
        allowed_mentions=discord.AllowedMentions(
            roles=True
        )
    )


# ============================================================
# COMANDO DE PRUEBA DE DETECCIÓN
# ============================================================

@bot.command()
async def testedana(ctx):

    message = (
        "🚨 **PRUEBA DE DETECCIÓN AUTOMÁTICA**\n\n"
        "🏰 **Aphrodon**\n"
        "⚔️ Agris\n"
        "📊 Uso: **#2/10**\n\n"
        "✅ La alerta automática funciona correctamente."
    )

    await ctx.send(
        message
    )


# ============================================================
# INICIAR BOT
# ============================================================

if __name__ == "__main__":

    database.initialize()

    bot.run(
        config.DISCORD_TOKEN
    )