import random
import re
from asyncio import sleep

from discord import File
from discord.ext import commands
from playwright.async_api import async_playwright

from utilities import logger, utils


class SuperMarselo(commands.Cog):
    """Crazy random commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Separa os times pro famigerado.",
        help=(
            "Esse comando separa dois times para jogar codenames, já "
            "selecionando quem vai ser o spymaster de cada time.\n\nSe você "
            "quiser, ele pode, ainda, criar uma sala de Codenames e enviar o "
            "link. Para isso, adicione um dos argumentos a seguir: "
            '"$createRoom=true", "$createRoom", "True", "createRoom", '
            '"criarSala", "link", "URL", "URI".\ne.g.: ">codenames '
            '$createRoom=True", ou ">codenames True", ou ">codenames link", '
            "etc.\n\nÉ necessário estar conectado a um canal de voz com pelo "
            "menos mais três pessoas para ativar esse comando."
        ),
    )
    async def codenames(self, ctx, createRoom=None):
        """Create a Codenames room."""
        await ctx.trigger_typing()
        logger.info("`>codenames` command called.")

        voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
        members = [m for m in voiceChannel.members if not m.bot] if voiceChannel else []

        if not voiceChannel or len(members) < 4:
            await utils.react_message(ctx.message, ["🙅‍♂️", "❌", "🙅‍♀️"])

            response = await ctx.send(
                "É necessário estar em um canal de voz para usar esse comando."
                if not voiceChannel
                else "É necessário no mínimo 4 pessoas para jogar Codenames."
            )
            await utils.react_response(response)

            return
        else:
            await utils.react_message(ctx.message, ["🎲", "🎮", "🏏", "🕹️"])

        createRoom = createRoom and createRoom.lower() in [
            "$createroom=true",
            "$createroom",
            "true",
            "createroom",
            "criarsala",
            "link",
            "url",
            "uri",
        ]

        logger.info(f"{len(members)} members are present.", 2)
        logger.info(f'A room will {"" if createRoom else "not"} be created.', 2)

        people = [member.mention for member in members]

        blueSpymaster = random.choice(people)
        people.remove(blueSpymaster)

        redSpymaster = random.choice(people)
        people.remove(redSpymaster)

        blueOperatives = []
        for _ in range(len(people) // 2):
            blueOperatives.append(random.choice(people))
            people.remove(blueOperatives[-1])

        redOperatives = people

        logger.info("The teams were created.", 2)

        try:
            async with async_playwright() as p:
                if createRoom:
                    logger.info("A room is being created.", 2)

                    logger.info("Opening the website...", 2)

                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto("https://codenames.game/")

                    await ctx.trigger_typing()
                    logger.info("Waiting for the website to load...", 2)

                    await page.wait_for_selector("#nickname")
                    await page.fill("#nickname", "A Voz da SA-SEL")
                    await page.click('button[type="submit"]')

                    logger.info("Setting up the game...", 2)

                    await page.wait_for_url("**/r/*")

                    word_packs_button = await page.wait_for_selector("button:has-text('Word Packs'), button:has-text('Pacotes de palavras')")
                    await word_packs_button.click()

                    word_language_button = await page.wait_for_selector("button:has-text('Word Language'), button:has-text('Idioma das palavras')")
                    await word_language_button.click()

                    await page.wait_for_selector("text=Português (Brasil)")
                    await page.locator("text=Português (Brasil)").scroll_into_view_if_needed()
                    await page.get_by_text("Português (Brasil)", exact=True).click()

                    await page.get_by_role("button", name=re.compile(r"aprovar|approve", re.I)).click()

                    logger.info("Português (Brasil) word package selected!", 2)

                    await page.get_by_role("button", name=re.compile(r"iniciar jogo|start game", re.I)).click()

                    logger.info("Waiting for the room to be created...", 2)

                    await page.wait_for_selector("div > article:nth-child(25)")

                    roomURL = page.url
                else:
                    roomURL = None
                    browser = None

                response = await ctx.send(
                    "`TÁ NA HORA DO CODENAMES GAROTADA`\n\n"
                    + (f"**Link da sala**: {roomURL}\n\n" if roomURL else "")
                    + f"**Time azul**  🔵:\n__*Spymaster*__: {blueSpymaster}\n"
                    + f'__*Operatives*__: {", ".join(blueOperatives)}\n\n**Time '
                    + f"vermelho**  🔴:\n__*Spymaster*__: {redSpymaster}\n"
                    + f'__*Operatives*__: {", ".join(redOperatives)}\n\n'
                    + "Que vença o melhor time!"
                )
                await utils.react_response(response)

                # if a room was created, the bot needs
                # to leave it after someone entered
                await sleep(120)
                await ctx.trigger_typing()

                try:
                    people = (
                        [blueSpymaster] + blueOperatives + [redSpymaster] + redOperatives
                    )

                    try:
                        logger.info("Searching for new game hosts...", 2)

                        await page.get_by_role("button", name="Admin").click()

                        players = []

                        # Seleciona todos os players
                        playerSelectors = await page.locator('div[data-radix-scroll-area-viewport] section div[type="button"]').all()

                        for player in playerSelectors:
                            nome_div = player.locator('div.overflow-hidden.whitespace-nowrap.leading-none.text-center')
                            if await nome_div.count() == 0:
                                continue
                            nome = (await nome_div.inner_text()).strip()

                            if nome.lower() == "a voz da sa-sel":
                                continue

                            players.append((player, nome))

                        newHostElement, newHostName = random.choice(players)

                        if players:
                            await newHostElement.click()
                            await page.get_by_role("button", name=re.compile(r"promover|promote", re.I)).click()
                            logger.info(f"Player {newHostName} was promoted to host...", 2)
                        else:
                            logger.info("No player was found to be promoted...", 2)
                    except Exception:
                        # await page.screenshot(path="codenames/debug_screenshot.png")
                        response = await ctx.send(
                            f"Alô, {ctx.author.mention}! Eu vou sair da sala, mas como ninguém mais entrou, a sala vai ficar sem host. "
                            f'Se quiserem que crie outra sala depois, é só chamar.\n\ncc: {" ".join(people)}'
                        )
                    else:
                        response = await ctx.send(
                            f'Alô, {ctx.author.mention}! Eu vou sair da sala, agora **o novo host é o `{newHostName}`**.\n\ncc: {" ".join(people)}'
                        )
                    finally:
                        await utils.react_response(response)

                    logger.info("Leaving game...", 2)
                    await page.get_by_role("button", name=re.compile(r"configurações|settings", re.I)).click()

                    scroll_container = await page.wait_for_selector("div[data-radix-scroll-area-viewport]")
                    await scroll_container.evaluate("(el) => { el.scrollTop = el.scrollHeight; }")

                    await page.get_by_role("button", name=re.compile(r"sair da partida|leave match", re.I)).click()
                finally:
                    await sleep(5)
                    await browser.close()
                    logger.info("Browser closed...", 2)
        except Exception as e:
            await sleep(5)
            await browser.close()
            logger.error(f"Erro ao criar sala: {e}")

    @commands.command(brief="Press F to pay respects.")
    async def F(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>F` command called.")
        await utils.react_message(ctx.message, "⚰")
        response = await ctx.send("`Press F to Pay Respects`")
        await utils.react_response(response)

    @commands.command(brief="Chama um membro.", aliases=["cade", "kd"])
    async def cadê(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>cadê` command called.")
        await utils.react_message(ctx.message, ["🤬"])
        response = await ctx.send(
            f"**cadê vc otário??** {' '.join(user)}", file=File("images/cade-vc.png")
        )
        await utils.react_response(response, ["❔"])

    @commands.command(brief='"Bane" um "usuário" do servidor.')
    async def ban(self, ctx, *user):
        await ctx.trigger_typing()
        logger.info("`>ban` command called.")
        await utils.react_message(ctx.message, ["👺"])
        response = await ctx.send(f"O usuário '{' '.join(user)}' foi banido.")
        await utils.react_response(response, ["💀"])

    @commands.command(brief="Declara a saideira!")
    async def saideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>saideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            f"A saideira do {ctx.author.mention} está oficialmente declarada! "
            "A próxima partida será a última dele. Em caso de saideira de "
            'conversa, "a próxima partida" equivale aos próximos 30 minutos '
            "de um bom papo. \n\nPara mais informações, acione o comando "
            "`>regrasSaideira`."
        )
        await utils.react_response(response)

    @commands.command(
        brief="Regras relacionadas à saideira.",
        aliases=["regrassaideira", "regrasaideira"],
    )
    async def regrasSaideira(self, ctx):
        await ctx.trigger_typing()
        logger.info("`>regrasSaideira` command called.")
        await utils.react_message(ctx.message, ["🍉", "🚩"])
        response = await ctx.reply(
            "**A REGRA É CLARA!**\n\nA saideira precisa ser previamente "
            "declarada com uso do comando `>saideira`. Caso contrário, a "
            "saideira é inválida e todos têm direito de acionar o comando "
            "`>kakashi` para quem descumpriu a regra.\n\nA partir do momento "
            "em que a saideira for declarada, o declarante deve continuar "
            "jogando por no mínimo mais uma (01) partida e, no máximo, duas "
            "(02) - depois desse tempo, a saideira expira e deverá ser "
            "declarada novamente. Vale lembrar, que a 'partida' da saideira de "
            "conversa equivale a 30 minutos de um bom papo."
        )
        await utils.react_response(response)


def setup(bot):
    bot.add_cog(SuperMarselo(bot))
