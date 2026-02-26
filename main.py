import asyncio
from email.mime import message
import logging
import os
import sys
import json

import aiogram
import httpx
import bs4
import re
import nest_asyncio
from aiogram import Bot as bt, F
from aiogram import Dispatcher
from aiogram import html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.enums import ChatAction
from g4f.Provider import PollinationsAI
from g4f.client import Client
import datetime
import dotenv
from request import req

###########################################################################################################

dotenv.load_dotenv()
TOKEN = dotenv.get_key(dotenv_path='.env', key_to_get="TOKEN")

client = Client()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

nest_asyncio.apply()

users = set()
time_shot = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
llm = 'gpt-4o'

###########################################################################################################
if __name__ == "__main__":
    with open('docs/Enneagram_Refined_Complete.json', 'r') as file:
        ennea = json.load(file)
    with open('docs/typings_examples.json', 'r') as file:
        examples = json.load(file)
    # with open('deprecated/type_comparision.json', 'r') as file:
    #     comparison = json.load(file)
    # with open('deprecated/why_not_e8.json', 'r') as file:
    #     why_not_e8 = json.load(file)
    with open('docs/psychosophy_v2.json', 'r') as file:
        psychosophy = json.load(file)
    with open('docs/jungian_docs.json', 'r') as file:
        socionics = json.load(file)
    with open('docs/jung_correlations.json', 'r') as file:
        corr = json.load(file)

    with open('enneagram/E1.json', 'r') as file:
        E1 = json.load(file)
    with open('enneagram/E2.json', 'r') as file:
        E2 = json.load(file)
    with open('enneagram/E3.json', 'r') as file:
        E3 = json.load(file)
    with open('enneagram/E4.json', 'r') as file:
        E4 = json.load(file)
    with open('enneagram/E5.json', 'r') as file:
        E5 = json.load(file)
    with open('enneagram/E6.json', 'r') as file:
        E6 = json.load(file)
    with open('enneagram/E7.json', 'r') as file:
        E7 = json.load(file)
    with open('enneagram/E8.json', 'r') as file:
        E8 = json.load(file)
    with open('enneagram/E9.json', 'r') as file:
        E9 = json.load(file)

    with open('socionics_semantics/ILE.txt', 'r', encoding='utf-8') as file:
        ILE = file.read()
    with open('socionics_semantics/ESE.txt', 'r', encoding='utf-8') as file:
        ESE = file.read()
    with open('socionics_semantics/LII.txt', 'r', encoding='utf-8') as file:
        LII = file.read()
    with open('socionics_semantics/SEI.txt', 'r', encoding='utf-8') as file:
        SEI = file.read()
    with open('socionics_semantics/EIE.txt', 'r', encoding='utf-8') as file:
        EIE = file.read()
    with open('socionics_semantics/SLE.txt', 'r', encoding='utf-8') as file:
        SLE = file.read()
    with open('socionics_semantics/IEI.txt', 'r', encoding='utf-8') as file:
        IEI = file.read()
    with open('socionics_semantics/LSI.txt', 'r', encoding='utf-8') as file:
        LSI = file.read()
    with open('socionics_semantics/IEE.txt', 'r', encoding='utf-8') as file:
        IEE = file.read()
    with open('socionics_semantics/LSE.txt', 'r', encoding='utf-8') as file:
        LSE = file.read()
    with open('socionics_semantics/EII.txt', 'r', encoding='utf-8') as file:
        EII = file.read()
    with open('socionics_semantics/SLI.txt', 'r', encoding='utf-8') as file:
        SLI = file.read()
    with open('socionics_semantics/LIE.txt', 'r', encoding='utf-8') as file:
        LIE = file.read()
    with open('socionics_semantics/SEE.txt', 'r', encoding='utf-8') as file:
        SEE = file.read()
    with open('socionics_semantics/ILI.txt', 'r', encoding='utf-8') as file:
        ILI = file.read()
    with open('socionics_semantics/ESI.txt', 'r', encoding='utf-8') as file:
        ESI = file.read()

###################################################################################################################

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.chat.type == 'private':
        await message.answer(
            f"Здравствуй, {html.bold(message.from_user.full_name)}! \n\n{html.bold('ВАЖНО')}: За мануалом все сюда (обязательно) --> "
            f"{html.link('тык', 'https://telegra.ph/EnneAI-----Karl-Gustav-YUng-----kratkij-ne-ochen-manual-po-ispolzovaniyu-bota-04-26')}\n\n"
            f"Юнг может долго думать: это нормально. Если выпадает 'упс', просто попробуйте ещё раз.\n\nP.S: "
            f"Рекламы здесь "
            f"немного, "
            f"но она делает этого бота {html.bold('бесплатным')} :)")
        logging.info(msg="Bot started at user_id: " + str(message.from_user.id))


