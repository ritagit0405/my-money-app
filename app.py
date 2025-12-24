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
        # 強制轉換日期格式，不符合的會變成 NaT
        data['日期'] = pd.to_datetime(data['日期'], errors='coerce')
        data = data.dropna(subset=['日期'])
        # 初始排序：由舊到新
        data = data.sort_values(by="日期", ascending=True).reset_index(drop=True)
        return data
    except Exception as e:
        return pd.DataFrame(columns=["日期", "分類項目", "收支類型", "金額", "結餘", "支出方式", "備註"])

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
        
        # 合併資料
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        
        # --- 修正點：先統一轉為 datetime，再格式化為字串存檔 ---
        updated_df['日期'] = pd.to_datetime(updated_df['日期'])
        updated_df['日期'] = updated_df['日期'].dt.strftime('%Y-%m-%d')
        
        conn.update(data=updated_df)
        st.success("✅ 資料已同步！")
        st.rerun()

st.markdown("---")

# --- 3. 數據分析區域 (每月總支出折線圖) ---
if not df.empty:
    st.header("📈 每月支出趨勢分析")
    
    expense_df = df[df["收支類型"] == "支出"].copy()
    
    if not expense_df.empty:
        # 建立月份標籤
        expense_df['月份'] = expense_df['日期'].dt.strftime('%Y-%m')
        # 按月加總
        monthly_trend = expense_df.groupby("月份", as_index=False)["金額"].sum()
        monthly_trend = monthly_trend.sort_values("月份")
        
        # 繪製折線圖
        fig = px.line(
            monthly_trend, 
            x="月份", 
            y="金額", 
            title="每月總支出趨勢 (TWD)",
            markers=True,
            text="金額"
        )
        fig.update_traces(textposition="top center", line_color="#EF553B")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("尚無支出資料。")

    st.markdown("---")

    # --- 4. 歷史紀錄管理 (獨立篩選月份) ---
    st.header("🗂️ 歷史紀錄管理")
    
    all_months = sorted(df['日期'].dt.strftime('%Y-%m').unique(), reverse=True)
    if all_months:
        history_month = st.selectbox("🔍 選擇月份查看明細", all_months, key="history_month_sel")
        
        history_df = df[df['日期'].dt.strftime('%Y-%m') == history_month].copy()
        
        # 計算統計卡片
        total_income = history_df[history_df["收支類型"] == "收入"]["金額"].sum()
        total_expense = history_df[history_df["收支類型"] == "支出"]["金額"].sum()
        monthly_balance = total_income - total_expense
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 當月總收入", f"{total_income:,.0f} 元")
        c2.metric("💸 當月總支出", f"{total_expense:,.0f} 元", delta=f"-{total_expense:,.0f}", delta_color="inverse")
        c3.metric("⚖️ 本月結餘", f"{monthly_balance:,.0f} 元", delta=f"{monthly_balance:,.0f}")

        # 表格顯示
        display_df = history_df.copy()
        display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)
        
        # 刪除功能
        with st.expander("🗑️ 刪除單筆紀錄"):
            row_to_del_idx = st.number_input("輸入欲刪除的編號 (表格最左側 index)", 
                                            min_value=int(display_df.index.min()), 
                                            max_value=int(display_df.index.max()), 
                                            step=1)
            
            if st.button("⚠️ 確認刪除資料"):
                df_final = df.drop(row_to_del_idx).reset_index(drop=True)
                df_final['日期'] = df_final['日期'].dt.strftime('%Y-%m-%d')
                conn.update(data=df_final)
                st.warning("資料已移除。")
                st.rerun()
else:
    st.info("目前雲端尚無數據。")
