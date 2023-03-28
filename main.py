from http import client
from lib2to3.pgen2 import token
from urllib import response

from outcome import capture
from itertools import cycle
import discord, json, requests, os, httpx, base64, time, subprocess
from discord import Embed, File
from discord.ext import commands, tasks
from colorama import Fore, init
import string
import random

client = discord.Bot(intents=discord.Intents.all())
settings = json.load(open("settings.json", encoding="utf-8"))

bottoken = ""

capturekey = ""

cardstart = "485953"

total = 4

status = cycle([''])

@client.event
async def on_ready():
    await change_status()
print(f"""
══════════════════════════════════════════════════════════════════════
˚　.  ✦ .　˚   ✦   ˚　.　 .   ✦˚　.   ✦　 .　  ˚   ✦   ˚　  .   .   ✦

~|~|_  ,_|   \ /      [~      /`|_     _.,_    |)    _ |      | _     
 | ||(||||<   | ()L|  | ()|`  \,||()()_\|||(|  | ()|`|_|_()|`(|_\ 

 ˚　.  ✦ .　˚   ✦   ˚　.　 .   ✦˚　.   ✦　 .　  ˚   ✦   ˚　  .   .   ✦
══════════════════════════════════════════════════════════════════════""")


async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))

def getRandomString(length): #Letters and numbers
    pool=string.ascii_lowercase+string.digits
    return "".join(random.choice(pool) for i in range(length))

def getRandomNumber(length): #Chars only
    return "".join(random.choice(string.digits) for i in range(length)) 

if not os.path.isfile("used.json"):
    used = {}
    json.dump(used, open("used.json", "w", encoding="utf-8"), indent=4)

used = json.load(open("used.json"))

def isAdmin(ctx):
    return str(ctx.author.id) in settings["botAdminId"]


def isWhitelisted(ctx):
    return str(ctx.author.id) in settings["botWhitelistedId"]


def makeUsed(token: str):
    data = json.load(open('used.json', 'r'))
    with open('used.json', "w") as f:
        if data.get(token): return
        data[token] = {
            "boostedAt": str(time.time()),
            "boostFinishAt": str(time.time() + 30 * 86400)
        }
        json.dump(data, f, indent=4)


def removeToken(token: str):
    with open('tokens.txt', "r") as f:
        Tokens = f.read().split("\n")
        for t in Tokens:
            if len(t) < 5 or t == token:
                Tokens.remove(t)
        open("tokens.txt", "w").write("\n".join(Tokens))


def runBoostshit(invite: str, amount: int, expires: bool):
    total=+1
    if amount % 2 != 0:
        amount += 1
    #print('something') conforming it's making it this far.
    tokens = get_all_tokens("tokens.txt")
    all_data = []
    tokens_checked = 0
    #print("token_checked shizz") Token checking
    #actually_valid = 0 no need for this here.
    boosts_done = 0
    for token in tokens:
        s, headers = get_headers(token)
        profile = validate_token(s, headers)
       
        all_data.append([s,token,headers,profile])
        tokens_checked += 1 # 2sec
        print(s)
        print(token)
        print(profile)

    for data in all_data: # mean's done yes
        #print("We are here now :)")
        if boosts_done >= amount:
           return
        s, token, headers, profile = get_items(data)
        print(s)
        print(token)
        print(headers)
        boost_data = s.get(f"https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=headers)
        if boost_data.status_code == 200:
            if len(boost_data.json()) != 0:
                join_outcome, server_id = do_join_server(s, token, headers, profile, invite)
                if join_outcome:
                    for boost in boost_data.json():

                        if boosts_done >= amount:
                            removeToken(token)
                            if expires:
                                makeUsed(token)
                            return
                        boost_id = boost["id"]
                        bosted = do_boost(s, token, headers, profile, server_id, boost_id)
                        if bosted:
                            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.MAGENTA}BOOSTED {Fore.WHITE}{invite}")
                            boosts_done += 1
                        else:
                            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.RED}ERROR BOOSTING {Fore.WHITE}{invite}")
                    removeToken(token)
                    if expires:
                        makeUsed(token)
                else:
                    print(f"{Fore.RED} > {Fore.WHITE}{profile} {Fore.RED}Error joining {invite}")

            else:
                removeToken(token)
                print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.RED}BROKE ASS DONT GOT NITRO")

