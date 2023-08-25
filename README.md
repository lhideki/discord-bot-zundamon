# discord-bot-zundamon

This is a Discord bot that uses OpenAI's API to answer questions in the style of "zundamon" and incorporates knowledge from web searches through integration with DuckDuckGo.

## Architecture

Start `discord.py` on `AWS AppRunner`. Manage it with `AWS Copilot`.

## ADR(Architecture Decision Record)

### Placement of pyproject.toml

If you open the project root directly in VS Code, you can select the Python execution environment with the default settings of VS Code because pyproject.toml is in the root.

### Reasons for choosing AWS AppRunner instead of AWS Lambda

The following article explains how to create a Discord bot using AWS Lambda:

-   [aws-lambda-discord-bot](https://github.com/ker0olos/aws-lambda-discord-bot)

This method uses Discord's REST API directly, so it does not use discord.py. It is possible to use discord.py with AWS Lambda, but since discord.py assumes Python's asyncio, individual efforts are required in the AWS Lambda Handler.

Also, according to Discord's specifications, the initial response of the bot needs to be within 3 seconds (this is not official information). In this implementation, LangChain is used, and due to the package size of LangChain, it is necessary to run AWS Lambda on Docker. Cold starts on Lambda on Docker can take time, so it may not be possible to comply with the 3-second response limit.

It is possible to comply with the above limit by separating the Lambda for the initial response and the follow-up message, but this would make the implementation more complex. Therefore, AWS AppRunner, which does not have cold start issues, was chosen.

### Notes on combining discord.py and AWS AppRunner

AWS AppRunner requires a response at the URL specified during deployment for HealthCheck. However, discord.py does not wait for external requests in the form of a web server, so a separate web server is required for HealthCheck.

In this implementation, a Flask server is started asynchronously in the hook when the discord.py client is started to listen for HealthCheck.

## Folder structure

-   app
-   docs
-   experiments
-   notebooks

## Prepare for development

```bash
git clone [This repository]
poetry install
```

## Deploy Procedure

1. Create Bot application on Discord Developer Portal.
2. Register Bot for Discord server.
3. Setting up SSM Parameter
4. Deploy

### Create Bot application on Discord Developer Portal.

Create a Bot with reference to the following.

-   https://discordpy.readthedocs.io/ja/latest/discord.html

### Register Bot for Discord server.

Register the Bot on the Discord server with the following reference.

-   https://discordpy.readthedocs.io/ja/latest/discord.html

### Setting up SSM Parameter

Manually set up the following SSM Parameter.

-   /discord-bot-zundamon/OpenAiApiKey
    -   OpenAI's ApiKey.
-   /discord-bot-zundamon/LangSmith/ApiKey
    -   LangSmith's ApiKey. If you do not use LangSmith, you do not need to set this.
-   /discord-bot-zundamon/LangSmith/Project
    -   LangSmith's Project name。If you do not use LangSmith, you do not need to set this.
-   /discord-bot-zundamon/Discord/BotToken
    -   Discord's Bot Token.
-   /discord-bot-zundamon/Discord/GuildId
    -   Id of the Guild (server) where the Discord Bot is set up.

### Deploy

```bash
cd app
copilot deploy
```

## Notes.

-   The server administrator is not affected by the permission restrictions of the slash command. For this reason, a separate user must be prepared for operation checks. Note that only slash commands can be restricted by the Discrod function.
-   The Discord function cannot restrict mentions to bots.
-   If you do not use discord.py, slash commands must be registered in advance by calling the API directly.
-   There are two types of Discord bot commands, and the slash command is currently recommended. The slash command is called the Application Command in SDK terms.
-   The Bot's initial response should take no more than 3 seconds.
    -   https://stackoverflow.com/questions/73361556/error-discord-errors-notfound-404-not-found-error-code-10062-unknown-inter

## References

-   [Discord - DEVELOPER PORTAL](https://discord.com/developers/applications)
-   [discord.py](https://discordpy.readthedocs.io/ja/latest/index.html)
-   [aws-lambda-discord-bot](https://github.com/ker0olos/aws-lambda-discord-bot)
-   [ChatGPT の API を使ってずんだもんとボイス付きでお喋りできるアプリを作ってみた](https://neenet-pro.com/zunda-gpt/)
