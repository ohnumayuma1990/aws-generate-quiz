# システム構成案: AIによる問題生成システム（コスト最適化版）

本ドキュメントでは、Gemini APIとAWSサービスを活用し、低コストかつ効率的にクイズ問題を生成・管理するシステムの構成案を記載します。

## 1. AIによる問題生成（コスト最適化）

### 活用モデル: Gemini 1.5 Flash (Google)
- **選定理由:**
    - 無料枠が非常に広く、個人の開発や小規模運用であればコストをほぼゼロに抑えることが可能です。
    - 高速なレスポンスと十分なコンテキストウィンドウを持ち、多言語（日本語）対応も優れています。
- **活用方法:**
    - プロンプトにて「週に1回、10問のクイズをJSON形式で出力する」よう指定します。

## 2. スケジューリングと実行環境

### Amazon EventBridge (Scheduler)
- **役割:** 定期実行のトリガー。
- **設定:** `cron(0 0 ? * MON *)`（毎週月曜日の午前0時など）のスケジュールでLambdaを起動するように設定します。

### AWS Lambda
- **役割:** メインロジックの実行。
- **処理フロー:**
    1. EventBridgeから起動。
    2. Gemini APIを呼び出し、10問の新しい問題を生成。
    3. 生成された問題をパースし、DynamoDBに一括保存（BatchWriteItem）。

## 3. データベース設計 (Amazon DynamoDB)

AWSの無期限無料枠（25GB）を活用し、以下の2つのテーブルを設計します。

### ① 問題テーブル (Questions Table)
| 属性名 | 型 | 説明 |
| :--- | :--- | :--- |
| `QuestionId` | String (PK) | 問題の一意なID (UUID等) |
| `Content` | String | 問題文 |
| `Answer` | String | 正解 |
| `IsPublished` | Boolean | 出題済みフラグ (True/False) |
| `CreatedAt` | Number | 作成日時 (Unix Timestamp) |

### ② 回答履歴テーブル (AnswerHistory Table)
| 属性名 | 型 | 説明 |
| :--- | :--- | :--- |
| `UserId` | String (PK) | ユーザーの一意なID |
| `QuestionId` | String (SK) | 反応した問題のID |
| `ReactionTime` | Number | リアクション日時 (Unix Timestamp) |
| `ReactionType` | String | リアクションの内容（例: 正解、不正解、スタンプ等） |

## 4. 実現可能性と実装のポイント

### 実現可能性
- **コスト:** Gemini 1.5 Flashの無料枠とAWSの無料枠（Lambda, DynamoDB, EventBridge）を組み合わせることで、月額コストほぼ0円での運用が十分に可能です。
- **技術的難易度:** 標準的なAWSのサーバーレスアーキテクチャであり、Gemini APIもSDKが提供されているため、実装のハードルは低いです。

### 実装のステップ
1. **Google AI Studio**でAPIキーを取得。
2. **AWS Lambda**でGemini APIを叩くためのコード（PythonやNode.js）を作成。
3. **DynamoDB**テーブルを作成。
4. **EventBridge**でスケジュールを設定。
5. LambdaからDynamoDBへの書き込み権限（IAM Role）を設定。
