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

  # Convert PyArrow string columns to standard object dtype to prevent assignment TypeErrors
  for col in df_master.columns:
    if pd.api.types.is_string_dtype(df_master[col]):
      df_master[col] = df_master[col].astype(object)
  for col in df_orders.columns:
    if pd.api.types.is_string_dtype(df_orders[col]):
      df_orders[col] = df_orders[col].astype(object)

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

# --- TAB 2: PROJECT MASTER SHEET WITH DYNAMIC FILTERS ---
with tab2:
  st.subheader("Project Master Sheet (Dynamic Filters & Calendar Date Pickers)")
  st.markdown(
      "Upload master template or dynamically filter and edit online. Status"
      " is calculated automatically based on dates."
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

      filter_column_2 = st.selectbox(
          "Select Second Column to Filter By (Optional)",
          options=["None"] + all_columns,
          key="dynamic_filter_col_2",
      )
      if filter_column_2 != "None":
        unique_vals_2 = sorted(
            filtered_master[filter_column_2]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        selected_vals_2 = st.multiselect(
            f"Select value(s) for '{filter_column_2}'", options=unique_vals_2
        )
        if selected_vals_2:
          filtered_master = filtered_master[
              filtered_master[filter_column_2].astype(str).isin(selected_vals_2)
          ]

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
          if pd.isna(val):
            full_df.loc[idx, col] = None
          else:
            full_df.loc[idx, col] = val
      else:
        new_row_df = pd.DataFrame([row])
        full_df = pd.concat([full_df, new_row_df], ignore_index=True)

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
    st.rerun()


# --- HELPER: AGEING REPORT CALCULATION ---
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
    weight_col = work_df.columns[11]

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


# --- TAB 3: WIP AGEING REPORT WITH DRILL-DOWN ---
with tab3:
  st.subheader("WIP Ageing Bucket Report & Mark-No Drill-Down")
  st.markdown(
      "Calculated based on **Today's Date - WIP Date** for items with status"
      " **WIP**, summing up `DRAW TOTAL WT`."
  )

  raw_wip_work_df, wip_rep = get_ageing_detail_df(df_master, "WIP", "wip_date")
  if wip_rep.empty or raw_wip_work_df.empty:
    st.info("No data available for WIP ageing report.")
  else:
    numeric_cols = wip_rep.select_dtypes(include=["number"]).columns
    styled_wip = (
        wip_rep.style.apply(style_ageing_report, axis=None)
        .format("{:.3f}", subset=numeric_cols)
    )
    st.dataframe(styled_wip, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Drill-Down: View Master Mark Numbers for WIP")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
      available_projs = sorted(
          raw_wip_work_df["project_no"].dropna().astype(str).unique().tolist()
      )
      sel_proj = st.selectbox(
          "Select Project No for Drill-Down",
          options=available_projs,
          key="wip_drill_proj",
      )
    with d_col2:
      sel_bucket = st.selectbox(
          "Select Age Bucket",
          options=[
              "0-7 Days",
              "8-15 Days",
              "16-30 Days",
              "30-60 Days",
              ">60 Days",
          ],
          key="wip_drill_bucket",
      )

    drill_filtered = raw_wip_work_df[
        (raw_wip_work_df["project_no"].astype(str) == str(sel_proj))
        & (raw_wip_work_df["Bucket"] == sel_bucket)
    ]
    st.markdown(
        f"**Showing Mark Number Details for Project {sel_proj} in bucket"
        f" '{sel_bucket}':**"
    )
    if drill_filtered.empty:
      st.info(
          "No items found for the selected Project and Age Bucket combination."
      )
    else:
      st.dataframe(
          drill_filtered[[
              "sr_no",
              "drawing_no",
              "element_type",
              "mark_no",
              "qty",
              "draw_total_wt",
              "contractor",
              "wip_date",
              "Age",
          ]],
          use_container_width=True,
      )

# --- TAB 4: RFD AGEING REPORT WITH DRILL-DOWN ---
with tab4:
  st.subheader("RFD Ageing Bucket Report & Mark-No Drill-Down")
  st.markdown(
      "Calculated based on **Today's Date - RFD Date** for items with status"
      " **RFD**, summing up `DRAW TOTAL WT`."
  )

  raw_rfd_work_df, rfd_rep = get_ageing_detail_df(df_master, "RFD", "rfd_date")
  if rfd_rep.empty or raw_rfd_work_df.empty:
    st.info("No data available for RFD ageing report.")
  else:
    numeric_cols = rfd_rep.select_dtypes(include=["number"]).columns
    styled_rfd = (
        rfd_rep.style.apply(style_ageing_report, axis=None)
        .format("{:.3f}", subset=numeric_cols)
    )
    st.dataframe(styled_rfd, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Drill-Down: View Master Mark Numbers for RFD")
    rd_col1, rd_col2 = st.columns(2)
    with rd_col1:
      available_rfd_projs = sorted(
          raw_rfd_work_df["project_no"].dropna().astype(str).unique().tolist()
      )
      sel_rfd_proj = st.selectbox(
          "Select Project No for Drill-Down",
          options=available_rfd_projs,
          key="rfd_drill_proj",
      )
    with rd_col2:
      sel_rfd_bucket = st.selectbox(
          "Select Age Bucket",
          options=[
              "0-7 Days",
              "8-15 Days",
              "16-30 Days",
              "30-60 Days",
              ">60 Days",
          ],
          key="rfd_drill_bucket",
      )

    drill_rfd_filtered = raw_rfd_work_df[
        (raw_rfd_work_df["project_no"].astype(str) == str(sel_rfd_proj))
        & (raw_rfd_work_df["Bucket"] == sel_rfd_bucket)
    ]
    st.markdown(
        f"**Showing Mark Number Details for Project {sel_rfd_proj} in bucket"
        f" '{sel_rfd_bucket}':**"
    )
    if drill_rfd_filtered.empty:
      st.info(
          "No items found for the selected Project and Age Bucket combination."
      )
    else:
      st.dataframe(
          drill_rfd_filtered[[
              "sr_no",
              "drawing_no",
              "element_type",
              "mark_no",
              "qty",
              "draw_total_wt",
              "contractor",
              "rfd_date",
              "Age",
          ]],
          use_container_width=True,
      )


# --- TAB 5: OVERALL PROJECT STATUS PIVOT WITH DRILL-DOWN ---
with tab5:
  st.subheader("Overall Project Status Summary Pivot & Drill-Down")
  st.markdown(
      "Automatic pivot table summarizing total weight (`DRAW TOTAL WT`) by"
      " Project Number, VLOOKUP Project Name, and Status."
  )


  def calculate_overall_status_pivot(df_m, df_o, weight_col="draw_total_wt"):
    if df_m.empty or "status" not in df_m.columns:
      return df_m, pd.DataFrame(
          columns=["ProjectNo", "Project Name", "Grand Total"]
      )

    work_df = df_m.copy()
    if weight_col not in work_df.columns:
      weight_col = work_df.columns[11]

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
          "job_number"
          if "job_number" in df_o.columns
          else (df_o.columns[1] if len(df_o.columns) > 1 else None)
      )
      cust_col = (
          "customer_name"
          if "customer_name" in df_o.columns
          else (df_o.columns[2] if len(df_o.columns) > 2 else None)
      )

      if job_col and cust_col:
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


  def style_overall_pivot(df):
    if df.empty:
      return df
    styles = pd.DataFrame("", index=df.index, columns=df.columns)

    if "Grand Total" in df.columns:
      styles["Grand Total"] = "background-color: #e2f0d9; font-weight: bold;"

    last_idx = df.index[-1]
    if (
        "ProjectNo" in df.columns
        and str(df.loc[last_idx, "ProjectNo"]).strip().upper() == "GRAND TOTAL"
    ):
      styles.loc[last_idx, :] = "background-color: #fff2cc; font-weight: bold;"

    return styles


  raw_pivot_work, overall_pivot = calculate_overall_status_pivot(
      df_master, df_orders
  )
  if overall_pivot.empty or raw_pivot_work.empty:
    st.info("No data available for overall status pivot.")
  else:
    numeric_cols = overall_pivot.select_dtypes(include=["number"]).columns
    styled_pivot = (
        overall_pivot.style.apply(style_overall_pivot, axis=None)
        .format("{:.3f}", subset=numeric_cols)
    )
    st.dataframe(styled_pivot, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Drill-Down: View Master Mark Numbers by Status")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
      available_p_nos = sorted(
          raw_pivot_work["project_no"].dropna().astype(str).unique().tolist()
      )
      sel_p_no = st.selectbox(
          "Select Project No", options=available_p_nos, key="pivot_drill_proj"
      )
    with p_col2:
      available_statuses = sorted(
          raw_pivot_work["status"].dropna().astype(str).unique().tolist()
      )
      sel_status = st.selectbox(
          "Select Status",
          options=available_statuses,
          key="pivot_drill_status",
      )

    drill_pivot_filtered = raw_pivot_work[
        (raw_pivot_work["project_no"].astype(str) == str(sel_p_no))
        & (raw_pivot_work["status"].astype(str) == str(sel_status))
    ]
    st.markdown(
        f"**Showing Mark Number Details for Project {sel_p_no} with Status"
        f" '{sel_status}':**"
    )
    if drill_pivot_filtered.empty:
      st.info(
          "No items found for the selected Project and Status combination."
      )
    else:
      st.dataframe(
          drill_pivot_filtered[[
              "sr_no",
              "drawing_no",
              "element_type",
              "mark_no",
              "qty",
              "draw_total_wt",
              "contractor",
              "wip_date",
              "rfd_date",
              "dispatch_date",
          ]],
          use_container_width=True,
      )
