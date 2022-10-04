# parameters for the Elo algorithm -- setting kind of arbitrarily for now, should tune once we have more data
DEFAULT_K_VALUE = 16
DEFAULT_D_VALUE = 400
DEFAULT_SCORING_FUNCTION_BASE = 1.25
INITIAL_RATING = 1000

# Google Sheets info for reading input data
GSHEETS_CREDENTIALS_FILE = "./google-credentials.json"
SPREADSHEET_ID = "1oZ1M3ckCDxYGEQvPk8_Fe9aAGllc8LBvzL6Kc-wP2ik"
DATA_SHEET_ID = 0
PLAYER_SHEET_ID = 1739759371
DUMMY_PLAYER_NAME = "_Sub_"

# dashboard settings
DBC_THEME = "FLATLY"  # others I liked: DARKLY, SIMPLEX, LUMEN (https://bootswatch.com/flatly/)
PLOTLY_THEME = "plotly_white"
LOGO_PATH = "/assets/tennis.jpg"
GITHUB_LOGO_PATH = "assets/GitHub-Mark-32px.png"
GITHUB_URL = "https://github.com/kimyun7/tennis-elo-dashboard"
TITLE = "Aoullim Tennis"
SUBTITLE = "Elo Leaderboard"