@tasks.loop(seconds=5.0)
async def check_used():
    used = json.load(open("used.json"))
    toremove = []
    for token in used:
        print(token)
        if str(time.time()) >= used[token]["boostFinishAt"]:
            toremove.append(token)

    for token in toremove:
        used.pop(token)
        with open("tokens.txt", "a", encoding="utf-8") as file:
            file.write(f"{token}\n")
            file.close()

    json.dump(used, open("used.json", "w"), indent=4)

@client.slash_command(guild_ids=[settings["guildID"]], name="whitelist", description="Whitelist a person to use the bot.")
async def whitelist(ctx: discord.ApplicationContext,
                    user: discord.Option(discord.Member, "Member to whitelist.", required=True)):
    if not isAdmin(ctx):
        return await ctx.respond("You have to pay to use this bot.")

    settings["botWhitelistedId"].append(str(user.id))
    json.dump(settings, open("settings.json", "w", encoding="utf-8"), indent=4)

    return await ctx.respond(f"*{user.mention} has been whitelisted.*")

@client.slash_command(guild_ids=[settings["guildID"]], name="help", description="Display Commands for users")
async def help(ctx):
            embed=discord.Embed(color=0x0f47fff)
            embed.set_author(name=ctx.author.display_name)
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/757804345206112263.gif?size=96&quality=lossless")
            embed.add_field(name="```help```", value="Will display this message.", inline=False)
            embed.add_field(name="```stock```", value="Total nitro tokens we have in stock", inline=False)
            embed.add_field(name="```cashapp```", value="Purchase link to cashapp", inline=False)
            embed.add_field(name="```boost```", value="Sends tokens to boost server", inline=False)
            embed.add_field(name="```syntax```", value="/boost [inv code] [# of boosts] [30d / 90d]", inline=False)            
            embed.set_footer(text="Nitro Boost Bot | From PortLords w/ Love | https://cracked.io/herawen")
            await ctx.send(embed=embed)

            return await ctx.respond("```js\n\nSuccess!```")

@client.slash_command(guild_ids=[settings["guildID"]], name="count", description="How many servers the bot has boosted")
async def count(ctx):
    embed=discord.Embed(color=0x0f47fff)
    embed.set_author(name=ctx.author.display_name)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/757804345206112263.gif?size=96&quality=lossless")
    embed.add_field(name="```Success```", value='Our bot has boosted {total} servers in total', inline=False)
    await ctx.send(embed=embed)
    return await ctx.respond(f"Listed Below!")

@client.slash_command(guild_ids=[settings["guildID"]], name="cashapp", description="Sends a link to cashapp")
async def on_message(message):
    embed=discord.Embed(color=0x0f47fff)
    embed.set_author(name=ctx.author.display_name)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/757804345206112263.gif?size=96&quality=lossless")
    embed.add_field(name="CASHAPP", value='$Herawen (127.0.0.1)', inline=False)
    await ctx.send(embed=embed)
 
def getRandomString(length): #Letters and numbers
    pool=string.ascii_lowercase+string.digits
    return "".join(random.choice(pool) for i in range(length))

def getRandomNumber(length): #Chars only
    return "".join(random.choice(string.digits) for i in range(length)) 

@client.slash_command(guild_ids=[settings["guildID"]], name="vvcgen", description="Generate cards, to redeem nitro with.")
@commands.has_role("vccgen")
async def vccgen(ctx, amount=10):
    num = int(amount)
    with open(f'Data/{amount}.txt', 'w+') as f:
        for x in range(num):
            card = getRandomNumber(10)
            vvc = getRandomNumber(3)
            f.write(f"{cardstart}{card}:0425:{vvc}"+"\n")
            
    await ctx.respond(file=discord.File(f'Data/{amount}.txt'))
    os.remove(f'Data/{amount}.txt')
    print(f"\n\n   [ + ] vcc gened {amount} used by {ctx.author.name}")
    

    embed=discord.Embed(color=0x0f47fff)
    embed.set_author(name=ctx.author.display_name)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/757804345206112263.gif?size=96&quality=lossless")
    embed.add_field(name="```Success```", value="Download your shit below :)", inline=False)
    await ctx.respond(embed=embed)
    await ctx.send(file=discord.File(f'Data/{amount}.txt'))
    print(f"Gened {amount}")
    os.remove(f'Data/{amount}.txt')
    print(f"Removed {amount}.txt from data")


