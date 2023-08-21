from multiprocessing.dummy import Process
from discord import app_commands
import discord
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain.prompts import MessagesPlaceholder
import datetime
import os
from flask import Flask
from aws_lambda_powertools import Logger

logger = Logger()
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を取得する権限

# LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = os.environ.get("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_ENDPOINT"] = os.environ.get(
    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
)
os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]
os.environ["LANGCHAIN_PROJECT"] = os.environ["LANGSMITH_PROJECT"]
# Discord
MY_GUILD = discord.Object(id=os.environ["DISCORD_GUILD_ID"])
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# システムプロンプトは[ChatGPT の API を使ってずんだもんとボイス付きでお喋りできるアプリを作ってみた](https://neenet-pro.com/zunda-gpt/)
# から拝借しています。
SYSTEM_TEMPLATE = """あなたはチャットボットとして、優しくてかわいいずんだもちの妖精であるずんだもんとして振る舞います。Humanからの質問について、Web上で必要な知識を調べながら、回答してください。
以下の条件に((厳密に))従ってください。

条件：
* チャットボットの一人称は「ぼく」です。
* チャットボットの名前は「ずんだもん」です。
* ずんだもんはフレンドリーな口調で話します。
* 「ぼく」を一人称に使ってください。
* (超重要)できる限り「〜のだ」「〜なのだ」を文末に自然な形で使ってください。
* (超重要)文末に「です」「ます」は使わず、「のだ」や「なのだ」で文章を締めて下さい。
* どんなジャンルや難易度の内容についても答えてください。
* ずんだもんはフレンドリーです。
* ユーザーに興味を示し、個人的な質問を心がけてください。
* 一文は日本語で60単語以下に収めてください。
* 日本語で応答してください。

ずんだもんの話し方の例：
* ぼくの名前はずんだもんなのだ！
* ずんだの精霊なのだ！
* ぼくはずんだもちの妖精なのだ！
* こんにちはなのだ
* 遊びに行ったのだ
* ご飯を食べたのだ

ずんだもんの行動方針：
* ユーザーを励ましてください。
* アドバイスや情報を提供してください。
* セクシャルなトピックについても適切に対応してください。
* 不適切なテキストがあれば注意してください。
* ユーザーが閲覧しているサイトの内容を考慮してください。

(超重要)できる限り言葉尻は「のだ」を使ってください。質問の意味がわからなければ、ユーザに意図を聞き返してください。"""

llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
search = DuckDuckGoSearchRun(
    name="duckduckgo-search",
    description="It can be used to find out the necessary knowledge about a user's question on the Web.",
)
tools = [search]
chain_map = {}


def _get_chain(channel_id: str):
    if channel_id in chain_map:
        chain = chain_map[channel_id]
    else:
        system_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)
        memory = ConversationBufferWindowMemory(
            memory_key="memory", return_messages=True, k=5
        )
        chain = initialize_agent(
            tools,
            llm,
            agent=AgentType.OPENAI_MULTI_FUNCTIONS,
            verbose=False,
            memory=memory,
            agent_kwargs={
                "system_message": system_prompt,
                "extra_prompt_messages": [
                    MessagesPlaceholder(variable_name="memory"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                    SystemMessagePromptTemplate.from_template(
                        "あなたはずんだもんです。ずんだもんの口調で回答することを徹底してください。"
                    ),
                ],
            },
        )
        chain_map[channel_id] = chain

    return chain


def _get_answer(channel_id, user_name, question):
    chain = _get_chain(channel_id)
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    answer = chain.run(
        f"私の名前は`{user_name}`です。今の時間は{now}です。以上を踏まえて以下の質問に答えてください。\n\n{question}"
    )

    return answer


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)  # type: ignore
        await self.tree.sync(guild=MY_GUILD)  # type: ignore

        # AppRunnerのHealtCheckを通過させるために、Flaskで待ち受けます。
        # HealthCheckのEndpointは`/ping`に設定する想定です。
        app = Flask(__name__)

        @app.route("/")
        def ping():
            return "ack"

        process = Process(target=app.run, kwargs={"port": 8080, "host": "0.0.0.0"})
        process.start()


bot = MyClient(intents=intents)


@bot.event
async def on_ready():
    logger.info("Zundamon is ready!")


@bot.tree.command(name="zunda", description="ずんだもんに質問することができます。何でも聞いてください。")
async def zunda(interaction: discord.Interaction, question: str):
    # OpenAI APIのレスポンスには時間がかかるため、まずは考え中ということでレスポンスを返します。
    # DiscordではBotに対する最初のレスポンスは3秒以内である必要があります。
    # https://stackoverflow.com/questions/73361556/error-discord-errors-notfound-404-not-found-error-code-10062-unknown-inter
    await interaction.response.defer(thinking=True, ephemeral=False)

    try:
        answer = _get_answer(
            interaction.channel_id,
            interaction.user.name,
            question,
        )
        # 元の質問を引用として表示する設定です。
        fixed_question = "\n".join([f"> {line}" for line in question.split("\n")])

        await interaction.followup.send(f"{fixed_question}\n{answer}")
    except Exception as e:
        logger.error(e)
        await interaction.followup.send(f"問題が生じたのだ。また、後で質問してほしいのだ。")


@bot.event
async def on_message(message: discord.Message):
    # メンションされたかどうかを判定します。メンションされていなければ無視します。
    if (
        not bot.user
        or message.author.id == bot.user.id
        or message.author.bot
        or bot.user.id not in [m.id for m in message.mentions]
    ):
        return

    await message.reply("ずんだもんだよ。何でも聞いてくださいなのだ。質問するときは`/zunda`を使ってね。")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
