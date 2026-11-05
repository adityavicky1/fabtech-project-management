import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FabTech Project Management System", layout="wide"
)

DB_FILE = "fabtech_server_data.db"


# Initialize Server Database (Active & Archive tables)
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
        CREATE TABLE IF NOT EXISTS archive_master_sheet (
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

  if not df_master.empty and "part_sl_no" in df_master.columns:
    df_master["part_sl_no"] = df_master["part_sl_no"].astype(str)

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
        "contractor": "Vendor_A",
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
        "nat",
    ]:
      return "DISP"
    elif rfd and rfd.lower() not in ["nan", "none", "nat", "", "NaT", "nat"]:
      return "RFD"
    elif wip and wip.lower() not in ["nan", "none", "nat", "", "NaT", "nat"]:
      return "WIP"
    else:
      return "YTS"

  if "status" in df.columns:
    df["status"] = df.apply(derive_status, axis=1)
  return df


def save_master_to_db(df):
  if "part_sl_no" in df.columns:
    df["part_sl_no"] = df["part_sl_no"].astype(str)
  df = calculate_automatic_status(df)
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("master_sheet", conn, if_exists="replace", index=False)
  conn.close()


def save_orders_to_db(df):
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("order_backlog", conn, if_exists="replace", index=False)
  conn.close()


# --- AUTHENTICATION SYSTEM ---
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
  st.session_state.username = ""
  st.session_state.role = ""
  st.session_state.vendor_name = ""

if not st.session_state.authenticated:
  st.title("🔐 FabTech Portal Login")
  st.markdown("Please log in with your assigned vendor or admin credentials.")

  with st.form("login_form"):
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    submit_btn = st.form_submit_button("Login")

    if submit_btn:
      users = {
          "admin": {
              "password": "AdminPassword123",
              "role": "Admin",
              "vendor": "",
          },
          "vendor_a": {
              "password": "VendorA_Pass",
              "role": "Vendor",
              "vendor": "Vendor_A",
          },
          "vendor_b": {
              "password": "VendorB_Pass",
              "role": "Vendor",
              "vendor": "Vendor_B",
          },
          "vendor_c": {
              "password": "VendorC_Pass",
              "role": "Vendor",
              "vendor": "Vendor_C",
          },
      }

      if (
          username_input in users
          and users[username_input]["password"] == password_input
      ):
        st.session_state.authenticated = True
        st.session_state.username = username_input
        st.session_state.role = users[username_input]["role"]
        st.session_state.vendor_name = users[username_input]["vendor"]
        st.success("Login successful!")
        st.rerun()
      else:
        st.error("Invalid username or password.")
  st.stop()

# --- MAIN APP (AFTER SUCCESSFUL LOGIN) ---
df_master, df_orders = load_data_from_db()

st.sidebar.title(f"👤 Welcome, {st.session_state.username}")
st.sidebar.markdown(f"**Role:** {st.session_state.role}")
if st.session_state.role == "Vendor":
  st.sidebar.markdown(f"**Assigned Vendor:** {st.session_state.vendor_name}")

if st.sidebar.button("🚪 Logout"):
  st.session_state.authenticated = False
  st.rerun()

st.title("⚙️ FabTech Fabrication Project Management & Tracking Portal")

if st.session_state.role == "Admin":
  tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
      "1. Order Backlog",
      "2. Project Master Sheet",
      "3. WIP Ageing Report",
      "4. RFD Ageing Report",
      "5. Overall Status Pivot",
      "6. Archive Projects",
  ])
else:
  tab2, tab3, tab4 = st.tabs([
      "2. My Project Master Sheet",
      "3. WIP Ageing Report",
      "4. RFD Ageing Report",
  ])

