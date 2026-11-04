import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FabTech Project Management System", layout="wide"
)

DB_FILE = "fabtech_server_data.db"


# Initialize Server Database
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

  # Ensure Part Sl No is explicitly treated as string format
  if not df_master.empty and "part_sl_no" in df_master.columns:
    df_master["part_sl_no"] = df_master["part_sl_no"].astype(str)

  # Round weights to 3 decimal places if present
  for w_col in ["actual_wt", "draw_total_wt"]:
    if not df_master.empty and w_col in df_master.columns:
      df_master[w_col] = pd.to_numeric(
          df_master[w_col], errors="coerce"
      ).round(3)

  if df_master.empty:
    df_master = pd.DataFrame([{
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
        "status": "YTS",
        "wip_date": None,
        "rfd_date": None,
        "dispatch_date": None,
    }])
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


# Function to automatically calculate status based on dates entered
def calculate_automatic_status(df):
  if df.empty:
    return df

  def derive_status(row):
    dispatch = str(row.get("dispatch_date", "")).strip()
    rfd = str(row.get("rfd_date", "")).strip()
    wip = str(row.get("wip_date", "")).strip()

    if dispatch and dispatch.lower() not in [
        "nan",
        "none",
        "nat",
        "",
        "NaT",
    ]:
      return "DISP"
    elif rfd and rfd.lower() not in ["nan", "none", "nat", "", "NaT"]:
      return "RFD"
    elif wip and wip.lower() not in ["nan", "none", "nat", "", "NaT"]:
      return "WIP"
    else:
      return "YTS"

  if "status" in df.columns:
    df["status"] = df.apply(derive_status, axis=1)
  return df


def save_master_to_db(df):
  if "part_sl_no" in df.columns:
    df["part_sl_no"] = df["part_sl_no"].astype(str)
  for w_col in ["actual_wt", "draw_total_wt"]:
    if w_col in df.columns:
      df[w_col] = pd.to_numeric(df[w_col], errors="coerce").round(3)
  df = calculate_automatic_status(df)
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
    "Server-Persistent Master Data, Auto-Status Calculation, Ageing Reports,"
    " and Overall Status Pivot."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Order Backlog",
    "2. Project Master Sheet",
    "3. WIP Ageing Report (Weight Sum)",
    "4. RFD Ageing Report (Weight Sum)",
    "5. Overall Project Status Pivot",
])

# --- TAB 1: ORDER BACKLOG & UPLOAD ---
with tab1:
  st.subheader("Order Backlog Management & Master Upload")
  uploaded_order_file = st.file_uploader(
      "Upload Order Backlog Excel/CSV", type=["xlsx", "csv"], key="order_upload"
  )
  if uploaded_order_file is not None:
    try:
      if uploaded_order_file.name.endswith(".csv"):
        df_order_new = pd.read_csv(uploaded_order_file)
      else:
        df_order_new = pd.read_excel(uploaded_order_file)
      df_order_new.columns = [
          c.strip().lower().replace(" ", "_").replace(".", "")
          for c in df_order_new.columns
      ]
      save_orders_to_db(df_order_new)
      st.success("Order backlog uploaded and saved permanently to server!")
      st.rerun()
    except Exception as e:
      st.error(f"Error processing order file: {e}")

  if "end_delivery_date" in df_orders.columns:
    df_orders["end_delivery_date"] = pd.to_datetime(
        df_orders["end_delivery_date"].replace(
            ["", "None", "none", "NaN", "nan", "NaT", "nat"], pd.NaT
        ),
        errors="coerce",
    ).dt.date

  order_column_configs = {}
  if "end_delivery_date" in df_orders.columns:
    order_column_configs["end_delivery_date"] = st.column_config.DateColumn(
        label="End Delivery Date", format="YYYY-MM-DD"
    )

  edited_orders = st.data_editor(
      df_orders,
      num_rows="dynamic",
      key="orders_editor",
      column_config=order_column_configs,
  )
  if st.button("💾 Save Order Backlog to Server"):
    if "end_delivery_date" in edited_orders.columns:
      edited_orders["end_delivery_date"] = pd.to_datetime(
          edited_orders["end_delivery_date"], errors="coerce"
      ).dt.strftime("%Y-%m-%d")
      edited_orders["end_delivery_date"] = edited_orders[
          "end_delivery_date"
      ].fillna("")
    save_orders_to_db(edited_orders)
    st.success("Order backlog successfully saved to server database!")
    st.rerun()

