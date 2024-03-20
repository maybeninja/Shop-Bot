from discord.ext import commands
import discord
import json
import requests

config = json.load(open("config.json", encoding="utf-8"))

activity = discord.Activity(type=discord.ActivityType.streaming, name=config["status"], url="https://twitch.tv/ninjajodxd")
bot = commands.Bot(help_command=None, command_prefix=config['prefix'], intents=discord.Intents.all(), activity=activity, guild_ids=[config["guild"]])


@bot.event
async def on_ready():
    print(f"{bot.user} is online!")


@bot.command(name="bal", description="Check Balance, LTC Only")
async def bal(ctx, ltc_addy: str):
    try:
        response = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{ltc_addy}/balance')
        if response.status_code == 200:
            data = response.json()
            balance = data['balance'] / 10**8
            t_balance = data['total_received'] / 10**8
            uc_balance = data['unconfirmed_balance'] / 10**8

            cg_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
            if cg_response.status_code == 200:
                usd_price = cg_response.json()['litecoin']['usd']

                usd_balance = usd_price * balance
                usd_t_balance = t_balance * usd_price
                usd_uc_balance = uc_balance * usd_price

                embed = discord.Embed(
                    title="LTC Balance",
                    description=f"**LTC Address: {ltc_addy}\n\n Total Balance: ${usd_balance}\n\n Unconfirmed Balance: ${usd_uc_balance}\n\n Total Received: ${usd_t_balance}**",
                    color=0x8B0000
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("Error: Unable to fetch LTC price.")
        else:
            await ctx.send("Error: Unable to fetch LTC balance.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(name="calc", description="Calculate simple maths")
async def calc(ctx, *, expression):
    try:
        result = eval(expression)
        embed = discord.Embed(
            title="Calculation",
            description=f"**Result: {result}**",
            color=0x8B0000
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command(name="client", description="Give client role")
async def client(ctx, member: discord.Member):
    if ctx.author.id in config['admin']:
        role = discord.utils.get(ctx.guild.roles, id=1219246101224493106)  # Replace with the role ID
        await member.add_roles(role)
        await ctx.send(f"{member.mention} Got Client Role")
    else:
        await ctx.send("You Are Not An Admin")


@bot.command(name="cp", description="Show LTC Rates")
async def cp(ctx):
    try:
        cg_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
        if cg_response.status_code == 200:
            usd_price = cg_response.json()['litecoin']['usd']
            embed = discord.Embed(
                title="Current Rates",
                description=f"USD Price: ${usd_price}",
                colour=0xFFC0CB
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error: Unable To Fetch Rates")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(name="ltc", description="Show LTC")
async def ltc(ctx):
    embed = discord.Embed(
        title="Payment Options",
        description="**LSGh2wYvBy2Gjfvo3wHyedKzbjisTUTuTr**",
        color=0x8B0000
    )
    embed.set_footer(text="Please Give Payment Screenshot")
    await ctx.send(embed=embed)


@bot.slash_command(name="drop", description="Drop products in DM")
async def drop(ctx: discord.ApplicationContext, member: discord.Member, quantity: int, product: str, price):
    if ctx.author.id in config['admin']:
        file_paths = {
            'Nitro Booster': config['boost_links'],
            '1m Nitro Tokens': config['nitro_tokens_1m'],
            '3m Nitro Tokens': config['nitro_tokens_3m'],
            'Nitro Basic': config['basic_links'],
            '1m Nitro ID': config['1m_id'],
            '3m Nitro ID': config['3m_id'],
            'MCFA': config['mcfa']
        }

        file_path = file_paths.get(product)

        if file_path:
            try:
                with open(file_path, "r+") as file:
                    lines = file.readlines()

                    if len(lines) < quantity:
                        await ctx.respond("Insufficient quantity available.")
                        return

                    sent_lines = lines[:quantity]
                    vouch_msg = f"+rep <@{config['vouch_id']}> {quantity} {product} In {price} | TY!"

                    embed = discord.Embed(
                        description=f"**__Thanks For Purchasing__\n\n\n`{vouch_msg}`\n\n- Don't Forget To [Vouch Us]({config['vouch_url']})**",
                        color=0xFFC0CB
                    )

                    message_content = '\n'.join(sent_lines)
                    embed.add_field(name=f"Your {product} is here", value=message_content)

                    await member.send(embed=embed)

                    confirmation_message = f"{quantity}x {product} Sent To {member.display_name}!"
                    await ctx.respond(confirmation_message)

                    # Remove sent lines from the appropriate link file
                    with open(file_path, 'w') as file:
                        file.writelines(lines[quantity:])

            except FileNotFoundError:
                await ctx.respond("File for the specified product not found.")
            except discord.Forbidden:
                await ctx.respond("Failed To DM")
        else:
            await ctx.respond("Invalid product specified.")
    else:
        await ctx.respond("You Are Not An Admin.")


@bot.slash_command(name="embed", description="Send an embed to a channel.")
async def embed(ctx: discord.ApplicationContext,
                channel: discord.Option(discord.TextChannel, "channel"),  # type: ignore
                title: discord.Option(str, "title", required=True),  # type: ignore
                description: discord.Option(str, "description", required=True)  # type: ignore
                ):
    if ctx.author.id in config['admin']:
        try:
            embed = discord.Embed(title=title, description=description, color=0x8B0000)
            await channel.send(embed=embed)
            await ctx.respond("Embed sent successfully!")
        except discord.Forbidden:
            await ctx.respond("I don't have permission to send messages in that channel.")
        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")
    else:
        await ctx.send("You are not authorized to use this command.")


@bot.slash_command(name="stock", description="Show available stock")
async def stock(ctx: discord.ApplicationContext):
    try:
        onemtkn = len(open(config['nitro_tokens_1m'], "r").readlines())
        threemtkn = len(open(config['nitro_tokens_3m'], "r").readlines())
        onemid = len(open(config['1m_id'], "r").readlines())
        threemid = len(open(config['3m_id'], "r").readlines())
        nitbst = len(open(config['boost_links'], "r").readlines())
        ntrbsc = len(open(config['basic_links'], "r").readlines())
        mcfa = len(open(config['mcfa'], "r").readlines())

        message = discord.Embed(
            title="Available Stock",
            description="Here is the current available stock:",
            color=0x8B0000
        )
        message.add_field(name="1 Month Nitro Tokens", value=onemtkn, inline=False)
        message.add_field(name="3 Month Nitro Tokens", value=threemtkn, inline=False)
        message.add_field(name="1 Month Nitro IDs", value=onemid, inline=False)
        message.add_field(name="3 Month Nitro IDs", value=threemid, inline=False)
        message.add_field(name="Nitro Boost Links", value=nitbst, inline=False)
        message.add_field(name="Nitro Basic Links", value=ntrbsc, inline=False)
        message.add_field(name="MCFA", value=mcfa, inline=False)

        await ctx.respond(embed=message)
    except Exception as e:
        await ctx.respond(f"An error occurred: {e}")


@bot.slash_command(name="restock", description="Restock a product")
async def restock(ctx: discord.ApplicationContext, code: str, product: str):
    if ctx.author.id in config['admin']:
        valid_products = ['Nitro Booster', 'Nitro Basic', '1m Nitro Tokens', '3m Nitro Tokens', '1m Nitro ID', '3m Nitro ID', 'MCFA']

        if product not in valid_products:
            return await ctx.respond("Product Not Found")

        file = None
        if product == 'Nitro Booster':
            file = config['boost_links']
        elif product == 'Nitro Basic':
            file = config['basic_links']
        elif product == '1m Nitro Tokens':
            file = config['nitro_tokens_1m']
        elif product == '3m Nitro Tokens':
            file = config['nitro_tokens_3m']
        elif product == '1m Nitro ID':
            file = config['1m_id']
        elif product == '3m Nitro ID':
            file = config['3m_id']
        elif product == 'MCFA':
            file = config['mcfa']

        if file is None:
            return await ctx.respond("Invalid Product")

        try:
            # Extract code from Paste.ee link
            code = code.replace("https://paste.ee/p/", "")

            # Retrieve stock information from Paste.ee
            temp_stock = requests.get(f"https://paste.ee/d/{code}", headers={"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"}).text

            # Write to the specified file
            with open(file, "a", encoding="utf-8") as f:
                f.write(f"{temp_stock}\n")

            lst = temp_stock.split("\n")
            embed = discord.Embed(
                title="Success",
                description=f"Successfully added {len(lst)} {product} to stock",
                color=0x8B0000
            )
            await ctx.respond(embed=embed)
        except Exception as e:
            await ctx.respond(f"An error occurred: {e}")
    else:
        await ctx.respond("You Are Not An Admin")


@bot.slash_command(name="addadmin", description="Add Admin To Bot")
async def addadmin(ctx: discord.ApplicationContext, member: discord.Member):
    if ctx.author.id in config['owner']:
        config["admin"].append(member.id)
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

        await ctx.respond(embed=discord.Embed(title="**Success**", description=f"Successfully Added {member.mention} As Admin", color=0xFFC0CB))
    else:
        await ctx.respond("You Are Not The Owner Nigga!")


@bot.command(name="paypal", description="Show PayPal details")
async def paypal(ctx):
    try:
        embed = discord.Embed(
            title="amogusdripmadrip@gmail.com",
            description="friends and family\nno notes\nONLY BALANCE\nrecord when sending\ndont follow rules = no item/exchange & no refund",
            color=0x8B0000
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        
        
        
@bot.command(name="help", description="Show available commands")
async def help(ctx):
    embed = discord.Embed(
        title="Cute Fire Bot Help",
        description="Here are the available commands:",
        color=0x8B0000
    )

    # Add command descriptions
    embed.add_field(name=f"{config['prefix']}bal [ltc_addy]", value="Check Balance, LTC Only", inline=False)
    embed.add_field(name=f"{config['prefix']}calc [expression]", value="Calculate simple maths", inline=False)
    embed.add_field(name=f"{config['prefix']}client [member]", value="Give client role", inline=False)
    embed.add_field(name=f"{config['prefix']}cp", value="Show LTC Price", inline=False)
    embed.add_field(name=f"{config['prefix']}ltc", value="Show LTC", inline=False)
    embed.add_field(name=f"{config['prefix']}drop [member] [quantity] [product] [price]", value="Drop products in DM", inline=False)
    embed.add_field(name=f"{config['prefix']}embed [channel] [title] [description]", value="Send an embed to a channel", inline=False)
    embed.add_field(name=f"{config['prefix']}stock", value="Show available stock", inline=False)
    embed.add_field(name=f"{config['prefix']}restock [Paste.ee link] [product]", value="Restock a product", inline=False)
    embed.add_field(name=f"{config['prefix']}addadmin [member]", value="Add Admin To Bot", inline=False)
    embed.add_field(name=f"{config['prefix']}paypal", value="Show Paypal", inline=False)

    await ctx.send(embed=embed)



bot.run(config['token'])
