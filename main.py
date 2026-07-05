# ============================================
# main.py
# ============================================

from backtest import BackTester
from report import Report
from analysis import OshoAnalyzer

from config import RESULT_PATH


def main():

    bt = BackTester()

    trade_log = bt.run()

    report = Report(RESULT_PATH)

    summary = report.create_summary(trade_log)

    report.print_summary(summary)

    # Ver2.0.0: 10年バックテスト評価基盤
    yearly = report.create_yearly_performance(trade_log)
    benchmark = report.create_benchmark_comparison(trade_log)
    report.print_yearly_performance(yearly)
    report.print_benchmark_comparison(benchmark)

    # Ver2.0.1: 売買ロジックは変更せず、片寄り・枯渇を診断する
    position_diag, position_yearly = report.create_position_diagnostics(trade_log)
    report.print_position_diagnostics(position_diag)

    # Ver1.1.1: 王将フィルター分析レポートを追加出力
    analyzer = OshoAnalyzer()
    analyzer.run()


if __name__ == "__main__":

    main()
