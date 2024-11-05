import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="audits"
)
cursor = conn.cursor()

# Utility function to fetch foreign key options
def fetch_fk_options(table, column):
    cursor.execute(f"SELECT id FROM {table}")
    return [row[0] for row in cursor.fetchall()]

# Fetch options for dropdowns
department_ids = fetch_fk_options("Department", "id")
employee_ids = fetch_fk_options("Employees", "id")
system_ids = fetch_fk_options("Systems", "id")
audit_ids = fetch_fk_options("SecurityAudits", "id")

# Function to load data into Treeview for selected table
def load_data(table, tree):
    for i in tree.get_children():
        tree.delete(i)
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    for row in rows:
        tree.insert("", "end", values=row)

# Add data for different tables
def add_data(table, values, fields, tree):
    cursor.execute(f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(['%s'] * len(values))})", values)
    conn.commit()
    load_data(table, tree)

# Update selected row for different tables
def update_data(table, fields, values, id_field, id_value, tree):
    set_clause = ', '.join([f"{field} = %s" for field in fields])
    cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {id_field} = %s", values + [id_value])
    conn.commit()
    load_data(table, tree)

# Delete selected row for different tables
def delete_data(table, id_field, id_value, tree):
    cursor.execute(f"DELETE FROM {table} WHERE {id_field} = %s", (id_value,))
    conn.commit()
    load_data(table, tree)

# Main window
root = tk.Tk()
root.title("Security Audits Management System")
root.geometry("1000x700")

# Create tabs for each table
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Dictionary to hold frames and trees for each table
frames = {}
trees = {}

# Define tables and corresponding fields
tables = {
    "Employees": ["last_name", "first_name", "position", "department_id"],
    "Systems": ["name", "type", "department_id", "manager_id"],
    "SecurityAudits": ["date", "status", "employee_id", "system_id"],
    "VulnerabilitiesDetected": ["audit_id", "system_id", "severity", "status"],
    "Department": ["manager_id", "type", "status", "location"]
}

# Loop over each table to create UI
for table, fields in tables.items():
    # Frame and Treeview setup for each table
    frame = tk.Frame(notebook)
    frames[table] = frame
    notebook.add(frame, text=table)
    
    tree = ttk.Treeview(frame, columns=("ID", *fields), show="headings")
    trees[table] = tree
    for idx, field in enumerate(["ID"] + fields):
        tree.heading(field, text=field)
        tree.column(field, width=150)
    tree.pack(expand=True, fill="both")

    # Load data on startup
    load_data(table, tree)
    
    # Entry widgets for each field
    entries = {}
    for idx, field in enumerate(fields):
        tk.Label(frame, text=field.capitalize()).pack()
        if "id" in field and field != "department_id":  # Foreign key field
            options = department_ids if field == "department_id" else employee_ids if field == "manager_id" else system_ids if field == "system_id" else audit_ids
            entry = ttk.Combobox(frame, values=options)
        else:
            entry = tk.Entry(frame)
        entry.pack()
        entries[field] = entry

    # Button to Add data
    def create_add_button(table=table, fields=fields, entries=entries, tree=tree):
        def add_callback():
            values = [entries[field].get() for field in fields]
            add_data(table, values, fields, tree)
        tk.Button(frame, text="Add", command=add_callback).pack()

    # Button to Update data
    def create_update_button(table=table, fields=fields, entries=entries, tree=tree):
        def update_callback():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select error", "Select a row to update.")
                return
            id_value = tree.item(selected[0])['values'][0]
            values = [entries[field].get() for field in fields]
            update_data(table, fields, values, "id", id_value, tree)
        tk.Button(frame, text="Update", command=update_callback).pack()

    # Button to Delete data
    def create_delete_button(table=table, tree=tree):
        def delete_callback():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select error", "Select a row to delete.")
                return
            id_value = tree.item(selected[0])['values'][0]
            delete_data(table, "id", id_value, tree)
        tk.Button(frame, text="Delete", command=delete_callback).pack()

    # Create Add, Update, and Delete buttons
    create_add_button()
    create_update_button()
    create_delete_button()

root.mainloop()

# Close database connection when done
conn.close()