# --- TAB 1: ORDER BACKLOG (Admin Only) ---
if st.session_state.role == "Admin":
  with tab1:
    st.subheader("Order Backlog Management & Master Upload")
    uploaded_order_file = st.file_uploader(
        "Upload Order Backlog Excel/CSV", type=["xlsx", "csv"], key="order_upload"
    )
    if uploaded_order_file is not None:
      df_order_new = pd.read_excel(uploaded_order_file)
      df_order_new.columns = [
          c.strip().lower().replace(" ", "_").replace(".", "")
          for c in df_order_new.columns
      ]
      save_orders_to_db(df_order_new)
      st.success("Order backlog saved!")
      st.rerun()

    edited_orders = st.data_editor(
        df_orders, num_rows="dynamic", key="orders_editor"
    )
    if st.button("💾 Save Order Backlog"):
      save_orders_to_db(edited_orders)
      st.success("Saved successfully!")

# --- TAB 2: PROJECT MASTER SHEET ---
with tab2:
  st.subheader("Project Master Sheet & Progress Updating")

  if st.session_state.role == "Vendor":
    st.markdown(
        f"Showing data exclusively assigned to vendor:"
        f" **{st.session_state.vendor_name}**"
    )
    editable_df = df_master[
        df_master["contractor"].astype(str).str.strip().str.lower()
        == st.session_state.vendor_name.lower()
    ].copy()
  else:
    st.markdown("Admin View: Managing active projects and vendors.")
    editable_df = df_master.copy()

  uploaded_file = st.file_uploader(
      "Upload Project Master Excel/CSV", type=["xlsx", "csv"], key="master_upload"
  )
  if uploaded_file is not None and st.session_state.role == "Admin":
    df_new = pd.read_excel(uploaded_file, dtype=str)
    df_new.columns = [
        c.strip().lower().replace(" ", "_").replace(".", "")
        for c in df_new.columns
    ]
    save_master_to_db(df_new)
    st.success("Master sheet uploaded successfully!")
    st.rerun()

  editable_df = calculate_automatic_status(editable_df)
  for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
    if d_col in editable_df.columns:
      editable_df[d_col] = pd.to_datetime(
          editable_df[d_col].replace(
              ["", "None", "none", "NaN", "nan", "NaT", "nat"], pd.NaT
          ),
          errors="coerce",
      ).dt.date

  column_configurations = {}
  for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
    if d_col in editable_df.columns:
      column_configurations[d_col] = st.column_config.DateColumn(
          label=d_col.replace("_", " ").title(), format="YYYY-MM-DD"
      )
  if "status" in editable_df.columns:
    column_configurations["status"] = st.column_config.TextColumn(
        label="Status (Auto)", disabled=True
    )
  if st.session_state.role == "Vendor":
    column_configurations["contractor"] = st.column_config.TextColumn(
        label="Contractor", disabled=True
    )

  edited_master = st.data_editor(
      editable_df,
      num_rows="dynamic" if st.session_state.role == "Admin" else "fixed",
      key="master_editor",
      column_config=column_configurations,
  )

  if st.button("💾 Save My Updates to Server"):
    for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
      if d_col in edited_master.columns:
        edited_master[d_col] = pd.to_datetime(
            edited_master[d_col], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        edited_master[d_col] = edited_master[d_col].fillna("")

    edited_master = calculate_automatic_status(edited_master)

    if st.session_state.role == "Vendor":
      df_master.update(edited_master)
      save_master_to_db(df_master)
    else:
      save_master_to_db(edited_master)

    st.success("Changes successfully saved to server!")
    st.rerun()


# --- HELPER: AGEING & PIVOT CALCULATIONS ---
def calculate_weight_ageing_report(df, status_val, date_col):
  if df.empty or "status" not in df.columns:
    return pd.DataFrame()
  work_df = df[df["status"].astype(str).str.upper() == status_val.upper()].copy()
  if work_df.empty:
    return pd.DataFrame()

  today = pd.Timestamp.today().normalize()
  work_df[date_col] = pd.to_datetime(work_df[date_col], errors="coerce")
  work_df["Age"] = (today - work_df[date_col]).dt.days

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
  weight_col = (
      "draw_total_wt" if "draw_total_wt" in work_df.columns else work_df.columns[11]
  )
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
  final_df = pivot[["ProjectNo"] + bucket_cols + ["Total Weight"]]

  if not final_df.empty:
    numeric_cols = final_df.select_dtypes(include=["number"]).columns
    total_row = {
        col: final_df[col].sum() if col in numeric_cols else ""
        for col in final_df.columns
    }
    total_row["ProjectNo"] = "TOTAL"
    final_df = pd.concat([final_df, pd.DataFrame([total_row])], ignore_index=True)
  return final_df


report_df = (
    df_master
    if st.session_state.role == "Admin"
    else df_master[
        df_master["contractor"].astype(str).str.strip().str.lower()
        == st.session_state.vendor_name.lower()
    ]
)

with tab3:
  st.subheader("WIP Ageing Report")
  wip_rep = calculate_weight_ageing_report(report_df, "WIP", "wip_date")
  st.dataframe(wip_rep, use_container_width=True)

with tab4:
  st.subheader("RFD Ageing Report")
  rfd_rep = calculate_weight_ageing_report(report_df, "RFD", "rfd_date")
  st.dataframe(rfd_rep, use_container_width=True)

if st.session_state.role == "Admin":
  with tab5:
    st.subheader("Overall Project Status Summary Pivot")


    def calculate_overall_status_pivot(df):
      if df.empty or "status" not in df.columns:
        return pd.DataFrame()
      work_df = df.copy()
      weight_col = (
          "draw_total_wt"
          if "draw_total_wt" in work_df.columns
          else work_df.columns[11]
      )
      work_df[weight_col] = pd.to_numeric(
          work_df[weight_col], errors="coerce"
      ).fillna(0)
      proj_col = (
          "project_no" if "project_no" in work_df.columns else work_df.columns[2]
      )
      pivot = (
          work_df.pivot_table(
              index=proj_col,
              columns="status",
              values=weight_col,
              aggfunc="sum",
              fill_value=0,
          )
          .reset_index()
          .rename(columns={proj_col: "ProjectNo"})
      )
      status_cols = [c for c in pivot.columns if c != "ProjectNo"]
      pivot["Grand Total"] = pivot[status_cols].sum(axis=1)
      if not pivot.empty:
        numeric_cols = pivot.select_dtypes(include=["number"]).columns
        total_row = {
            col: pivot[col].sum() if col in numeric_cols else ""
            for col in pivot.columns
        }
        total_row["ProjectNo"] = "Grand Total"
        pivot = pd.concat(
            [pivot, pd.DataFrame([total_row])], ignore_index=True
        )
      return pivot


    overall_pivot = calculate_overall_status_pivot(df_master)
    st.dataframe(overall_pivot, use_container_width=True)

  # --- TAB 6: ARCHIVE PROJECTS (Admin Only) ---
  with tab6:
    st.subheader("Project Archiving")
    st.markdown(
        "Archive finished projects to keep your active master sheet lean and"
        " fast."
    )

    if not df_master.empty and "project_no" in df_master.columns:
      active_projects = df_master["project_no"].dropna().unique().tolist()
      selected_archive_proj = st.selectbox(
          "Select Completed Project Number to Archive", options=active_projects
      )

      if st.button("📦 Archive Selected Project"):
        conn = sqlite3.connect(DB_FILE)
        # 1. Get rows for this project from master_sheet
        df_to_archive = df_master[
            df_master["project_no"].astype(str)
            == str(selected_archive_proj)
        ]

        if not df_to_archive.empty:
          # 2. Append to archive_master_sheet table
          df_to_archive.to_sql(
              "archive_master_sheet", conn, if_exists="append", index=False
          )

          # 3. Remove from active master_sheet table
          df_active_remaining = df_master[
              df_master["project_no"].astype(str)
              != str(selected_archive_proj)
          ]
          df_active_remaining.to_sql(
              "master_sheet", conn, if_exists="replace", index=False
          )
          conn.close()

          st.success(
              f"Project {selected_archive_proj} has been successfully"
              " archived!"
          )
          st.rerun()
        else:
          conn.close()
          st.warning("No records found for this project number.")
    else:
      st.info("No active projects found in master sheet.")

    st.markdown("---")
    st.subheader("View Archived Projects")
    conn = sqlite3.connect(DB_FILE)
    df_archive = pd.read_sql("SELECT * FROM archive_master_sheet", conn)
    conn.close()

    if df_archive.empty:
      st.info("No archived projects found.")
    else:
      st.dataframe(df_archive, use_container_width=True)
