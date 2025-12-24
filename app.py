import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.express as px

# --- 1. 基本設定 ---
st.set_page_config(page_title="雲端記帳分析 App", layout="wide")
st.title("💰 雲端收支管理與分析")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

df = load_data()

# --- 2. 新增資料區域 ---
with st.expander("➕ 新增一筆紀錄"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("選擇日期", datetime.date.today())
        type_option = st.selectbox("收入/支出", ["支出", "收入"])
        
        if type_option == "支出":
            category_list = ["飲食", "交通", "購物", "住房", "教育", "娛樂", "其他"]
        else:
            category_list = ["薪資", "獎金", "投資", "其他"]
        category = st.selectbox("分類項目", category_list)
        
    with col2:
        amount = st.number_input("金額 (TWD)", min_value=0, step=1)
        if type_option == "收入":
            pay_method = " " 
            st.selectbox("支出方式", [" "], disabled=True)
        else:
            pay_method = st.selectbox("支出方式", ["現金", "信用卡", "轉帳"])
        note = st.text_input("備註")

    if st.button("確認儲存 💾"):
        new_entry = pd.DataFrame([{
            "日期": str(date),
            "分類項目": category,
            "收支類型": type_option,
            "金額": amount,
            "結餘": amount if type_option == "收入" else -amount,
            "支出方式": pay_method,
            "備註": note
        }])
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ 資料已同步至 Google Sheets！")
        st.rerun()

st.markdown("---")

# --- 3. 圓餅圖分析 (修正版) ---
st.header("📊 本月支出佔比")
if not df.empty:
    # 統一日期格式
    df['日期'] = pd.to_datetime(df['日期'])
    now = datetime.date.today()
    
    # 篩選當月支出
    monthly_expense = df[
        (df["收支類型"] == "支出") & 
        (df['日期'].dt.year == now.year) & 
        (df['日期'].dt.month == now.month)
    ].copy()
    
    if not monthly_expense.empty:
        # 使用 Plotly 畫圓餅圖
        fig = px.pie(monthly_expense, values='金額', names='分類項目', hole=0.3)
        
        c1, c2 = st.columns([0.7, 0.3])
        with c1:
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.write("**支出分類統計**")
            summary = monthly_expense.groupby("分類項目")["金額"].sum()
            st.write(summary)
    else:
        st.info(f"📅 {now.year}年{now.month}月 尚無支出紀錄。")
else:
    st.info("尚無歷史數據。")

st.markdown("---")

# --- 4. 歷史明細與刪除功能 ---
st.header("🗂️ 歷史紀錄管理")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    st.subheader("🗑️ 刪除紀錄")
    row_idx = st.number_input("輸入欲刪除的編號 (表格最左側數字)", min_value=0, max_value=max(0, len(df)-1), step=1)
    if st.button("⚠️ 確認從雲端刪除"):
        df = df.drop(df.index[row_idx]).reset_index(drop=True)
        conn.update(data=df)
        st.warning(f"編號 {row_idx} 的資料已移除。")
        st.rerun()
