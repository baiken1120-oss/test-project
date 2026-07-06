# ============================================
# Osho Strategy Lab
# config.py
# ============================================

# 初期資産
INITIAL_CAPITAL = 20_000_000

# 初期配分
INITIAL_RATIO_1329 = 0.50
INITIAL_RATIO_JT = 0.50

# デッドゾーン(%)
DEAD_ZONE = 0.40

# JT単元株数
JT_ROUND_LOT = 100

# ミニ株コスト
# 楽天かぶミニ想定。100株単元部分には掛けず、100株未満の端数部分だけに掛ける。
MINI_STOCK_COST = 0.0022

# Ver1.1: 1329売られ過ぎ対策
# JT比率が70%以上、かつ1329が25日移動平均から-3%以上下に乖離したら、
# 1329:JT = 15:5（75%:25%）へ回復リバランスする。
ENABLE_RECOVERY_REBALANCE = True

# ============================================
# Ver2.1.0 Strategy Mode
# ============================================

# A : 現行
# B : JT比率が高い時だけ1329買付数量を増やす
# C : 月次リバランス
STRATEGY_MODE = "A"

JT_RATIO_BOOST = 0.65
BOOST_MULTIPLIER = 1.5
MONTHLY_REBALANCE_RATIO = 0.70

RECOVERY_JT_RATIO_THRESHOLD = 0.70
RECOVERY_MA_WINDOW = 25
RECOVERY_1329_DEVIATION_THRESHOLD = -0.03
RECOVERY_TARGET_RATIO_1329 = 0.75
RECOVERY_TARGET_RATIO_JT = 0.25

# Ver1.1.1: 王将フィルター分析用の閾値候補(%)
THRESHOLD_CANDIDATES = [
    0.00, 0.05, 0.10, 0.15, 0.20,
    0.25, 0.30, 0.35, 0.40, 0.45,
    0.50, 0.60, 0.70, 0.80, 0.90, 1.00,
]

# データフォルダ
DATA_PATH = "./data"

# 出力フォルダ
RESULT_PATH = "./result"

# データファイル
FILE_1329 = "1329.csv"
FILE_JT = "JT.csv"
FILE_QUANTITY = "quantity.csv"
