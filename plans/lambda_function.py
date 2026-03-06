import os
import json
import uuid
import time
import logging
import boto3
import google.generativeai as genai
from botocore.exceptions import ClientError

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数の取得
API_KEY = os.environ.get("GEMINI_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "クイズを生成してください。")
QUESTION_COUNT = int(os.environ.get("QUESTION_COUNT", "10"))
TABLE_NAME = os.environ.get("QUESTIONS_TABLE")

# クライアントの初期化
genai.configure(api_key=API_KEY)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # モデルの準備 (JSONモードを有効化)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )

        # プロンプトの構築
        prompt = f"{SYSTEM_PROMPT}\n\n以下の形式のJSONリストで、{QUESTION_COUNT}問作成してください。\n" \
                 "形式: [{\"content\": \"問題文\", \"answer\": \"答え\"}]"

        # Gemini API呼び出し
        logger.info(f"Generating {QUESTION_COUNT} questions...")
        response = model.generate_content(prompt)

        # レスポンスのパース
        questions = json.loads(response.text)

        if not isinstance(questions, list):
            raise ValueError("AI returned non-list format")

        # DynamoDBへの一括保存
        logger.info(f"Saving {len(questions)} questions to {TABLE_NAME}...")
        with table.batch_writer() as batch:
            for q in questions:
                batch.put_item(
                    Item={
                        'QuestionId': str(uuid.uuid4()),
                        'Content': q.get('content', ''),
                        'Answer': q.get('answer', ''),
                        'IsPublished': False,
                        'CreatedAt': int(time.time())
                    }
                )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Successfully generated and saved {len(questions)} questions.'})
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate questions'})
        }