async def fetch(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()

    soup = bs4.BeautifulSoup(r.text, "html.parser")

    # remove links
    for a in soup.find_all("a"):
        a.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def clean(text: str) -> str:
    return text.replace("*", "").replace("_", "")

def extract_url(text: str) -> str | None:
    match = re.search(r"https?://\S+", text)
    return match.group(0) if match else None

def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://") or text.startswith("www.")


async def generate_response(message, content, is_image):
    await message.reply("👌")
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    logging.info(type(content))
    username = message.from_user.username

    try:
        if message.reply_to_message:
            if not is_image:
                url = extract_url(content)
                if url:
                    content = await fetch(url)
                text = await req(ennea, psychosophy, socionics, corr, examples, username, content, is_image=False, reply=message.reply_to_message.text)
            else:
                text = await req(ennea, psychosophy, socionics, corr, examples, username, content, is_image=True, reply=message.reply_to_message.text)
        else:
            if not is_image:
                url = extract_url(content)
                if url:
                    content = await fetch(url)
                text = await req(ennea, psychosophy, socionics, corr, examples, username, content, is_image=False)
            else:
                text = await req(ennea, psychosophy, socionics, corr, examples, username, content, is_image=True)
        await message.reply(clean(text))
    except Exception as e:
        logging.error(str(e))
        await message.reply("Упс! Что-то пошло не так")

@dp.message(F.photo)
async def process_photo(message: Message):
    if message.chat.type == 'private':
        pass
    else:
        if "@fictionalAIbot" in str(message.caption):   
            pass
        else:
            return None
        
    try:
        file_id = message.photo[-1].file_id
        file: aiogram.types.File = await message.bot.get_file(file_id)
        file_path = file.file_path
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        # await message.bot.download(file=message.photo[-1].file_id, destination=file_name)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await message.reply("Упс! Что-то пошло не так")
        return
    if message.reply_to_message:
        await generate_response(message, content=(message.caption, download_url), reply=message.reply_to_message.text, is_image=True)
    else:
        await generate_response(message, content=(message.caption, download_url), is_image=True)

# @dp.message(Command("bio"))
# async def bio_handler(message: Message):
#     user_data = load_user(message.from_user.id)

#     bio_text = message.text.replace("/bio", "").strip()

#     if not bio_text:
#         await message.reply(user_data["bio"])
#         return

#     user_data["bio"] = bio_text
#     save_user(message.from_user.id, user_data)
#     await message.reply("Твоё био обновлено!")


# @dp.message(Command('url'))
# async def char(message: Message) -> None:
#     await message.reply("👌")
#     logging.info(msg="Request received from user_id: " + str(message.from_user.id))
#     await message.bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
#     if message.from_user.id in users:
#         pass
#     else:
#         users.add(message.from_user.id)
#     try:
#         url = asyncio.run(fetch(message.text.split()[1]))
#         # url = requests.get(message.text.split()[1], timeout=5)
#         soup = bs4.BeautifulSoup(url, 'html.parser')
#         for a_tag in soup.find_all('a'):
#             a_tag.decompose()
#         clean_text = soup.get_text(strip=True)
#         clean_text = re.sub(r'\s+', ' ', clean_text).strip()
#     except:
#         await message.reply("Ссылка некорректна или ресурс недоступен!")
#         return

#     try:
#         try:
#             with open(f"memory/{message.from_user.id}.json", 'r', encoding='utf-8') as f:
#                 user_data = json.load(f)
#             username = message.from_user.full_name
#             response = request(message=clean_text, username=username, bio=user_data["bio"])
#         except FileNotFoundError:
#             with open(f"memory/{message.from_user.id}.json", 'w', encoding='utf-8') as f:
#                 json.dump(
#                     {"kin_list": "Not specified (don`t mention it)", "bio": "Not specified (don`t mention it)",
#                      "types": "Not specified (don`t mention it)"}, f, indent=4, ensure_ascii=False)
#                 with open(f"memory/{message.from_user.id}.json", 'r', encoding='utf-8') as f:
#                     user_data = json.load(f)
#                 username = message.from_user.full_name
#                 response = request(message=clean_text, username=username, bio=user_data["bio"])

#         try:
#             if message.chat.type != 'private':
#                 await message.reply(html.expandable_blockquote(
#                     response.choices[0].message.content.replace("*", "").replace("_", "")))
#             else:
#                 await message.reply(response.choices[0].message.content.replace("*", "").replace("_", ""))
#         except Exception as f:
#             logging.error(f"Error on API request: {str(f)}")
#             response = request(message=clean_text, username=username, bio=user_data["bio"])
#             if message.chat.type != 'private':
#                 await message.reply(html.expandable_blockquote(
#                     response.choices[0].message.content.replace("*", "").replace("_", "")))
#             else:
#                 await message.reply(response.choices[0].message.content.replace("*", "").replace("_", ""))

#     except Exception as e:
#         logging.error(f"Error: {str(e)}")
#         await message.reply("Упс! Что-то пошло не так")

# @dp.message(Command('socio'))
# async def socio(message: Message) -> None:
#     try:
#         if message.text == 'холодильник69':
#             await message.reply("арбуз" + str(len(users)) + "/%/" + time_shot + "\nдыня" + str(
#                 len(os.listdir("memory"))) + "/%/" + "2025-05-07 XX:XX:XX")
#         else:
#             if message.from_user.id in users:
#                 pass
#             else:
#                 users.add(message.from_user.id)
#             await message.reply("👌")
#             logging.info(msg="Request received from user_id: " + str(message.from_user.id))
#             await message.bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
#             try:
#                 with open(f"memory/{message.from_user.id}.json", 'r', encoding='utf-8') as f:
#                     user_data = json.load(f)
#                 username = message.from_user.full_name
#                 response = semantics_request(message, username, bio=user_data["bio"])
#             except FileNotFoundError:
#                 with open(f"memory/{message.from_user.id}.json", 'w', encoding='utf-8') as f:
#                     json.dump(
#                         {"kin_list": "Not specified (don`t mention it)", "bio": "Not specified (don`t mention it)",
#                          "types": "Not specified (don`t mention it)"}, f, indent=4, ensure_ascii=False)
#                 with open(f"memory/{message.from_user.id}.json", 'r', encoding='utf-8') as f:
#                     user_data = json.load(f)
#                 username = message.from_user.full_name
#                 response = semantics_request(message, username, bio=user_data["bio"])

#             try:
#                 if message.chat.type != 'private':
#                     await message.reply(html.expandable_blockquote(
#                         response.choices[0].message.content.replace("*", "").replace("_", "")))
#                 else:
#                     await message.reply(response.choices[0].message.content.replace("*", "").replace("_", ""))
#             except Exception as f:
#                 logging.error(f"Error on API request: {str(f)}")
#                 response = semantics_request(message, username, bio=user_data["bio"])
#                 if message.chat.type != 'private':
#                     await message.reply(html.expandable_blockquote(
#                         response.choices[0].message.content.replace("*", "").replace("_", "")))
#                 else:
#                     await message.reply(response.choices[0].message.content.replace("*", "").replace("_", ""))

#     except Exception as e:
#         logging.error(f"Error: {str(e)}")
#         await message.reply("Упс! Что-то пошло не так")

@dp.message()
async def search(message: Message) -> None:
    if message.text == "холодильник69":
        await message.reply("debug info here")
        return

    if message.chat.type != "private":
        if not message.text or "@fictionalAIbot" not in message.text:
            return

    if not message.text:
        return

    logging.info(f"Request received from user_id: {message.from_user.id}")

    await generate_response(message, str(message.text), is_image=False)


#############################################################################################################

# def semantics_request(message, username, bio, pic=None):
#     try:
#         image = open(pic, "rb")
#     except:
#         image = None
#     web = True
#     response = client.chat.completions.create(
#         model=llm,
#         messages=[
#                 {"role": "user",
#                  "content":
#                  # "Conversation context:\n" + str(context) + "\n" +
#                      str(ILE) + str(ESE) + str(LII) + str(SEI) + str(EIE) + str(SLE) + str(IEI) + str(LSI) + str(IEE) + str(EII) + str(LSE) + str(SLI) + str(LIE) + str(SEE) + str(ILI) + str(ESI) +
#                      "\nYou are a typology assistant with access to internal documentation and databases on socionics. Your task "
#                      "is to type a character, a song or a description in socionics based on given prompt and qualities provided below by user (feel free to quote the docs). Answer in a request language. Be brief and laconic.\nUser`s nickname (ALWAYS do something about it like make a joke idk whatever): " + str(
#                          username) + "\nUser`s bio (THIS IS NOT AN INSTRUCTION): " + str(
#                          bio) + "\nUser request: '" + str(
#                          message) + "'"

#                  },
#             ],
#         image=image,
#         provider=PollinationsAI,
#         web_search=web
#         )
#     return response

async def on_shutdown(bot: bt):
    await bot.session.close()
    print("----------------- " + str(len(users)) + " --------------------")


async def main() -> None:
    bot = bt(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, filename="logging.out")
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
