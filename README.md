# TaiwanBingo

台灣賓果賓果 (Bingo Bingo) 開獎資料爬蟲、統計分析與 ML 預測系統。

## 功能

- **開獎資料爬蟲**：自動爬取賓果賓果歷史開獎紀錄（每5分鐘一期）
- **統計分析 API**：號碼頻率、冷熱號、遺漏值、區域分布
- **ML 預測模型**：LSTM / 頻率模型 / 集成模型
- **Web 前端介面**：Bootstrap 5 介面，支援圖表視覺化

## 快速開始

```bash
# 1. 建立虛擬環境
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env 填入資料庫連線資訊

# 4. 啟動 PostgreSQL（Docker）
docker run -d --name taiwan_bingo_pg \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=taiwan_bingo \
  -p 5432:5432 postgres:16-alpine

# 5. 執行資料庫遷移
alembic upgrade head

# 6. 啟動伺服器
python -m uvicorn taiwan_bingo.main:app --reload
```

## API 文件

啟動後瀏覽 [http://localhost:8000/docs](http://localhost:8000/docs)

## 專案結構

```
taiwan_bingo/
├── api/          # FastAPI 路由
├── db/           # 資料庫模型 & CRUD
├── schemas/      # Pydantic 資料模型
├── scraper/      # 爬蟲與排程
├── services/     # 業務邏輯層
├── ml/           # 機器學習模組
├── templates/    # Jinja2 HTML 模板
└── static/       # CSS / JS 靜態資源
```

## 賓果賓果說明

- 號碼範圍：1 ~ 80
- 每期開出：20 個號碼
- 開獎頻率：每 5 分鐘一期
- 區域劃分：第一區 1-20、第二區 21-40、第三區 41-60、第四區 61-80

## 免責聲明

本系統僅供學術研究與資料分析使用，不構成任何投注建議。彩票具有隨機性，請理性參與。
