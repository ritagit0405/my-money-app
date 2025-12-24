import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.express as px

# --- 1. 基本設定 ---
st.set_page_config(page_title="專業雲端帳本分析", layout="wide")
st.title("💰 雲端收支管理與分析系統")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl=0)
        # 確保日期欄位是 datetime 格式，方便排序與篩選
        data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
        return data
    except:
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

# 每次重新執行都抓取最新資料
df = load_data()

# --- 2. 新增資料區域 ---
with st.expander("➕ 新增一筆紀錄"):
    col1, col2 = st.columns(2)
    with col1:
        date_val = st.date_input("選擇日期", datetime.date.today())
        type_option = st.selectbox("收入/支出", ["支出", "收入"])
        
        if type_option == "支出":
            category_list = ["飲食", "交通", "購物", "住房", "教育", "娛樂", "其他", "孝親費"]
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
            "日期": date_val, # 直接存入 date 物件
            "分類項目": category,
            "收支類型": type_option,
            "金額": amount,
            "結餘": amount if type_option == "收入" else -amount,
            "支出方式": pay_method,
            "備註": note
        }])
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        # 移除輔助欄位後存回
        conn.update(data=updated_df)
        st.success("✅ 資料已同步至 Google Sheets！")
        st.rerun()

st.markdown("---")

# --- 3. 數據分析區域 (長條圖 + 月份選擇) ---
st.header("📊 收支數據分析")

if not df.empty:
    # 建立月份選擇器
    df = df.dropna(subset=['日期']) # 移除日期無效的資料
    available_months = sorted(df['日期'].dt.strftime('%Y-%m').unique(), reverse=True)
    
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        selected_month = st.selectbox("📅 選擇分析月份", available_months)
    
    # 篩選選定月份的「支出」資料
    month_df = df[
        (df['日期'].dt.strftime('%Y-%m') == selected_month) & 
        (df["收支類型"] == "支出")
    ].copy()

    if not month_df.empty:
        # 按分類加總
        chart_data = month_df.groupby("分類項目", as_index=False)["金額"].sum()
        # 依照金額由大到小排序長條圖
        chart_data = chart_data.sort_values(by="金額", ascending=False)

        # 使用 Plotly 畫長條圖
        fig = px.bar(chart_data, x='分類項目', y='金額', color='分類項目', 
                     text='金額', title=f"{selected_month} 支出分類統計")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"📅 {selected_month} 尚無支出紀錄。")
else:
    st.info("尚無數據可供分析。")

st.markdown("---")

# --- 4. 歷史紀錄管理 (由舊到新排序) ---
st.header("🗂️ 歷史紀錄管理")

if not df.empty:
    # 解決排序問題：由舊到新 (如果要新到舊，就改為 ascending=False)
    display_df = df.sort_values(by="日期", ascending=True).copy()
    
    # 將日期轉回漂亮格式顯示
    display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
    
    # 顯示表格
    st.dataframe(display_df, use_container_width=True)
    
    # 刪除功能
    st.subheader("🗑️ 刪除紀錄")
    row_to_del = st.number_input("輸入欲刪除的編號 (表格最左側 index)", min_value=0, max_value=max(0, len(display_df)-1), step=1)
    
    if st.button("⚠️ 確認從雲端刪除"):
        # 根據 index 刪除
        final_df = display_df.drop(display_df.index[row_to_del]).reset_index(drop=True)
        conn.update(data=final_df)
        st.warning(f"紀錄已移除。")
        st.rerun()
