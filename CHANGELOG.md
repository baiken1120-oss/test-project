# CHANGELOG

## Ver2.0.1
- 売買ロジックは変更しない。
- 10年バックテストで発生した「1329枯渇後に約定なしが続く」状態を可視化する診断レポートを追加。
- `position_diagnostics.csv` を追加。
- `position_yearly.csv` を追加。


## Ver2.0.0 - 10年バックテスト評価基盤

- 10年CSV対応のため、`data_loader.py` を追加。
  - 日付を正規化。
  - 終値・前日比のカンマ、空白、`-` を吸収して数値化。
  - 1329/JTの共通営業日のみをマージ。
- 年度別成績 `yearly_performance.csv` を追加。
- ベンチマーク比較 `benchmark_comparison.csv` を追加。
- 日次ベンチマーク推移 `benchmark_daily.csv` を追加。
- `trade_log.csv` に `Year`, `Close_1329`, `Close_JT` を追加。
- Ver2.0.0では売買ロジックを変更しない方針のため、JT70%回復リバランスは `ENABLE_RECOVERY_REBALANCE = False` とし、Ver2.1評価用に保留。

2026/07/05

Ver1.0開始

- Python化開始
- Portfolio実装
- Strategy実装

--------------

2026/07/06

- 資金不足処理修正
- 売却→購入順へ変更

--------------

2026/07/05 追加修正

- backtest.pyのJT二重売買を削除
- portfolio.pyを追加資金なしの資金制約型に修正
- 売却数量を保有数量で上限化
- 購入数量を手元資金で上限化
- trade_logへ実際の約定数量、保有比率、追加資金を出力
- 1329がゼロになる問題はVer1.1の戦略変更課題として保留

## 2026-07-05 Ver1.0 report fix

- 初期建付け直後の状態をtrade_logのINIT行として記録。
- summaryの開始資産が初回売買後になっていたため、初期投入額基準の損益を追加。
- 表示項目を「初期投入額」「初期建付後資産」「投入額基準総損益」「ログ期間損益」に整理。
- 追加資金ゼロ方針の検証用にsummaryへ追加資金を出力。

--------------

## 2026-07-05 Ver1.1 recovery rebalance

- JT比率70%以上で通常売買を停止する「1329回復待ちモード」を追加。
- 1329の25日移動平均と25日線乖離率を計算し、trade_logへ出力。
- JT比率70%以上、かつ1329が25日線から-3%以上下に乖離した場合、1329:JT = 15:5（75%:25%）へ戻す回復リバランスを追加。
- summaryに「1329回復待ち回数」「1329回復リバランス回数」を追加。
- 今回の検証期間では1329が25日線より割安にならなかったため、回復リバランスは0回。ただし通常売買停止により1329ゼロ化は回避。

## Ver1.1.1
- 王将フィルター分析ツール `analysis.py` を追加。
- `main.py` 実行時に以下のCSVを `result/` に出力するよう変更。
  - `daily_gap_analysis.csv`
  - `gap_distribution.csv`
  - `gap_bins.csv`
  - `threshold_analysis.csv`
- `trade_log.csv` に判定用デバッグ項目を追加。
  - `Pct_1329`, `Pct_JT`, `Gap`, `BasePercent`, `Merit`, `Planned1329Amount`, `PlannedJTAmount`, `JT_MiniQty`
- JTミニ株コストの扱いを修正。
  - 旧：JT全株に0.22%を適用
  - 新：100株単元部分は通常取引、100株未満の端数部分だけ0.22%を適用

## Ver2.0.2
- Ver2.0.0/2.0.1で誤って無効化していた `ENABLE_RECOVERY_REBALANCE` を True に戻した。
- 売買ロジック自体は添付元コードに存在していた Ver1.1 の 1329回復リバランスを復元。
