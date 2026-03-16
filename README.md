<div align="center">

# Controller Music

Joyconを楽器にして演奏するためのソフトウェアです。</br>
JoyconのHD振動機能を利用して、音を鳴らすことができます。

</div>

<p align="center" style="text-align: center;">
    <!-- 動作保証OS -->
    <img src="https://img.shields.io/badge/OS-Windows10%2F11-blue?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 10/11">
    <!-- 動作保証Pythonバージョン -->
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
    <!-- 動作保証コントローラー -->
    <img src="https://img.shields.io/badge/Controller-Joycon(First Generation)-red?style=for-the-badge&logo=nintendo-switch&logoColor=white" alt="Joycon">
</p>

## 保障動作条件

- Windows 10/11
- Python 3.10以上
- Joycon (Switch1)　一組
  
  
## 環境構築
venvを使用して、Pythonの仮想環境を作成することを推奨します。

```bash
python -m venv .venv
```

必須ライブラリhidapiをインストールします。

```bash
pip install hidapi
```
  
  
## 使い方

### 1. PCにJoyconを接続
<div style="font-size: 1.1em; margin-top: 20px;">
    Joyconのペアリングモードを有効にした状態で、PCのBluetooth設定からJoyconを選択して接続します。
</div>

### 2. 正常にJoyconが接続されているかの確認
<div style="font-size: 1.1em; margin-top: 20px;">
    main.pyの31行目に再生したい曲のJSONファイルが指定されています(初期はnotes_test.json)。</br>
    main.pyを実行して、Joyconから音が鳴るか確認します。
</div>

### 3. 曲のJSONファイルを編集して、オリジナルの曲を作ってみる
<div style="font-size: 1.1em; margin-top: 20px; margin-bottom: 20px;">
    songsフォルダ内にJSONファイルを作成して、曲の情報を記述します。</br>
    JSONファイルの構造は、notes_test.jsonやsequence_test.jsonを参考にしてください。</br>
    サンプルとして、family_mart.jsonも確認できます。
</div>

notes記述の例<br>
[notes_test.json](songs/notes_test.json)
  
sequence記述の例<br>
[sequence_test.json](songs/sequence_test.json)
  
note記法でのサンプル曲（ファミリーマートの入店音）<br>
[family_mart.json](songs/family_mart.json)

<div style="font-size: 1.1em; margin-top: 20px;">
    曲の情報を記述したら、main.pyの31行目に作成したJSONファイルのパスを指定して、main.pyを実行します。
</div>

```bash
python main.py
```

  
  
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
  
  
## 注意事項
- JoyconのHD振動は高振幅では不安定なことが多いです。デバイスへの負荷を考慮して、ampを0.3前後に設定することを推奨します。
- Joycon以外にBluetooth機器を接続している場合、HD振動が正常に動作しないことがあります。可能であれば、Joycon以外のBluetooth機器は切断して使用してください。
- Windows側で他アプリケーションがJoyconを使用している場合、HD振動が正常に動作しないことがあります。可能であれば、他のアプリケーションを終了して使用してください。
  
  
## 今後の予定
- MIDIファイルの読み込み機能の実装
- 音符の種類の追加（休符、スタッカートなど）
- 複数のJoyconを同時に使用する機能の実装