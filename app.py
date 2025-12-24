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
        # 強制轉換日期，errors='coerce' 會處理格式不統一的問題
        data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
        # 移除日期完全無效的列
        data = data.dropna(subset=['日期'])
        # 統一排序：由舊到新
        data = data.sort_values(by="日期", ascending=True).reset_index(drop=True)
        return data
    except Exception as e:
        st.error(f"讀取資料出錯: {e}")
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

# 獲取最新資料
df = load_data()

# --- 2. 新增資料區域 ---
with st.expander("➕ 新增一筆紀錄"):
    col1, col2 = st.columns(2)
    with col1:
        date_val = st.date_input("選擇日期", datetime.date.today())
        type_option = st.selectbox("收入/支出", ["支出", "收入"])
        category_list = ["飲食", "交通", "購物", "住房", "教育", "娛樂", "其他", "孝親費"] if type_option == "支出" else ["薪資", "獎金", "投資", "其他"]
        category = st.selectbox("分類項目", category_list)
    with col2:
        amount = st.number_input("金額 (TWD)", min_value=0, step=1)
        pay_method = st.selectbox("支出方式", ["現金", "信用卡", "轉帳"]) if type_option == "支出" else " "
        note = st.text_input("備註")

    if st.button("確認儲存 💾"):
        new_entry = pd.DataFrame([{
            "日期": date_val,
            "分類項目": category,
            "收支類型": type_option,
            "金額": amount,
            "結餘": amount if type_option == "收入" else -amount,
            "支出方式": pay_method,
            "備註": note
        }])
        # 合併並存回
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        # 存回前將日期轉回字串格式，確保 Google Sheets 格式整齊
        updated_df['日期'] = updated_df['日期'].dt.strftime('%Y-%m-%d')
        conn.update(data=updated_df)
        st.success("✅ 資料已同步！")
        st.rerun()

st.markdown("---")

# --- 3. 數據分析與歷史紀錄連動 ---
if not df.empty:
    # 產生不重複的月份清單 (由新到舊排，方便選擇)
    available_months = sorted(df['日期'].dt.strftime('%Y-%m').unique(), reverse=True)
    
    # 選擇分析月份
    selected_month = st.selectbox("📅 選擇分析月份 (圖表與歷史紀錄將同步篩選)", available_months)
    
    # 【關鍵：統一篩選當月資料】
    filtered_df = df[df['日期'].dt.strftime('%Y-%m') == selected_month].copy()
    
    # --- A. 長條圖分析 ---
    st.header(f"📊 {selected_month} 支出統計")
    expense_df = filtered_df[filtered_df["收支類型"] == "支出"]
    
    if not expense_df.empty:
        chart_data = expense_df.groupby("分類項目", as_index=False)["金額"].sum().sort_values(by="金額", ascending=False)
        fig = px.bar(chart_data, x='分類項目', y='金額', color='分類項目', text_auto='.2s', title="類別支出排行")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"{selected_month} 尚無支出紀錄。")

    st.markdown("---")

    # --- B. 歷史紀錄管理 (僅顯示選定月份) ---
    st.header(f"🗂️ {selected_month} 歷史明細管理")
    # 顯示前先轉為字串格式
    display_df = filtered_df.copy()
    display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_df, use_container_width=True)
    
    # 刪除功能
    st.subheader("🗑️ 刪除紀錄")
    if not display_df.empty:
        # 注意：這裡刪除的是 filtered_df 的 index，要對應回原始 df 刪除
        row_to_del_display = st.number_input("輸入欲刪除的編號 (表格最左側 index)", min_value=int(display_df.index.min()), max_value=int(display_df.index.max()), step=1)
        
        if st.button("⚠️ 確認刪除此筆"):
            # 從原始 df 中刪除對應的資料
            df_final = df.drop(row_to_del_display).reset_index(drop=True)
            df_final['日期'] = df_final['日期'].dt.strftime('%Y-%m-%d')
            conn.update(data=df_final)
            st.warning("資料已移除並更新至雲端。")
            st.rerun()
else:
    st.info("目前雲端尚無數據。")
