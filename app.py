import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- 1. App 基本設定 ---
st.set_page_config(page_title="專業雲端記帳本", layout="wide")
st.title("💰 個人雲端收支管理系統")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端資料的函數
def load_data():
    try:
        # ttl=0 確保每次都抓最新資料，不使用過期的暫存
        return conn.read(ttl=0)
    except Exception as e:
        # 如果讀不到資料（例如表單是空的），回傳預設欄位
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

# 初始化 Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 2. 輸入區域 ---
st.header("📝 新增明細紀錄")
col1, col2 = st.columns(2)

with col1:
    date = st.date_input("選擇日期", datetime.date.today())
    type_option = st.selectbox("收入/支出", ["支出", "收入"])
    
    if type_option == "收入":
        category_list = ["薪資收入", "投資獲利", "失業補助", "其他"]
    else:
        category_list = ["飲食", "孝親費", "百貨藥妝", "住房", "交通", "教育", "娛樂", "健保費", "商業保險費", "稅捐", "其他"]
    category = st.selectbox("分類項目", category_list)

with col2:
    amount = st.number_input("金額 (TWD)", min_value=0, step=1)
    if type_option == "收入":
        pay_method = "不適用"
        st.selectbox("支出方式", ["不適用"], disabled=True)
    else:
        pay_method = st.selectbox("支出方式", ["現金", "信用卡"])
    note = st.text_input("備註")

# --- 3. 儲存邏輯 (寫入 Google Sheets) ---
if st.button("確認儲存 💾"):
    # 建立單筆新資料
    new_entry = pd.DataFrame([{
        "日期": str(date),
        "分類項目": category,
        "收支類型": type_option,
        "金額": amount,
        "結餘": amount if type_option == "收入" else -amount,
        "支出方式": pay_method,
        "備註": note
    }])
    
    # 讀取雲端最新資料並合併
    all_data = load_data()
    updated_df = pd.concat([all_data, new_entry], ignore_index=True)
    
    # 寫回 Google Sheets
    try:
        conn.update(data=updated_df)
        st.success("✅ 資料已同步至 Google Sheets！")
        st.session_state.data = updated_df
        st.rerun()
    except Exception as e:
        st.error(f"❌ 儲存失敗：{e}")

# --- 4. 數據回顧 ---
st.markdown("---")
st.header("📊 雲端歷史紀錄")
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
else:
    st.info("目前雲端尚無資料，請新增一筆試試看。")
