import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FabTech Project Management System", layout="wide"
)

DB_FILE = "fabtech_server_data.db"


# Initialize SQLite Server Database for Persistence
def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_sheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sr_no TEXT,
            unique_id TEXT,
            project_no TEXT,
            description TEXT,
            revision_no TEXT,
            drawing_no TEXT,
            element_type TEXT,
            mark_no TEXT,
            qty REAL,
            part_sl_no TEXT,
            actual_wt REAL,
            draw_total_wt REAL,
            contractor TEXT,
            status TEXT,
            wip_date TEXT,
            rfd_date TEXT,
            dispatch_date TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_backlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sl_no TEXT,
            job_number TEXT,
            customer_name TEXT,
            type_of_project TEXT,
            place TEXT,
            state TEXT,
            country TEXT,
            po_number TEXT,
            po_line_item TEXT,
            po_qty REAL,
            po_rate REAL,
            end_delivery_date TEXT
        )
    """)
  conn.commit()
  conn.close()


def load_data_from_db():
  init_db()
  conn = sqlite3.connect(DB_FILE)
  df_master = pd.read_sql("SELECT * FROM master_sheet", conn)
  df_orders = pd.read_sql("SELECT * FROM order_backlog", conn)
  conn.close()

  # Seed default sample data if tables are empty
  if df_master.empty:
    df_master = pd.DataFrame([
        {
            "sr_no": "1",
            "unique_id": "201-CT-T1-MB-1",
            "project_no": "201",
            "description": "CT-T1",
            "revision_no": "Rev-00",
            "drawing_no": "024014-Q",
            "element_type": "MAIN BEAM",
            "mark_no": "MB-1",
            "qty": 1,
            "part_sl_no": "1/2",
            "actual_wt": 2.268,
            "draw_total_wt": 2.268,
            "contractor": "MANOJ",
            "status": "WIP",
            "wip_date": "2026-02-25",
            "rfd_date": "",
            "dispatch_date": "",
        },
        {
            "sr_no": "2",
            "unique_id": "201-CT-T1-MB-2",
            "project_no": "201",
            "description": "CT-T1",
            "revision_no": "Rev-00",
            "drawing_no": "024014-Q",
            "element_type": "MAIN BEAM",
            "mark_no": "MB-2",
            "qty": 1,
            "part_sl_no": "2/2",
            "actual_wt": 2.268,
            "draw_total_wt": 2.268,
            "contractor": "MANOJ",
            "status": "RFD",
            "wip_date": "2026-01-10",
            "rfd_date": "2026-02-15",
            "dispatch_date": "",
        },
    ])
  if df_orders.empty:
    df_orders = pd.DataFrame([{
        "sl_no": "1",
        "job_number": "201",
        "customer_name": "Adani Pirapanti",
        "type_of_project": "Power Plant",
        "place": "Bhagalpur",
        "state": "Bihar",
        "country": "India",
        "po_number": "2002323",
        "po_line_item": "10",
        "po_qty": 1000,
        "po_rate": 105000,
        "end_delivery_date": "2027-12-31",
    }])
  return df_master, df_orders


def save_master_to_db(df):
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("master_sheet", conn, if_exists="replace", index=False)
  conn.close()


def save_orders_to_db(df):
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("order_backlog", conn, if_exists="replace", index=False)
  conn.close()


df_master, df_orders = load_data_from_db()

st.title("⚙️ FabTech Fabrication Project Management & Tracking Portal")
st.markdown(
    "Server-Persistent Master Data, Online Editing, and Weight-Summed Ageing"
    " Buckets."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Order Backlog",
    "2. Project Master Sheet",
    "3. WIP Ageing Report (Weight Sum)",
    "4. RFD Ageing Report (Weight Sum)",
])

# --- TAB 1: ORDER BACKLOG ---
with tab1:
  st.subheader("Order Backlog Management")
  edited_orders = st.data_editor(
      df_orders, num_rows="dynamic", key="orders_editor"
  )
  if st.button("💾 Save Order Backlog to Server"):
    save_orders_to_db(edited_orders)
    st.success("Order backlog successfully saved to server database!")

# --- TAB 2: PROJECT MASTER SHEET ---
with tab2:
  st.subheader("Project Master Sheet (Server Persistent)")
  st.markdown(
      "Upload master sheets or edit online. Data is saved permanently on the"
      " server."
  )

  uploaded_file = st.file_uploader(
      "Upload Project Master Excel/CSV", type=["xlsx", "csv"], key="master_upload"
  )
  if uploaded_file is not None:
    try:
      if uploaded_file.name.endswith(".csv"):
        df_new = pd.read_csv(uploaded_file)
      else:
        df_new = pd.read_excel(uploaded_file)

      # Clean and standardize column names for the server database
      df_new.columns = [
          c.strip().lower().replace(" ", "_").replace(".", "")
          for c in df_new.columns
      ]
      save_master_to_db(df_new)
      st.success(
          "Project master sheet uploaded and saved permanently to server!"
      )
      st.rerun()
    except Exception as e:
      st.error(f"Error processing uploaded file: {e}")

  edited_master = st.data_editor(
      df_master, num_rows="dynamic", key="master_editor"
  )
  if st.button("💾 Save Master Sheet Changes to Server"):
    save_master_to_db(edited_master)
    st.success(
        "Project master sheet successfully updated and saved to server database!"
    )


# --- HELPER: AGEING BUCKET CALCULATOR WITH WEIGHT SUM ---
def calculate_weight_ageing_report(
    df, status_val, date_col, weight_col="draw_total_wt"
):
  if df.empty or "status" not in df.columns:
    return pd.DataFrame(
        columns=[
            "ProjectNo",
            "0-7 Days",
            "8-15 Days",
            "16-30 Days",
            "30-60 Days",
            ">60 Days",
            "Total Weight",
        ]
    )

  work_df = df[df["status"].astype(str).str.upper() == status_val.upper()].copy()
  if work_df.empty:
    return pd.DataFrame(
        columns=[
            "ProjectNo",
            "0-7 Days",
            "8-15 Days",
            "16-30 Days",
            "30-60 Days",
            ">60 Days",
            "Total Weight",
        ]
    )

  today = pd.Timestamp.today().normalize()
  if date_col in work_df.columns:
    work_df[date_col] = pd.to_datetime(work_df[date_col], errors="coerce")
    work_df["Age"] = (today - work_df[date_col]).dt.days
  else:
    work_df["Age"] = 0

  def get_bucket(age):
    if pd.isna(age) or age < 0:
      return "Unknown"
    elif age <= 7:
      return "0-7 Days"
    elif age <= 15:
      return "8-15 Days"
    elif age <= 30:
      return "16-30 Days"
    elif age <= 60:
      return "30-60 Days"
    else:
      return ">60 Days"

  work_df["Bucket"] = work_df["Age"].apply(get_bucket)

  if weight_col not in work_df.columns:
    # Fallback to numeric column if weight column name differs
    numeric_cols = work_df.select_dtypes(include=["number"]).columns
    weight_col = numeric_cols[0] if len(numeric_cols) > 0 else work_df.columns[11]

  work_df[weight_col] = pd.to_numeric(
      work_df[weight_col], errors="coerce"
  ).fillna(0)
  proj_col = "project_no" if "project_no" in work_df.columns else work_df.columns[2]

  pivot = (
      work_df.pivot_table(
          index=proj_col,
          columns="Bucket",
          values=weight_col,
          aggfunc="sum",
          fill_value=0,
      )
      .reset_index()
      .rename(columns={proj_col: "ProjectNo"})
  )

  expected_cols = [
      "ProjectNo",
      "0-7 Days",
      "8-15 Days",
      "16-30 Days",
      "30-60 Days",
      ">60 Days",
  ]
  for c in expected_cols:
    if c not in pivot.columns:
      pivot[c] = 0.0

  bucket_cols = ["0-7 Days", "8-15 Days", "16-30 Days", "30-60 Days", ">60 Days"]
  pivot["Total Weight"] = pivot[bucket_cols].sum(axis=1)
  return pivot[["ProjectNo"] + bucket_cols + ["Total Weight"]]


# --- TAB 3: WIP AGEING REPORT ---
with tab3:
  st.subheader("WIP Ageing Bucket Report (Sum of Total Weight)")
  st.markdown(
      "Calculated based on **Today's Date - WIP Date** for items with status"
      " **WIP**, summing up `DRAW TOTAL WT`."
  )
  wip_rep = calculate_weight_ageing_report(df_master, "WIP", "wip_date")
  st.dataframe(wip_rep, use_container_width=True)

# --- TAB 4: RFD AGEING REPORT ---
with tab4:
  st.subheader("RFD Ageing Bucket Report (Sum of Total Weight)")
  st.markdown(
      "Calculated based on **Today's Date - RFD Date** for items with status"
      " **RFD**, summing up `DRAW TOTAL WT`."
  )
  rfd_rep = calculate_weight_ageing_report(df_master, "RFD", "rfd_date")
  st.dataframe(rfd_rep, use_container_width=True)