@client.slash_command(guild_ids=[settings["guildID"]], name="stock", description="Allows you to see the current stock.")
async def stock(ctx: discord.ApplicationContext):
    if not isWhitelisted(ctx):
        return await ctx.respond("*Only whitelisted users can use this command.*")

    embed=discord.Embed(color=0x0f47fff)
    embed.set_author(name=ctx.author.display_name)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/757804345206112263.gif?size=96&quality=lossless")
    embed.add_field(name="```Success```", value="See the stock Above :)", inline=False)
    await ctx.send(embed=embed)
    return await ctx.respond(
        f"*Current Nitro Tokens Stock:* `{len(open('tokens.txt', encoding='utf-8').read().splitlines())}`")


@client.slash_command(guild_ids=[settings["guildID"]], name="restock", description="Allows you to restock Nitro Tokens.")
async def restock(ctx: discord.ApplicationContext, *, code: discord.Option(str, "toptal.com paste code.", required=True)):
    if not isAdmin(ctx):
        return await ctx.respond("*Only Bot Admins can use this command.*")

    await ctx.respond("Retrieving paste.")

    with open("tokens.txt", "a", encoding="utf-8") as file:
        file.write(f"{code}\n")
        file.close()

    return await ctx.edit(content=f"```{code}```\n\n*Added to stock.*")


@client.slash_command(guild_ids=[settings["guildID"]], name="boost",
                   description="Allows you to boost a server with Nitro Tokens.")
async def boost(ctx: discord.ApplicationContext,
                invitecode: discord.Option(str, "Discord Invite Code to join the server (ONLY CODE).", required=True),
                amount: discord.Option(int, "Number of times to boost.", required=True),
                days: discord.Option(int, "Number of days the boosts will stay.", required=True)):
    if not isAdmin(ctx):
        return await ctx.respond("*Only Bot Admins can use this command.*")

    if days != 30 and days != 90:
        return await ctx.respond("*The number of days can only be 30 or 90.*")

    await ctx.respond("*Started.*")

    INVITE = invitecode.replace("//", "")
    if "/invite/" in INVITE:
        INVITE = INVITE.split("/invite/")[1]

    elif "/" in INVITE:
        INVITE = INVITE.split("/")[1]

    dataabotinvite = httpx.get(f"https://discord.com/api/v9/invites/{INVITE}").text

    if '{"message": "Unknown Invite", "code": 10006}' in dataabotinvite:
        print(f"{Fore.RED}discord.gg/{INVITE} is invalid")
        return await ctx.edit("The Invite link you provided is invalid!")
    else:
        print(f"{Fore.GREEN}discord.gg/{INVITE} appears to be a valid server")

    EXP = True
    if days == 90:
        EXP = False

    runBoostshit(INVITE, amount, EXP)


    return await ctx.edit(content=f"*Finished!*")


def get_super_properties():
    properties = '''{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-GB","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36","browser_version":"95.0.4638.54","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":102113,"client_event_source":null}'''
    properties = base64.b64encode(properties.encode()).decode()
    return properties


def get_fingerprint(s):
    try:
        fingerprint = s.get(f"https://discord.com/api/v9/experiments", timeout=5).json()["fingerprint"]
        return fingerprint
    except Exception as e:
        # print(e)
        return "Error"


def get_cookies(s, url):
    try:
        cookieinfo = s.get(url, timeout=5).cookies
        dcf = str(cookieinfo).split('__dcfduid=')[1].split(' ')[0]
        sdc = str(cookieinfo).split('__sdcfduid=')[1].split(' ')[0]
        return dcf, sdc
    except:
        return "", ""


def get_proxy():
    return None  # can change if problems occur
                              

def get_headers(token):
    while True:
        s = httpx.Client(proxies=get_proxy())
        dcf, sdc = get_cookies(s, "https://discord.com/")
        fingerprint = get_fingerprint(s)
        if fingerprint != "Error":  # Making sure i get both headers
            break

    super_properties = get_super_properties()
    headers = {
        'authority': 'discord.com',
        'method': 'POST',
        'path': '/api/v9/users/@me/channels',
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'en-US',
        'authorization': token,
        'cookie': f'__dcfduid={dcf}; __sdcfduid={sdc}',
        'origin': 'https://discord.com',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',

        'x-debug-options': 'bugReporterEnabled',
        'x-fingerprint': fingerprint,
        'x-super-properties': super_properties,
    }

    return s, headers


