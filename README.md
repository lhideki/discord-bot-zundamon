# discord-bot-zundamon

OpenAI の API を利用し、ずんだもん風で質問応答する Discord 用の Bot です。DuckDuckGo と連携し、Web 検索した知識を利用した回答をします。

## アーキテクチャ概要

discord.py を AWS AppRunner で起動します。AppRunner は AWS Copilot で管理します。

## ADR

### pyproject.toml の配置場所

プロジェクトのルートをそのまま VS Code で開いた場合に、pyproject.toml がルートにあると VS Code のデフォルトの設定のままで Python の実効環境が選択できます。

### AWS Lambda ではなく AWS AppRunner を選択している理由

AWS Lambda で Discrod のボットを作成する方法は、以下で解説されています。

-   [aws-lambda-discord-bot](https://github.com/ker0olos/aws-lambda-discord-bot)

この方法では Discord の REST API を直接利用するため、discord.py は利用していません。AWS Lambda でも discord.py を利用することができると思われますが、discord.py は Python の asyncio を前提としているため、AWS Lambda の Handler で個別の工夫が必要だと考えられます。

また、Discord の仕様ではボットの初回応答は(公式情報ではありませんが)3 秒以内とする必要があるようです。本実装では LangChain を利用しており、LangChain のパッケージサイズの問題より、AWS Lambda を On Docker で動かす必要があります。Lambda on Docker のコールドスタートは時間がかかるため、3 秒以内の応答制限を守れないことがありました。

初回応答用とフォローアップメッセージ用の Lambda を別とすることで、上記の制限内で対応することも可能ですが、実装が複雑になることからコールドスタートの問題が発生しない AWS AppRunner を選択しています。

### discord.py と AWS AppRunner を組み合わせる際の注意事項

AWS AppRunner は HealthCheck のために、デプロイ時に指定した URL で応答する必要があります。discord.py は Web サーバで外部からのクリエストを待ち受ける方式ではないため、HealthCheck 用の Web サーバを別途用意する必要があります。

本実装では、discord.py の Client 起動時の hok で非同期で Flask サーバを起動することで、HealthCheck 用の待ち受けを行っています。

## フォルダ構成

-   app
-   docs
-   experiments
-   notebooks

## 開発環境の準備

```bash
git clone [This repository]
poetry install
```

## Deploy 手順

1. Discord Developer Portal で Bot を作成する
2. Discord サーバに Bot を登録する
3. SSM Parameter を設定する
4. Deploy する

### Discord Developer Portal で Bot を作成する

以下を参考に Bot を作成します。

-   https://discordpy.readthedocs.io/ja/latest/discord.html

### Discord サーバに Bot を登録する

以下を参考に Discord サーバに Bot を登録します。

-   https://discordpy.readthedocs.io/ja/latest/discord.html

### SSM Parameter を設定する

以下の SSM Parameter を手動で設定します。

-   /discord-bot-zundamon/OpenAiApiKey
    -   OpenAI の ApiKey です。
-   /discord-bot-zundamon/LangSmith/ApiKey
    -   LangSmith の ApiKey です。LangSmith を利用しない場合は、設定する必要はありません。
-   /discord-bot-zundamon/LangSmith/Project
    -   LangSmith の Project 名 です。LangSmith を利用しない場合は、設定する必要はありません。
-   /discord-bot-zundamon/Discord/BotToken
    -   Discord の Bot Token です。
-   /discord-bot-zundamon/Discord/GuildId
    -   Discord の Bot を設定する Guild(サーバー)の Id です。

### Deploy する

```bash
cd app
copilot deploy
```

## 備考

-   サーバ管理者はコマンドの権限制限の影響を受けません。このため、動作確認用に別ユーザを用意する必要があります。なお、Discrod の機能で制限できるのはスラッシュコマンドのみです。
-   Discord の機能では、ボットに対するメンションを制限することはできません。
-   discord.py を利用しない場合、スラッシュコマンドは事前に API を直接呼び出して登録しておく必要があります。
-   Discord のボットコマンドは２種類あり、現在はスラッシュコマンドが推奨されています。スラッシュコマンドは SDK 的には Application Command と呼ばれます。
-   Bot の初回レスポンスは 3 秒以内で行う必要があります。
    -   https://stackoverflow.com/questions/73361556/error-discord-errors-notfound-404-not-found-error-code-10062-unknown-inter

## 参考文献

-   [Discord - DEVELOPER PORTAL](https://discord.com/developers/applications)
-   [discord.py](https://discordpy.readthedocs.io/ja/latest/index.html)
-   [aws-lambda-discord-bot](https://github.com/ker0olos/aws-lambda-discord-bot)
-   [ChatGPT の API を使ってずんだもんとボイス付きでお喋りできるアプリを作ってみた](https://neenet-pro.com/zunda-gpt/)
