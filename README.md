# Osho Strategy Lab

1329（iシェアーズ・コア 日経225 ETF）とJT（2914）のリバランス戦略を検証するためのバックテスト環境です。

## 実行方法

```bash
python main.py
```

## Ver1.1.1の追加内容

Ver1.1.1では、王将フィルターの閾値を感覚ではなくデータで決めるため、分析レポートを追加しました。

### 出力ファイル

`result/` に以下を出力します。

- `trade_log.csv`  
  通常の売買ログ。Ver1.1.1から判定用デバッグ項目を追加。

- `summary.csv`  
  バックテスト結果サマリー。

- `daily_gap_analysis.csv`  
  日ごとの1329前日比、JT前日比、乖離率、予定売買数量、推定ミニ株コスト。

- `gap_distribution.csv`  
  乖離率の平均、中央値、標準偏差、分位点。

- `gap_bins.csv`  
  乖離率帯ごとの日数。

- `threshold_analysis.csv`  
  閾値候補ごとの候補日数、平均乖離率、予定JT株数、端数株、推定ミニ株コスト。

## JTミニ株コストの扱い

Ver1.1.1から、JTの0.22%コストは100株未満の端数部分だけに掛けます。

例：112株売買する場合

- 100株：通常取引
- 12株：ミニ株扱い、0.22%コスト

## 現在の主な課題

- Ver1.1の1329回復待ちモードに入ると通常売買が止まりやすい。
- 王将フィルターの閾値そのものより、平均取得単価ベースの `Merit` 判定が売買回数を大きく絞っている可能性がある。
- 次の検証では `Gap >= 閾値` と `Merit > 0` のどちらが主な足切り要因かを比較する。


## Ver2.0.0 出力ファイル

`python main.py` 実行後、`result` フォルダに以下を出力します。

- `trade_log.csv` : 日次売買ログ
- `summary.csv` : 全期間サマリー
- `yearly_performance.csv` : 年度別成績
- `benchmark_comparison.csv` : 戦略、1329 Buy&Hold、JT Buy&Hold、50:50 Buy&Hold の比較
- `benchmark_daily.csv` : 日次ベンチマーク推移
- `daily_gap_analysis.csv` : 乖離率の日次分析
- `gap_distribution.csv` : 乖離率分布
- `gap_bins.csv` : 乖離率帯別集計
- `threshold_analysis.csv` : 閾値別候補日数・コスト分析

Ver2.0.0では、売買ロジックは変更せず、10年データで評価するための基盤追加に限定しています。JT70%回復リバランスはVer2.1で評価します。

本プロジェクトは全天候型アルゴリズムではない。対象は通常相場（緩やかな上昇・レンジ相場）とし、暴落局面・暴落回復局面は別戦略で運用する。