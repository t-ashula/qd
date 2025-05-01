# qd

ファイルアップロードして，文字起こしして，セグメントごとにベクトル化して，qdrant で検索する web ui

## tech stack

- python 3.12
- qdrant
- postgresql
- transcriber [kotoba-whisper2.2](https://huggingface.co/kotoba-tech/kotoba-whisper-v2.2)
- embedding [multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base)
- embedding [sentence-bert-base-ja-mean-tokens-v2](https://huggingface.co/sonoisa/sentence-bert-base-ja-mean-tokens-v2)

- postgresql, qdrant は docker compose 経由でセットアップ
- python は poetry で依存管理
  - sqlalchemy
  - fastapi

## postgresql

### episodes table

- id: string
  - uuid
- media_type: string
  - content-type
- name: string
  - アップロードされたときのファイル名
- bytes: int
  - ファイルサイズ
- length: int
  - 秒数
- created_at : datetime now()

### episode_segments table

- id: int
- episode_id: string
  - episodes.id
- seg_no: number
- start: number
- end: number
- text: text
- created_at: datetime now()

## qdrant

### episodes_e5 collection

- 768 次元
- e5-base でベクトル化した文字列を入れる
- payload
  - start: number
  - end: number
  - text: string
  - file_id: string (uuid)
  - seg_no: number

### episodes_v2 collection

- 768 次元
- tokens-v2 でベクトル化した文字列を入れる
- payload
  - start: number
  - end: number
  - text: string
  - episode_id: string (uuid)
  - seg_no: number

## web ui

### `/`

- 検索用のテキスト入力と検索実行ボタン
  - 検索ボタンを押すと `/search?q=${search_word}` に GET
- `/upload` へのリンク

### `/search`

- クエリパラメータ `q` で検索キーワードを受け取る
- 検索キーワードを embedding の各モデルを使ってベクトル化して，qdrant の各コレクションに対して検索
- 検索結果を `f"{payload.episode_id}-{payload.seg_no:%04d}` をキーにマージして，スコアの高い方から順に20件表示
  - 検索結果から `/episodes/${payload.episode_id}#seg${payload.seg_no}` へリンク
- q がなければ `/` にリダイレクト

### `/episodes/:episode_id`

- db の episodes テーブルと episode_segments テーブルから `:episode_id` のデータを持ってきて表示
- segments の表示に対して `<div id=#${episode_segments.seg_no}></div>` としておいてリンクできるようにする
- `/media/:episode_id.:ext` を再生(audio 要素？)可能にする

### `/media/:episode_id.:ext`

- ストレージから `:episode_id` のファイルを取り出して返す

### `/upload`

- ファイル選択ダイアログで mp3, wav, m4a あたりを選択か，ドラッグアンドドロップでファイル受け取る
- アップロードボタンで `/upload` へ post でアップロード
- ファイルを取り出して，
  - db の episodes にファイル名他のメタ情報を保存
  - episodes.id をファイル名に，media_type から拡張子を判定して保存
  - kotoba-whisper2.2 を使って文字起こし
    - 文字起こし結果の 'chunks' リストの各要素から，text と timestamp を 取り出して， text=text, start=timestamp[0], end=timestamp[1] として，episode_segments てーぶるに順次保存
    - 同じ要領で各 chunks リストの text を embedding モデルでベクトル化して qdrant のコレクションに payload として start, end, text, episode_id, seg_no を入れて保存
- 全部終わったら `/episodes/:episode_id` にリダイレクト
