# 機能追加 6 実装計画

## 概要

この計画は、transcriber モデルの追加と選択機能の実装、および関連するデータ構造の変更とマイグレーションについて詳述します。

## 1. データベース変更

### 1.1 TranscribeHistory モデルの追加

`app/models/models.py` に新しいモデルを追加します：

```python
class TranscribeHistory(Base):
    """
    Transcribe histories table for storing transcription history
    """

    __tablename__ = "transcribe_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)
    model_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<TranscribeHistory(id={self.id}, episode_id='{self.episode_id}', model_name='{self.model_name}')>"
```

### 1.2 EpisodeSegment モデルの更新

`EpisodeSegment` モデルに `transcribe_history_id` カラムを追加します：

```python
class EpisodeSegment(Base):
    # 既存のカラム...
    transcribe_history_id = Column(Integer, ForeignKey("transcribe_histories.id"), nullable=True)
    # ...
```

### 1.3 マイグレーションスクリプトの作成

Alembic を使用して、以下のマイグレーションスクリプトを作成します：

1. `transcribe_histories` テーブルの作成
2. `episode_segments` テーブルに `transcribe_history_id` カラムを追加

## 2. Transcriber サービスの更新

### 2.1 TranscriberService クラスの更新

`app/transcriber/transcriber.py` を更新して、複数のモデルをサポートします：

1. 定数として利用可能なモデルのリストを定義
2. モデル名をパラメータとして受け取る `transcribe` メソッドの更新
3. モデルごとに別々のインスタンスを管理するロジックの実装

```python
# 利用可能なモデル
AVAILABLE_MODELS = {
    "kotoba-tech/kotoba-whisper-v2.2": "Kotoba Whisper v2.2",
    "openai/whisper-large-v3": "OpenAI Whisper Large v3"
}

# デフォルトモデル
DEFAULT_MODEL = "kotoba-tech/kotoba-whisper-v2.2"
```

### 2.2 モデル選択機能の実装

`TranscriberService` クラスを更新して、指定されたモデルを使用するように変更します。

## 3. Upload サービスの更新

### 3.1 UploadService クラスの更新

`app/services/upload.py` を更新して、モデル選択をサポートします：

1. `process_upload` メソッドにモデル名パラメータを追加
2. トランスクリプション結果を `transcribe_histories` テーブルに記録
3. セグメントを `episode_segments` テーブルに記録する際に `transcribe_history_id` を設定
4. Qdrant のペイロードに `transcribe_history_id` と `model_name` を追加

## 4. API とエンドポイントの更新

### 4.1 アップロードエンドポイントの更新

`app/api/upload.py` を更新して、モデル選択パラメータをサポートします。

### 4.2 アップロードフォームの更新

`app/templates/upload.html` を更新して、モデル選択ドロップダウンを追加します。

### 4.3 エピソード表示の更新

`app/templates/episode.html` を更新して、使用されたモデル情報を表示します。

## 5. データマイグレーション

### 5.1 既存データのマイグレーションスクリプトの作成

`app/scripts/migrate_transcribe_histories.py` スクリプトを作成して、以下を実行します：

1. 既存の各エピソードに対して `transcribe_histories` レコードを作成
2. 作成した `transcribe_histories` の ID を対応する `episode_segments` レコードに設定
3. Qdrant の各コレクションのポイントに `transcribe_history_id` と `model_name` を追加

```python
def migrate_transcribe_histories(db):
    # 1. 既存のエピソードに対して transcribe_histories レコードを作成
    episodes = db.query(Episode).all()
    for episode in episodes:
        history = TranscribeHistory(
            episode_id=episode.id,
            model_name="kotoba-tech/kotoba-whisper-v2.2",
            created_at=episode.created_at
        )
        db.add(history)
        db.flush()  # ID を取得するためにフラッシュ

        # 2. episode_segments に transcribe_history_id を設定
        segments = db.query(EpisodeSegment).filter(EpisodeSegment.episode_id == episode.id).all()
        for segment in segments:
            segment.transcribe_history_id = history.id

        # 3. Qdrant のペイロードを更新
        update_qdrant_payload(episode.id, history.id, "kotoba-tech/kotoba-whisper-v2.2")

    db.commit()

def update_qdrant_payload(episode_id, history_id, model_name):
    # Qdrant の各コレクションのポイントを更新
    # ...
```

## 6. 実装順序

1. データベースモデルの更新
2. マイグレーションスクリプトの作成と実行
3. Transcriber サービスの更新
4. Upload サービスの更新
5. API とエンドポイントの更新
6. データマイグレーションスクリプトの作成と実行
7. テストと検証

## 7. テスト計画

1. 新しいモデルでの文字起こしが正常に動作することを確認
2. モデル選択機能が正常に動作することを確認
3. 既存データが正しくマイグレーションされたことを確認
4. Qdrant の検索が正常に動作することを確認
