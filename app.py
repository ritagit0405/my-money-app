import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. App 基本設定 ---
st.set_page_config(page_title="專業收支管理員", layout="wide")
st.title("💰 個人收支明細管理系統")

DATA_FILE = "my_spending2.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

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
        pay_method = st.selectbox("支出方式", [""], disabled=True)
    else:
        pay_method = st.selectbox("支出方式", ["現金", "信用卡"])
    note = st.text_input("備註")

current_balance = amount if type_option == "收入" else -amount

if st.button("確認儲存 💾"):
    new_data = {
        "日期": str(date),
        "分類項目": category,
        "收支類型": type_option,
        "金額": amount,
        "結餘": current_balance,
        "支出方式": pay_method,
        "備註": note
    }
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_data])], ignore_index=True)
    st.session_state.data.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    st.success("存好了！")
    st.rerun()

# --- 3. 歷史明細與分析 ---
st.markdown("---")
st.header("📊 數據回顧與分析")

if not st.session_state.data.empty:
    # 顯示表格（我們不排序，這樣編號才會固定，方便刪除）
    # 使用 .reset_index() 讓使用者看到編號
    st.write("請對照下表的 **左側編號** 進行刪除：")
    st.dataframe(st.session_state.data, width='stretch')
    
    # 統計
    total_income = st.session_state.data[st.session_state.data["收支類型"] == "收入"]["金額"].sum()
    total_expense = st.session_state.data[st.session_state.data["收支類型"] == "支出"]["金額"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("總收入", f"NT$ {total_income:,.0f}")
    m2.metric("總支出", f"NT$ {total_expense:,.0f}")
    m3.metric("總盈餘", f"NT$ {total_income - total_expense:,.0f}")

    # --- 4. 任意刪除功能區 ---
    st.markdown("---")
    st.subheader("🗑️ 刪除指定紀錄")
    del_col1, del_col2 = st.columns([0.3, 0.7])
    
    with del_col1:
        # 讓使用者輸入想刪除的編號
        row_to_delete = st.number_input("輸入要刪除的編號", min_value=0, max_value=len(st.session_state.data)-1, step=1)
        if st.button("⚠️ 確認刪除此筆"):
            st.session_state.data = st.session_state.data.drop(st.session_state.data.index[row_to_delete])
            # 刪除後要重整索引，並存檔
            st.session_state.data = st.session_state.data.reset_index(drop=True)
            st.session_state.data.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.warning(f"編號 {row_to_delete} 的資料已刪除！")
            st.rerun()
else:
    st.info("尚無資料。")