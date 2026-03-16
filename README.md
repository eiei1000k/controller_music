# Controller Music

Joyconを楽器にして演奏するためのソフトウェアです。
JoyconのHD振動機能を利用して、音を鳴らすことができます。

## 保障動作条件と推奨動作環境

- Windows 10/11
- Python 3.10以上
- Joycon (Switch1)　一組
- hidapi (Pythonライブラリ)
    - pip install hidapi
        - ※仮想環境を構築してからインストールすることを推奨します。
        - python -m venv .venv

## 使い方

### 1. PCにJoyconを接続
    Joyconのペアリングモードを有効にした状態で、PCのBluetooth設定からJoyconを選択して接続します。
### 2. 正常にJoyconが接続されているかの確認
    main.pyの31行目に再生したい曲のJSONファイルが指定されています(初期はnotes_test.json)。
    main.pyを実行して、Joyconから音が鳴るか確認します。
### 3. 曲のJSONファイルを編集して、オリジナルの曲を作ってみる
    songsフォルダ内にJSONファイルを作成して、曲の情報を記述します。
    JSONファイルの構造は、notes_test.jsonやsequence_test.jsonを参考にしてください。
    曲の情報を記述したら、main.pyの31行目に作成したJSONファイルのパスを指定して、main.pyを実行します。

## 曲のJSONファイルの構造
曲のJSONファイルは、以下のような構造になっています。

```json
{
  "title": "曲のタイトル",
  "bpm": BPMの値,
  "division": 1拍を何分割するか,
  "default_amp": 初期音量の倍率(振動の強さ),
  "assignment": {
    "pair_1": ["L", "R"] // Joyconのペア1に割り当てるデバイスのリスト
  },
  "tracks": [
    {
      "name": "パートの名前",
      "device": "使用するデバイスの名前",
      "amp": 音量の倍率(振動の強さ),
      "notes": [
            { "note": "音符の名前（例: C4, D4, E4）", "length": 音符の長さ(divisionの分割数で表す) } // notes記述の場合
      ]
    },
    {
      "name": "パートの名前",
      "device": "使用するデバイスの名前",
      "amp": 音量の倍率(振動の強さ),
      "sequence": "音符の名前:長さ 音符の名前:長さ ...(例: C4:1 D4:1 E4:1)" // sequence記述の場合
    }
  ]
}
```

## 今後の予定
- MIDIファイルの読み込み機能の実装
- 音符の種類の追加（休符、スタッカートなど）
- 複数のJoyconを同時に使用する機能の実装