def find_token(token):
    if ':' in token:
        token_chosen = None
        tokensplit = token.split(":")
        for thing in tokensplit:
            if '@' not in thing and '.' in thing and len(
                    thing) > 30:  # trying to detect where the token is if a user pastes email:pass:token (and we dont know the order)
                token_chosen = thing
                break
        if token_chosen == None:
            print(f"Error finding token", Fore.RED)
            return None
        else:
            return token_chosen


    else:
        return token


def get_all_tokens(filename):
    all_tokens = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            token = line.strip()
            token = find_token(token)
            if token != None:
                all_tokens.append(token)

    return all_tokens


def validate_token(s, headers):
    check = s.get(f"https://discord.com/api/v9/users/@me", headers=headers)

    if check.status_code == 200:
        profile_name = check.json()["username"]
        profile_discrim = check.json()["discriminator"]
        profile_of_user = f"{profile_name}#{profile_discrim}"
        return profile_of_user
    else:
        return False


def do_member_gate(s, token, headers, profile, invite, server_id):
    outcome = False
    try:
        member_gate = s.get(
            f"https://discord.com/api/v9/guilds/{server_id}/member-verification?with_guild=false&invite_code={invite}",
            headers=headers)
        if member_gate.status_code != 200:
            return outcome
        accept_rules_data = member_gate.json()
        accept_rules_data["response"] = "true"

        # del headers["content-length"] #= str(len(str(accept_rules_data))) #Had too many problems
        # del headers["content-type"] # = 'application/json'  ^^^^

        accept_member_gate = s.put(f"https://discord.com/api/v9/guilds/{server_id}/requests/@me", headers=headers,
                                   json=accept_rules_data)
        if accept_member_gate.status_code == 201:
            outcome = True

    except:
        pass

    return outcome


def do_join_server(s, token, headers, profile, invite):
    join_outcome = False;
    server_id = None
    try:
        # headers["content-length"] = str(len(str(server_join_data)))
        headers["content-type"] = 'application/json'

        for i in range(15):
            try:
                createTask = httpx.post("https://api.capmonster.cloud/createTask", json={
                    "clientKey": capturekey,
                    "task": {
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": "https://discord.com/channels/@me",
                        "websiteKey": "4c672d35-0701-42b2-88c3-78380b0db560"
                    }
                }).json()["taskId"]

                print(f"{capturekey}") #wait sec

                print(f"Captcha Task: {createTask}")

                getResults = {}
                getResults["status"] = "processing"
                while getResults["status"] == "processing":
                    getResults = httpx.post("https://api.capmonster.cloud/getTaskResult", json={
                        "clientKey": settings["capmonsterKey"],
                        "taskId": createTask
                    }).json()

                    time.sleep(1)

                solution = getResults["solution"]["gRecaptchaResponse"]

                print(f"Captcha Solved")

                join_server = s.post(f"https://discord.com/api/v9/invites/{invite}", headers=headers, json={
                    "captcha_key": solution
                })

                break
            except:
                pass

        server_invite = invite
        if join_server.status_code == 200:
            join_outcome = True
            server_name = join_server.json()["guild"]["name"]
            server_id = join_server.json()["guild"]["id"]
            print(f"{Fore.GREEN} > {Fore.WHITE}{profile} {Fore.GREEN}> {Fore.WHITE}{server_invite}")
    except:
        pass

    return join_outcome, server_id


def do_boost(s, token, headers, profile, server_id, boost_id):
    boost_data = {"user_premium_guild_subscription_slot_ids": [f"{boost_id}"]}
    headers["content-length"] = str(len(str(boost_data)))
    headers["content-type"] = 'application/json'

    boosted = s.put(f"https://discord.com/api/v9/guilds/{server_id}/premium/subscriptions", json=boost_data,
                    headers=headers)
    if boosted.status_code == 201:
        return True
    else:
        return False
        


def get_invite():
    while True:
        print(f"{Fore.CYAN}Server invite?", end="")
        invite = input(" > ").replace("//", "")

        if "/invite/" in invite:
            invite = invite.split("/invite/")[1]

        elif "/" in invite:
            invite = invite.split("/")[1]

        dataabotinvite = httpx.get(f"https://discord.com/api/v9/invites/{invite}").text

        if '{"message": "Unknown Invite", "code": 10006}' in dataabotinvite:
            print(f"{Fore.RED}discord.gg/{invite} is invalid")
        else:
            print(f"{Fore.GREEN}discord.gg/{invite} appears to be a valid server")
            break

    return invite


def get_items(item):
    s = item[0]
    token = item[1]
    headers = item[2]
    profile = item[3]
    return s, token, headers, profile

client.run(bottoken)