# Interview BARS System

外国人ITエンジニア向けの面談力診断MVPです。  
今回の版は、あなたがアップロードした **BARS評価項目と面談評価表.xlsx** をそのまま読み込み、以下の5指標で評価します。

- ①日本語の自然さ
- ②日本語の自然さ（非言語）
- ③STAR構造（論理性）
- ④技術説明の深さ
- ⑤論理性（一貫性）

## できること

- 面談質問と回答テキストを入力
- BARS評価をAPIで実行
- 結果をDB保存
- 「前のステージ / 現在 / 次のステージ」でUI表示
- 過去の診断一覧を表示

## 技術構成

- Frontend: Next.js 14
- Backend: FastAPI
- DB: PostgreSQL（Docker） / SQLite（ローカル）
- BARS基準: Excel読込
- AI評価: OpenAI API（未設定時はフォールバック評価）

## 最短起動手順

### 1. Dockerで起動

```bash
cd interview-bars-system
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

### 2. OpenAIを使う場合

プロジェクト直下で `.env` を作成し、以下を設定してください。

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
```

OpenAIキー未設定でもシステム自体は動きます。  
その場合はルールベースの仮評価になります。

## Dockerを使わないローカル起動

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## API

### BARS基準取得

```http
GET /api/v1/bars/criteria
```

### 面談評価実行

```http
POST /api/v1/interviews/evaluate
Content-Type: application/json

{
  "candidate_name": "Chen",
  "question": "これまでの開発経験を教えてください。",
  "transcript": "JavaとSpring Bootを使った..."
}
```

### 面談一覧

```http
GET /api/v1/interviews
```

### 面談詳細

```http
GET /api/v1/interviews/{id}
```

## 次に足すとよい機能

1. 録音アップロード
2. Whisper文字起こし
3. 営業ダッシュボード
4. 合格率分析
5. 権限管理