# --- TAB 2: PROJECT MASTER SHEET WITH FILTERS ---
with tab2:
  st.subheader("Project Master Sheet (Filters & Calendar Date Pickers)")
  st.markdown(
      "Upload master template or filter and edit online. Status is calculated"
      " automatically based on dates."
  )

  uploaded_file = st.file_uploader(
      "Upload Project Master Excel/CSV", type=["xlsx", "csv"], key="master_upload"
  )
  if uploaded_file is not None:
    try:
      if uploaded_file.name.endswith(".csv"):
        df_new = pd.read_csv(
            uploaded_file, dtype={"Part Sl No": str, "part_sl_no": str}
        )
      else:
        df_new = pd.read_excel(uploaded_file, dtype=str)

      df_new.columns = [
          c.strip().lower().replace(" ", "_").replace(".", "")
          for c in df_new.columns
      ]
      if "part_sl_no" in df_new.columns:
        df_new["part_sl_no"] = df_new["part_sl_no"].astype(str)

      save_master_to_db(df_new)
      st.success("Project master sheet uploaded and saved permanently to server!")
      st.rerun()
    except Exception as e:
      st.error(f"Error processing uploaded file: {e}")

  df_master = calculate_automatic_status(df_master)

  # --- FILTER SECTION ---
  with st.expander("🔍 Filter Project Master Sheet", expanded=True):
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
      available_projects = (
          ["All"] + sorted(df_master["project_no"].dropna().unique().tolist())
          if "project_no" in df_master.columns
          else ["All"]
      )
      selected_project = st.selectbox(
          "Filter by Project No", available_projects
      )
    with col_f2:
      available_statuses = (
          ["All"] + sorted(df_master["status"].dropna().unique().tolist())
          if "status" in df_master.columns
          else ["All"]
      )
      selected_status = st.selectbox("Filter by Status", available_statuses)
    with col_f3:
      available_contractors = (
          ["All"] + sorted(df_master["contractor"].dropna().unique().tolist())
          if "contractor" in df_master.columns
          else ["All"]
      )
      selected_contractor = st.selectbox(
          "Filter by Contractor", available_contractors
      )

  # Apply filters to working view
  filtered_master = df_master.copy()
  if selected_project != "All":
    filtered_master = filtered_master[
        filtered_master["project_no"] == selected_project
    ]
  if selected_status != "All":
    filtered_master = filtered_master[
        filtered_master["status"] == selected_status
    ]
  if selected_contractor != "All":
    filtered_master = filtered_master[
        filtered_master["contractor"] == selected_contractor
    ]

  # Clean up date columns for st.data_editor
  for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
    if d_col in filtered_master.columns:
      filtered_master[d_col] = pd.to_datetime(
          filtered_master[d_col].replace(
              ["", "None", "none", "NaN", "nan", "NaT", "nat"], pd.NaT
          ),
          errors="coerce",
      ).dt.date

  column_configurations = {}
  for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
    if d_col in filtered_master.columns:
      column_configurations[d_col] = st.column_config.DateColumn(
          label=d_col.replace("_", " ").title(), format="YYYY-MM-DD"
      )

  if "status" in filtered_master.columns:
    column_configurations["status"] = st.column_config.TextColumn(
        label="Status (Auto)", disabled=True
    )

  edited_filtered_master = st.data_editor(
      filtered_master,
      num_rows="dynamic",
      key="master_editor",
      column_config=column_configurations,
  )

  if st.button("💾 Save Master Sheet Changes to Server"):
    # Re-integrate edited rows back into full master DataFrame safely via index matching
    full_df = df_master.copy()
    for idx, row in edited_filtered_master.iterrows():
      if idx in full_df.index:
        full_df.loc[idx] = row
      else:
        # Handle newly added rows from the data editor
        full_df = pd.concat(
            [full_df, pd.DataFrame([row])], ignore_index=True
        )

    for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
      if d_col in full_df.columns:
        full_df[d_col] = pd.to_datetime(
            full_df[d_col], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        full_df[d_col] = full_df[d_col].fillna("")

    for w_col in ["actual_wt", "draw_total_wt"]:
      if w_col in full_df.columns:
        full_df[w_col] = pd.to_numeric(
            full_df[w_col], errors="coerce"
        ).round(3)

    full_df = calculate_automatic_status(full_df)
    save_master_to_db(full_df)
    st.success(
        "Project master sheet successfully updated, auto-status calculated, and"
        " saved to server!"
    )
