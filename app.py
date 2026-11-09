import base64
import datetime
import io
import os
import sqlite3
from github import Github
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="FabTech Project Management System", layout="wide"
)

# --- AUTHENTICATION CONFIGURATION ---
if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
  st.session_state["username"] = ""

VALID_CREDENTIALS = {"admin": "steel2030", "avikram": "plant2030"}


def login_screen():
  st.markdown(
      """
        <style>
        .stApp { background-color: #f4f6f9; }
        .login-container { max-width: 450px; margin: 80px auto; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        </style>
        """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🔐 FabTech Portal")
    st.markdown("### Secure Login")

    with st.form("login_form"):
      username = st.text_input("Username")
      password = st.text_input("Password", type="password")
      submit = st.form_submit_button("Sign In", use_container_width=True)

      if submit:
        if (
            username in VALID_CREDENTIALS
            and VALID_CREDENTIALS[username] == password
        ):
          st.session_state["authenticated"] = True
          st.session_state["username"] = username
          st.success("Login successful! Loading dashboard...")
          st.rerun()
        else:
          st.error("❌ Invalid username or password.")
    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state["authenticated"]:
  login_screen()
  st.stop()

# --- CUSTOM BACKGROUND & UI STYLING ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f4f6f9; }
    h1, h2, h3 { color: #1f3a60; }
    </style>
    """,
    unsafe_allow_html=True,
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
            plant TEXT,
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

  for col in df_master.columns:
    if pd.api.types.is_string_dtype(df_master[col]):
      df_master[col] = df_master[col].astype(object)
  for col in df_orders.columns:
    if pd.api.types.is_string_dtype(df_orders[col]):
      df_orders[col] = df_orders[col].astype(object)

  if not df_master.empty and "part_sl_no" in df_master.columns:
    df_master["part_sl_no"] = df_master["part_sl_no"].astype(str)
  if not df_master.empty and "plant" not in df_master.columns:
    df_master["plant"] = "Plant-1"

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
        "plant": "Plant-1",
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
        "po_rate": 105000.0,
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


def backup_db_to_github():
  """Automatically pushes the SQLite database to GitHub to persist data on Streamlit Cloud."""
  try:
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
      return
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["GITHUB_REPO"]
    file_path = "fabtech_server_data.db"

    if not os.path.exists(file_path):
      return

    g = Github(token)
    repo = g.get_repo(repo_name)

    with open(file_path, "rb") as f:
      db_content = f.read()

    try:
      file_in_repo = repo.get_contents(file_path)
      repo.update_file(
          path=file_path,
          message="[Auto-Backup] Update SQLite database from Streamlit Cloud",
          content=db_content,
          sha=file_in_repo.sha,
      )
    except Exception:
      repo.create_file(
          path=file_path,
          message=(
              "[Auto-Backup] Initial SQLite database upload from Streamlit Cloud"
          ),
          content=db_content,
      )
    st.toast("Database backed up to GitHub successfully!", icon="☁️")
  except Exception as e:
    st.error(f"GitHub Auto-Backup Error: {e}")


def save_master_to_db(df):
  if "part_sl_no" in df.columns:
    df["part_sl_no"] = df["part_sl_no"].astype(str)
  if "plant" not in df.columns:
    df["plant"] = "Plant-1"
  for w_col in ["actual_wt", "draw_total_wt"]:
    if w_col in df.columns:
      df[w_col] = pd.to_numeric(df[w_col], errors="coerce").round(3)
  df = calculate_automatic_status(df)
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("master_sheet", conn, if_exists="replace", index=False)
  conn.close()
  backup_db_to_github()


def save_orders_to_db(df):
  conn = sqlite3.connect(DB_FILE)
  df.to_sql("order_backlog", conn, if_exists="replace", index=False)
  conn.close()
  backup_db_to_github()


df_master, df_orders = load_data_from_db()
df_master = calculate_automatic_status(df_master)

# --- SIDEBAR: USER INFO & BACKUP RESTORE ---
st.sidebar.markdown(f"👤 **Logged in as:** `{st.session_state['username']}`")
if st.sidebar.button("🚪 Sign Out"):
  st.session_state["authenticated"] = False
  st.session_state["username"] = ""
  st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Database Backup & Restore")
if os.path.exists(DB_FILE):
  with open(DB_FILE, "rb") as f:
    db_bytes = f.read()
  st.sidebar.download_button(
      label="📥 Download Database Backup",
      data=db_bytes,
      file_name="fabtech_server_data.db",
      mime="application/octet-stream",
  )

uploaded_backup = st.sidebar.file_uploader("📤 Restore Database (.db)", type=["db"])
if uploaded_backup is not None:
  if st.sidebar.button("⚠️ Confirm & Overwrite Database", type="primary"):
    try:
      with open(DB_FILE, "wb") as f:
        f.write(uploaded_backup.getbuffer())
      st.sidebar.success("Database restored successfully! Reloading...")
      st.rerun()
    except Exception as e:
      st.sidebar.error(f"Restoration failed: {e}")

# --- MAIN APP HEADER & KPIS ---
st.title("⚙️ FabTech Fabrication Project Management & Tracking Portal")
st.markdown(
    "Server-Persistent Master Data, Visual Analytics, Contractor Tracker, and"
    " Monthly Performance."
)

st.markdown("### 📊 Executive KPI Summary")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_tonnage_raw = (
    df_master["draw_total_wt"].sum()
    if not df_master.empty and "draw_total_wt" in df_master.columns
    else 0.0
)
disp_mask = (
    df_master["status"].astype(str).str.upper() == "DISP"
    if not df_master.empty and "status" in df_master.columns
    else pd.Series([False])
)
dispatched_tonnage_raw = (
    df_master.loc[disp_mask, "draw_total_wt"].sum()
    if not df_master.empty and "draw_total_wt" in df_master.columns
    else 0.0
)

total_tonnage_int = int(round(total_tonnage_raw))
dispatched_tonnage_int = int(round(dispatched_tonnage_raw))
completion_pct = (
    round((dispatched_tonnage_raw / total_tonnage_raw) * 100, 1)
    if total_tonnage_raw > 0
    else 0.0
)

today = pd.Timestamp.today().normalize()


def count_critical_backlog(df):
  if df.empty or "wip_date" not in df.columns:
    return 0
  temp = df.copy()
  temp["wip_date"] = pd.to_datetime(temp["wip_date"], errors="coerce")
  temp["Age"] = (today - temp["wip_date"]).dt.days
  return len(temp[(temp["status"].isin(["WIP", "RFD"])) & (temp["Age"] > 60)])


critical_items_count = count_critical_backlog(df_master)

kpi1.metric(
    label="Total Master Tonnage",
    value=f"{total_tonnage_int:,} MT",
    delta="Active Scope",
)
kpi2.metric(
    label="Dispatched Tonnage",
    value=f"{dispatched_tonnage_int:,} MT",
    delta=f"{int(round(completion_pct))}% Done",
)
kpi3.metric(
    label="Active Orders Count",
    value=str(len(df_orders)) if not df_orders.empty else "0",
    delta="Backlog",
)
kpi4.metric(
    label="Critical (>60 Days Stalled)",
    value=str(critical_items_count),
    delta="Needs Attention" if critical_items_count > 0 else "All Clear",
    delta_color="inverse" if critical_items_count > 0 else "normal",
)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "1. Order Backlog",
    "2. Project Master Sheet",
    "3. WIP Ageing Report",
    "4. RFD Ageing Report",
    "5. Overall Status Pivot",
    "6. Milestone Tracker",
    "7. Contractor Performance",
    "8. Visual Analytics & Charts",
    "9. Monthly RFD & Dispatch",
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

  if "po_rate" in df_orders.columns:
    df_orders["po_rate"] = pd.to_numeric(
        df_orders["po_rate"], errors="coerce"
    ).round(2)

  order_column_configs = {}
  if "end_delivery_date" in df_orders.columns:
    order_column_configs["end_delivery_date"] = st.column_config.DateColumn(
        label="End Delivery Date", format="YYYY-MM-DD"
    )
  if "po_rate" in df_orders.columns:
    order_column_configs["po_rate"] = st.column_config.NumberColumn(
        label="PO Rate (INR)", format="₹ %.2f"
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
    if "po_rate" in edited_orders.columns:
      edited_orders["po_rate"] = pd.to_numeric(
          edited_orders["po_rate"], errors="coerce"
      ).round(2)
    save_orders_to_db(edited_orders)
    st.success("Order backlog successfully saved to server database!")
    st.rerun()

# --- TAB 2: PROJECT MASTER SHEET ---
with tab2:
  st.subheader(
      "Project Master Sheet (Dynamic Filters, Editing & Excel Export)"
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
      st.success("Project master sheet uploaded and saved to server!")
      st.rerun()
    except Exception as e:
      st.error(f"Error processing uploaded file: {e}")

  with st.expander(
      "🔍 Advanced Dynamic Column Filters (Filter any column)", expanded=True
  ):
    all_columns = list(df_master.columns)
    filter_column = st.selectbox(
        "Select Column to Filter By",
        options=["None"] + all_columns,
        key="dynamic_filter_col",
    )
    filtered_master = df_master.copy()
    if filter_column != "None":
      unique_vals = sorted(
          df_master[filter_column].dropna().astype(str).unique().tolist()
      )
      selected_vals = st.multiselect(
          f"Select value(s) for '{filter_column}'", options=unique_vals
      )
      if selected_vals:
        filtered_master = filtered_master[
            filtered_master[filter_column].astype(str).isin(selected_vals)
        ]

  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    filtered_master.to_excel(writer, index=False, sheet_name="ProjectMaster")
  st.download_button(
      label="📥 Download Filtered Master Sheet as Excel (.xlsx)",
      data=output.getvalue(),
      file_name="FabTech_Project_Master.xlsx",
      mime=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
  )

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
    full_df = df_master.copy()
    for idx, row in edited_filtered_master.iterrows():
      if idx in full_df.index:
        for col in edited_filtered_master.columns:
          val = row[col]
          full_df.loc[idx, col] = None if pd.isna(val) else val
      else:
        full_df = pd.concat(
            [full_df, pd.DataFrame([row])], ignore_index=True
        )

    for d_col in ["wip_date", "rfd_date", "dispatch_date"]:
      if d_col in full_df.columns:
        full_df[d_col] = pd.to_datetime(
            full_df[d_col], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        full_df[d_col] = full_df[d_col].fillna("")

    save_master_to_db(full_df)
    st.success("Project master sheet successfully updated and saved to server!")
    st.rerun()


# --- HELPER: AGEING REPORT ---
def get_ageing_detail_df(df, status_val, date_col, weight_col="draw_total_wt"):
  empty_rep = pd.DataFrame(
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
  if df.empty or "status" not in df.columns:
    return pd.DataFrame(), empty_rep
  work_df = df[df["status"].astype(str).str.upper() == status_val.upper()].copy()
  if work_df.empty:
    return pd.DataFrame(), empty_rep
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
  bucket_cols = ["0-7 Days", "8-15 Days", "16-30 Days", "30-60 Days", ">60 Days"]
  for c in bucket_cols:
    if c not in pivot.columns:
      pivot[c] = 0.0
  pivot["Total Weight"] = pivot[bucket_cols].sum(axis=1)
  final_df = pivot[["ProjectNo"] + bucket_cols + ["Total Weight"]]
  numeric_cols = final_df.select_dtypes(include=["number"]).columns
  final_df[numeric_cols] = final_df[numeric_cols].round(3)
  if not final_df.empty:
    total_row = {
        col: round(final_df[col].sum(), 3)
        if col in numeric_cols
        else ("TOTAL" if col == "ProjectNo" else "")
        for col in final_df.columns
    }
    final_df = pd.concat([final_df, pd.DataFrame([total_row])], ignore_index=True)
  return work_df, final_df


def style_ageing_report(df):
  if df.empty:
    return df
  styles = pd.DataFrame("", index=df.index, columns=df.columns)
  if "Total Weight" in df.columns:
    styles["Total Weight"] = "background-color: #e2f0d9; font-weight: bold;"
  last_idx = df.index[-1]
  if (
      "ProjectNo" in df.columns
      and str(df.loc[last_idx, "ProjectNo"]).strip().upper() == "TOTAL"
  ):
    styles.loc[last_idx, :] = "background-color: #fff2cc; font-weight: bold;"
  return styles


# --- TAB 3: WIP AGEING REPORT ---
with tab3:
  st.subheader("WIP Ageing Bucket Report & Excel Export")
  raw_wip_work_df, wip_rep = get_ageing_detail_df(df_master, "WIP", "wip_date")
  if wip_rep.empty or raw_wip_work_df.empty:
    st.info("No data available for WIP ageing report.")
  else:
    output_wip = io.BytesIO()
    with pd.ExcelWriter(output_wip, engine="xlsxwriter") as writer:
      wip_rep.to_excel(writer, index=False, sheet_name="WIP_Ageing")
    st.download_button(
        label="📥 Download WIP Ageing Report (.xlsx)",
        data=output_wip.getvalue(),
        file_name="WIP_Ageing_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    numeric_cols = wip_rep.select_dtypes(include=["number"]).columns
    styled_wip = wip_rep.style.apply(
        style_ageing_report, axis=None
    ).format("{:.3f}", subset=numeric_cols)
    st.dataframe(styled_wip, use_container_width=True)

# --- TAB 4: RFD AGEING REPORT ---
with tab4:
  st.subheader("RFD Ageing Bucket Report & Excel Export")
  raw_rfd_work_df, rfd_rep = get_ageing_detail_df(df_master, "RFD", "rfd_date")
  if rfd_rep.empty or raw_rfd_work_df.empty:
    st.info("No data available for RFD ageing report.")
  else:
    output_rfd = io.BytesIO()
    with pd.ExcelWriter(output_rfd, engine="xlsxwriter") as writer:
      rfd_rep.to_excel(writer, index=False, sheet_name="RFD_Ageing")
    st.download_button(
        label="📥 Download RFD Ageing Report (.xlsx)",
        data=output_rfd.getvalue(),
        file_name="RFD_Ageing_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    numeric_cols = rfd_rep.select_dtypes(include=["number"]).columns
    styled_rfd = rfd_rep.style.apply(
        style_ageing_report, axis=None
    ).format("{:.3f}", subset=numeric_cols)
    st.dataframe(styled_rfd, use_container_width=True)

# --- TAB 5: OVERALL PROJECT STATUS PIVOT ---
with tab5:
  st.subheader("Overall Project Status Summary Pivot & Excel Export")


  def calculate_overall_status_pivot(df_m, df_o, weight_col="draw_total_wt"):
    if df_m.empty or "status" not in df_m.columns:
      return df_m, pd.DataFrame(
          columns=["ProjectNo", "Project Name", "Grand Total"]
      )
    work_df = df_m.copy()
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

    if not df_o.empty:
      job_col = (
          "job_number" if "job_number" in df_o.columns else df_o.columns[1]
      )
      cust_col = (
          "customer_name" if "customer_name" in df_o.columns else df_o.columns[2]
      )
      mapping_dict = (
          df_o.drop_duplicates(subset=[job_col])
          .set_index(job_col)[cust_col]
          .to_dict()
      )
      pivot["Project Name"] = (
          pivot["ProjectNo"].astype(str).map(mapping_dict).fillna("N/A")
      )
    else:
      pivot["Project Name"] = "N/A"

    cols = ["ProjectNo", "Project Name"] + [
        c for c in pivot.columns if c not in ["ProjectNo", "Project Name"]
    ]
    pivot = pivot[cols]
    numeric_cols = pivot.select_dtypes(include=["number"]).columns
    pivot[numeric_cols] = pivot[numeric_cols].round(3)
    if not pivot.empty:
      total_row = {
          col: round(pivot[col].sum(), 3)
          if col in numeric_cols
          else ("Grand Total" if col == "ProjectNo" else "")
          for col in pivot.columns
      }
      pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)
    return work_df, pivot


  raw_pivot_work, overall_pivot = calculate_overall_status_pivot(
      df_master, df_orders
  )
  if overall_pivot.empty:
    st.info("No data available for status pivot.")
  else:
    output_pivot = io.BytesIO()
    with pd.ExcelWriter(output_pivot, engine="xlsxwriter") as writer:
      overall_pivot.to_excel(writer, index=False, sheet_name="StatusPivot")
    st.download_button(
        label="📥 Download Status Pivot (.xlsx)",
        data=output_pivot.getvalue(),
        file_name="Overall_Status_Pivot.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    st.dataframe(overall_pivot, use_container_width=True)

# --- TAB 6: MILESTONE TRACKER ---
with tab6:
  st.subheader("📅 Milestone & Delivery Timeline Tracker")
  if df_orders.empty:
    st.info("No order backlog data available.")
  else:
    timeline_df = df_orders.copy()
    if not df_master.empty and "project_no" in df_master.columns:
      m_summary = (
          df_master.groupby("project_no")
          .agg(
              total_wt=("draw_total_wt", "sum"),
              disp_wt=(
                  "draw_total_wt",
                  lambda x: x[
                      df_master.loc[x.index, "status"].astype(str).str.upper()
                      == "DISP"
                  ].sum(),
              ),
              rfd_wt=(
                  "draw_total_wt",
                  lambda x: x[
                      df_master.loc[x.index, "status"].astype(str).str.upper()
                      == "RFD"
                  ].sum(),
              ),
              wip_wt=(
                  "draw_total_wt",
                  lambda x: x[
                      df_master.loc[x.index, "status"].astype(str).str.upper()
                      == "WIP"
                  ].sum(),
              ),
          )
          .reset_index()
      )
    else:
      m_summary = pd.DataFrame(
          columns=["project_no", "total_wt", "disp_wt", "rfd_wt", "wip_wt"]
      )

    job_col = "job_number" if "job_number" in timeline_df.columns else None
    date_col = (
        "end_delivery_date" if "end_delivery_date" in timeline_df.columns else None
    )

    if job_col and date_col and not m_summary.empty:
      m_summary["project_no"] = m_summary["project_no"].astype(str)
      timeline_df[job_col] = timeline_df[job_col].astype(str)
      timeline_df = timeline_df.merge(
          m_summary, left_on=job_col, right_on="project_no", how="left"
      )
    else:
      timeline_df["total_wt"] = 0.0
      timeline_df["disp_wt"] = 0.0
      timeline_df["rfd_wt"] = 0.0
      timeline_df["wip_wt"] = 0.0

    # Round weight columns to whole numbers (integers)
    for wt_col in ["total_wt", "disp_wt", "rfd_wt", "wip_wt"]:
      if wt_col in timeline_df.columns:
        timeline_df[wt_col] = (
            pd.to_numeric(timeline_df[wt_col], errors="coerce")
            .fillna(0)
            .round()
            .astype(int)
        )


    def evaluate_milestone(row):
      d_str = str(row.get(date_col, ""))
      if not d_str or d_str.lower() in ["nan", "none", "nat", ""]:
        return "No Date Set"
      try:
        d_val = pd.to_datetime(d_str).normalize()
        disp = float(row.get("disp_wt", 0))
        tot = float(row.get("total_wt", 0))
        if tot > 0 and disp >= tot:
          return "Completed"
        elif d_val < today:
          return "Overdue"
        elif (d_val - today).days <= 30:
          return "Due in 30 Days"
        else:
          return "On Track"
      except Exception:
        return "Invalid Date"


    if date_col:
      timeline_df["Milestone Status"] = timeline_df.apply(
          evaluate_milestone, axis=1
      )


    def style_milestone_cell(val):
      if val == "Overdue":
        return "background-color: #f8cecc; font-weight: bold; color: #a94442;"
      elif val == "Due in 30 Days":
        return "background-color: #fff2cc; font-weight: bold; color: #8a6d3b;"
      elif val == "Completed":
        return "background-color: #e2f0d9; font-weight: bold; color: #3c763d;"
      return ""


    if "Milestone Status" in timeline_df.columns:
      styled_timeline = timeline_df.style.map(
          style_milestone_cell, subset=["Milestone Status"]
      )
    else:
      styled_timeline = timeline_df.style

    # Configure whole number formatting and move (MT) into headers
    timeline_configs = {}
    for col in ["total_wt", "disp_wt", "rfd_wt", "wip_wt"]:
      if col in timeline_df.columns:
        label_text = f"{col.replace('_', ' ').upper()} (MT)"
        timeline_configs[col] = st.column_config.NumberColumn(
            label=label_text, format="%,d"
        )
    if "po_rate" in timeline_df.columns:
      timeline_configs["po_rate"] = st.column_config.NumberColumn(
          label="PO Rate (INR)", format="₹ %.2f"
      )

    st.dataframe(
        styled_timeline,
        column_config=timeline_configs,
        use_container_width=True,
    )

# --- TAB 7: CONTRACTOR PERFORMANCE ---
with tab7:
  st.subheader("👷 Contractor Performance & Shop-Floor Productivity")
  if df_master.empty or "contractor" not in df_master.columns:
    st.info("No contractor data available.")
  else:
    c_df = df_master.copy()
    c_df["contractor"] = c_df["contractor"].fillna("Unassigned").astype(str)
    c_df["draw_total_wt"] = pd.to_numeric(
        c_df["draw_total_wt"], errors="coerce"
    ).fillna(0)
    contractor_summary = (
        c_df.groupby("contractor")
        .agg(
            Total_Items=("mark_no", "count"),
            Total_Weight=("draw_total_wt", "sum"),
            Dispatched_Weight=(
                "draw_total_wt",
                lambda x: x[
                    c_df.loc[x.index, "status"].astype(str).str.upper()
                    == "DISP"
                ].sum(),
            ),
            Active_WIP_Weight=(
                "draw_total_wt",
                lambda x: x[
                    c_df.loc[x.index, "status"].astype(str).str.upper() == "WIP"
                ].sum(),
            ),
        )
        .reset_index()
    )
    contractor_summary[["Total_Weight", "Dispatched_Weight", "Active_WIP_Weight"]] = (
        contractor_summary[
            ["Total_Weight", "Dispatched_Weight", "Active_WIP_Weight"]
        ].round(3)
    )
    st.dataframe(contractor_summary, use_container_width=True)

# --- TAB 8: VISUAL ANALYTICS & CHARTS ---
with tab8:
  st.subheader("📈 Visual Analytics & Shop-Floor Charts (Plotly)")
  if df_master.empty:
    st.info("No data available for charts.")
  else:
    c1, c2 = st.columns(2)
    with c1:
      status_counts = (
          df_master.groupby("status")["draw_total_wt"].sum().reset_index()
      )
      fig_pie = px.pie(
          status_counts,
          names="status",
          values="draw_total_wt",
          title="Weight Distribution by Status (MT)",
          hole=0.4,
      )
      st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
      proj_counts = (
          df_master.groupby("project_no")["draw_total_wt"]
          .sum()
          .reset_index()
      )
      fig_bar = px.bar(
          proj_counts,
          x="project_no",
          y="draw_total_wt",
          title="Total Tonnage per Project (MT)",
      )
      st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 9: MONTHLY RFD & DISPATCH PERFORMANCE ---
with tab9:
  st.subheader(
      "📅 Monthly RFD & Dispatch Performance (Project & Contractor Wise)"
  )
  if df_master.empty:
    st.info("No master data available.")
  else:
    m_df = df_master.copy()
    m_df["rfd_dt"] = pd.to_datetime(m_df["rfd_date"], errors="coerce")
    m_df["dispatch_dt"] = pd.to_datetime(m_df["dispatch_date"], errors="coerce")
    rfd_months = m_df["rfd_dt"].dt.strftime("%Y-%m").dropna().unique()
    disp_months = m_df["dispatch_dt"].dt.strftime("%Y-%m").dropna().unique()
    all_months = sorted(list(set(rfd_months) | set(disp_months)))
    current_ym = pd.Timestamp.today().strftime("%Y-%m")

    if not all_months:
      st.info("No RFD or Dispatch date records found.")
    else:
      default_ix = (
          all_months.index(current_ym)
          if current_ym in all_months
          else len(all_months) - 1
      )
      selected_month = st.selectbox(
          "Filter by Month (YYYY-MM)", options=all_months, index=default_ix
      )

      rfd_filtered = m_df[m_df["rfd_dt"].dt.strftime("%Y-%m") == selected_month]
      disp_filtered = m_df[
          m_df["dispatch_dt"].dt.strftime("%Y-%m") == selected_month
      ]

      st.markdown(f"### 📁 Project-Wise Summary for {selected_month}")
      proj_rfd = (
          rfd_filtered.groupby("project_no")["draw_total_wt"]
          .sum()
          .reset_index()
          .rename(columns={"draw_total_wt": "RFD_Weight_MT"})
      )
      proj_disp = (
          disp_filtered.groupby("project_no")["draw_total_wt"]
          .sum()
          .reset_index()
          .rename(columns={"draw_total_wt": "Dispatch_Weight_MT"})
      )
      proj_merged = pd.merge(
          proj_rfd, proj_disp, on="project_no", how="outer"
      ).fillna(0)

      if proj_merged.empty or "project_no" not in proj_merged.columns:
        st.info(f"No project data recorded for {selected_month}.")
      else:
        proj_merged[["RFD_Weight_MT", "Dispatch_Weight_MT"]] = proj_merged[
            ["RFD_Weight_MT", "Dispatch_Weight_MT"]
        ].round(3)
        total_proj_rfd = round(proj_merged["RFD_Weight_MT"].sum(), 3)
        total_proj_disp = round(proj_merged["Dispatch_Weight_MT"].sum(), 3)
        proj_total_row = pd.DataFrame([{
            "project_no": "GRAND TOTAL",
            "RFD_Weight_MT": total_proj_rfd,
            "Dispatch_Weight_MT": total_proj_disp,
        }])
        proj_merged = pd.concat(
            [proj_merged, proj_total_row], ignore_index=True
        )
        st.dataframe(proj_merged, use_container_width=True)

      st.markdown("---")
      st.markdown(f"### 👷 Contractor-Wise Summary for {selected_month}")
      con_col = "contractor" if "contractor" in m_df.columns else "Contractor"
      if con_col in m_df.columns:
        con_rfd = (
            rfd_filtered.groupby(con_col)["draw_total_wt"]
            .sum()
            .reset_index()
            .rename(columns={"draw_total_wt": "RFD_Weight_MT"})
        )
        con_disp = (
            disp_filtered.groupby(con_col)["draw_total_wt"]
            .sum()
            .reset_index()
            .rename(columns={"draw_total_wt": "Dispatch_Weight_MT"})
        )
        con_merged = pd.merge(con_rfd, con_disp, on=con_col, how="outer").fillna(
            0
        )

        if con_merged.empty or con_col not in con_merged.columns:
          st.info(f"No contractor data recorded for {selected_month}.")
        else:
          con_merged[["RFD_Weight_MT", "Dispatch_Weight_MT"]] = con_merged[
              ["RFD_Weight_MT", "Dispatch_Weight_MT"]
          ].round(3)
          total_con_rfd = round(con_merged["RFD_Weight_MT"].sum(), 3)
          total_con_disp = round(con_merged["Dispatch_Weight_MT"].sum(), 3)
          con_total_row = pd.DataFrame([{
              con_col: "GRAND TOTAL",
              "RFD_Weight_MT": total_con_rfd,
              "Dispatch_Weight_MT": total_con_disp,
          }])
          con_merged = pd.concat(
              [con_merged, con_total_row], ignore_index=True
          )
          st.dataframe(con_merged, use_container_width=True)
