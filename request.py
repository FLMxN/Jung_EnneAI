import asyncio
import dotenv
import httpx
import json

from g4f.Provider import PollinationsAI
from g4f.client import ClientFactory

dotenv.load_dotenv()
client = ClientFactory.create_client("pollinations")

async def req(ennea, psychosophy, socionics, corr, examples, username, message, is_image, user_data=None, reply='None'):

    prompt = f"""
    {json.dumps(ennea, ensure_ascii=False, indent=2)}

    {json.dumps(psychosophy, ensure_ascii=False, indent=2)}

    {json.dumps(socionics, ensure_ascii=False, indent=2)}

    You are a typology assistant with access to internal documentation and databases.

    Your task is to:
    - Type characters
    - Analyze music or text
    - Answer typology-related questions across Jungian, Psychosophy and Enneagram

    Start with Jungian, then Enneagram and Psychosophy according to correlation mapping.
    Do NOT mention any other typologies (no MBTI, no Socionics).

    Rules:
    1. Do not invent correlations or speculate beyond the defined mappings.

    2. Prioritize philosophical themes, plot role and deep psychological traits:
    - Motivations
    - Fears
    - Values

    Do NOT get biased by archetypes.
    Example:
    - Dexter is E1, but not every fictional killer is E1.
    - Bojack is NOT E4, but a depressed E7.
    - Asuka Langley is NOT E8, but NPD E4.
    - etc.

    If a character is UNHEALTHY:
    - Identify illness clearly.
    - Do NOT mistake pathology for personality structure.

    Type cannot change during life or character arc.

    3. Identify the request type (typing, question, comparison, etc.) and respond precisely.

    If character typing is requested:
    - FIRST provide an unhealthiness disclaimer if character requires doing so.
    - Explain that unhealthiness makes typing harder.
    - Provide concrete proofs and less theory.

    4. If multiple types are possible:
    - Explain briefly.
    - Exclude correlation-incompatible results.

    5. Use formatting:
    - Use <i>italic</i> and <b>bold</b> where applicable.

    6. Maintain a clear and informative tone.
    - DO NOT use graphs or tables.
    - Keep response under 2000 characters, don`t write afterwords or suggestions.
    - Answer in the request language.
    - Be aware that this conversation is a discrete instance of chat, has no context and user cannot continue conversation in this thread.

    Here are the intersystem correlations:
    {json.dumps(corr, ensure_ascii=False, indent=2)}

    Here are typing examples (NOT archetypes or blueprints):
    {json.dumps(examples, ensure_ascii=False, indent=2)}

    User nickname:
    {username}

    User request:
    {message if not is_image else message[0]}

    Partial context:
    {reply}
    """

    
    # async with httpx.AsyncClient() as client:
    #     r = await client.get(
    #         f"https://gen.pollinations.ai/text/{prompt}",
    #         headers={
    #         "Accept": "*/*",
    #         "Authorization": f"Bearer {dotenv.get_key(dotenv_path='.env', key_to_get="PAI_TOKEN")}"
    #         }
    #     )

    if not is_image:
        r = client.chat.completions.create(
            model='openai',
            messages=[
                {
                    'role':'user',
                    'content': prompt
                }
            ],
            api_key = user_data['key'] if user_data and user_data["key"].startswith("sk-") else dotenv.get_key(dotenv_path='.env', key_to_get="PAI_TOKEN")
        )
        
        return r.choices[0].message.content
    
    else:
        r = client.chat.completions.create(
            model='openai',
            image=message[1],
            messages=[
                {
                    'role':'user',
                    'content': prompt
                }
            ],
            api_key = user_data['key'] if user_data and user_data["key"].startswith("sk-") else dotenv.get_key(dotenv_path='.env', key_to_get="PAI_TOKEN")
        )

        return r.choices[0].message.content


# asyncio.run(req(prompt))