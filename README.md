# market-recap-bot

NY引け後に米国市場の主要数値(為替・金利・コモディティ・株価指数)と
翌営業日の注目経済指標をメール配信する個人プロジェクト。

## 配信内容(MVP)

- 為替: USD/JPY, EUR/USD, GBP/USD, DXY
- 金利: UST 5Y / 10Y / 30Y
- コモディティ: WTI, Brent, Gold
- 株価指数: S&P 500, NASDAQ, Dow
- 翌営業日の注目経済指標(USD・High インパクト)

将来的に LLM によるナラティブ解説、欧州・東京クローズ版を追加予定。

## 配信例

```
【Market Recap】 2026/05/05 (火) NY引け

■ 為替
  USD/JPY        157.26   (+0.26%)
  ...

■ 金利
  UST 10Y       4.45%   (+6.8bp)
  ...

■ コモディティ
  WTI              106.42   (+4.39%)
  ...

■ 翌営業日 (水 5/06 ET) の注目指標 [USD, High]
  08:30 ET  Core PCE Price Index m/m (予想 0.2% / 前回 0.3%)
  10:00 ET  ISM Services PMI (予想 53.7 / 前回 54.0)
```

## セットアップ

### 1. Gmail アプリパスワードを発行

1. Google アカウントで 2段階認証を有効化
2. <https://myaccount.google.com/apppasswords> でアプリパスワードを発行
3. 16桁のパスワードを控える

### 2. GitHub Secrets を設定

リポジトリの **Settings → Secrets and variables → Actions** で以下を登録:

| Secret 名 | 値 |
| --- | --- |
| `GMAIL_ADDRESS` | 送信元 Gmail アドレス |
| `GMAIL_APP_PASSWORD` | 上で発行したアプリパスワード |
| `RECIPIENT` | 配信先(個人アドレス、または将来 Google Group のアドレス) |

### 3. 動作確認

GitHub の **Actions** タブから `market-recap` ワークフローを開き、
`Run workflow` で `dry_run = true` を選んで実行 → ログに本文が出れば OK。

`dry_run = false` で実行すると実際に送信されます。

### 4. 自動配信

`.github/workflows/recap.yml` の `schedule` で平日 22:00 UTC に自動実行されます。

| 時期 | 実行時刻(NY) | 実行時刻(JST) |
| --- | --- | --- |
| EDT(夏時間) | 18:00 ET(NY引け2時間後) | 翌 07:00 JST |
| EST(冬時間) | 17:00 ET(NY引け1時間後) | 翌 07:00 JST |

## ローカル実行

```bash
pip install -r requirements.txt
cp .env.example .env  # 値を埋める

# 数値とフォーマットだけ確認(送信なし)
python -m recap --dry-run

# 実際に送信
python -m recap
```

## 銘柄の追加・削除

`config/instruments.yaml` を編集するだけ。コード変更は不要。

```yaml
groups:
  - name: 為替
    instruments:
      - { symbol: "JPY=X", label: "USD/JPY", kind: fx_jpy }
      # 行を足す/消すだけで反映
```

`symbol` は [Yahoo Finance](https://finance.yahoo.com/) のティッカー、
`kind` は表示形式(`fx`, `fx_jpy`, `yield`, `index`)を指定します。

## 経済指標カレンダーの設定

[Forex Factory](https://www.forexfactory.com/) の無料 XML フィードから取得し、
翌営業日(ET)のイベントを表示します。同じ `config/instruments.yaml` の末尾に設定があります:

```yaml
calendar:
  enabled: true
  currencies: [USD]      # 表示する通貨コード
  impacts: [High]        # High / Medium / Low / Holiday から選択
```

`enabled: false` でセクションごと非表示にできます。

## 構成

```
recap/
  __main__.py   # エントリポイント (fetch → format → send)
  config.py     # YAML 読み込み
  data.py       # yfinance データ取得
  calendar.py   # Forex Factory 経済指標フェッチャー
  format.py     # メール本文整形
  mail.py       # Gmail SMTP 送信
config/
  instruments.yaml
.github/workflows/
  recap.yml
```

## ライセンス・免責

個人プロジェクトです。配信内容は投資助言ではありません。
