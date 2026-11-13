"""Run with python -m streamlit run app.py."""

from pathlib import Path
import sqlite3
import streamlit as st

from organizer.core import scan
from organizer.history import History


st.set_page_config(page_title="Folder Organizer", page_icon="📁", layout="wide")
st.title("Download Folder Organizer")
st.write("Preview your files, sort them into folders, and undo when needed.")
st.caption("Local only · No uploads · No automatic deletion")

folder = st.text_input("Folder path", placeholder=r"C:\Users\YourName\Downloads")
st.caption("Scans top-level files only. Dot-prefixed files, subfolders, and symbolic links are skipped.")

history = History(Path(__file__).parent / ".organizer" / "history.sqlite")
try:
    history.reconcile()
    if st.button("Preview files", type="primary"):
        st.session_state.pop("plan", None)
        try:
            plan = scan(folder) if folder.strip() else None
            if plan is None:
                st.warning("Enter a folder path first.")
            else:
                st.session_state.plan = plan
                st.session_state.folder = folder
        except (OSError, ValueError) as error:
            st.error(f"Cannot scan folder: {error}")

    plan = st.session_state.get("plan")
    if plan is not None and st.session_state.get("folder") == folder:
        if not plan:
            st.info("No eligible files found. Subfolders are left as they are.")
        else:
            st.subheader(f"Preview · {len(plan)} files")
            st.dataframe([
                {"File": m.source.name, "Category": m.destination.parent.name,
                 "Destination": str(m.destination),
                 "Status": "Conflict — will be skipped" if m.destination.exists() else "Ready"}
                for m in plan
            ], hide_index=True, use_container_width=True)
            confirmed = st.checkbox("I reviewed these moves and want to apply them.")
            if st.button("Apply organization", disabled=not confirmed):
                with st.spinner("Organizing files…"):
                    batch = history.apply(plan)
                    history.reconcile()
                results = [r for r in history.rows() if r["batch"] == batch]
                count = sum(r["state"] == "moved" for r in results)
                st.success(f"Moved {count} of {len(results)} files. See history for any skipped files.")
                st.session_state.pop("plan", None)

    st.subheader("Operation history")
    st.caption("Undo checks file contents and never overwrites an occupied original path. Empty category folders remain.")
    rows = history.rows()
    if st.button("Undo latest available batch", disabled=not any(r["state"] == "moved" for r in rows)):
        history.undo_latest()
        st.session_state.pop("plan", None)
        st.info("Undo attempted. Check each file's status and error below.")
        rows = history.rows()
    if rows:
        st.dataframe([
            {"Batch": r["batch"][:8], "Original": r["source"], "Destination": r["destination"],
             "Status": r["state"], "Details": r["error"]} for r in rows
        ], hide_index=True, use_container_width=True)
        if any(r["state"] == "review" for r in rows):
            st.warning("Some files need manual review. Both paths have been preserved; inspect them before making changes.")
    else:
        st.info("No operations yet. Start with a preview.")
except (OSError, sqlite3.Error) as error:
    st.error(f"Operation could not finish: {error}. Check history before retrying.")
finally:
    history.close()
