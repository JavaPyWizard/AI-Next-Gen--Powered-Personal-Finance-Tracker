import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import os
from PIL import Image, ImageTk
from finance_tracker import FinanceTracker  


class FinanceTrackerGUI:
    def __init__(self, root, finance_tracker):
        self.root = root
        self.ft = finance_tracker
        self.setup_main_window()
        
    def setup_main_window(self):
        self.root.title("Personal Finance Tracker")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure style
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="Personal Finance Tracker", style='Header.TLabel').pack(side=tk.LEFT)
        ttk.Label(header_frame, text=f"User: {self.ft.user_manager.current_user['username']}").pack(side=tk.RIGHT)
        
        # Main content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Navigation sidebar
        self.setup_sidebar()
        
        # Display default view
        self.show_dashboard()
        
    def setup_sidebar(self):
        sidebar_frame = ttk.Frame(self.content_frame, width=150)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_frame.pack_propagate(False)
        
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Add Transaction", self.show_add_transaction),
            ("View Transactions", self.show_transactions),
            ("Reports", self.show_reports),
            ("Graphs", self.show_graphs),
            ("Anomalies", self.show_anomalies),
            ("Recommendations", self.show_recommendations),
            ("Import/Export", self.show_import_export),
            ("Logout", self.logout)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(sidebar_frame, text=text, command=command)
            btn.pack(fill=tk.X, padx=5, pady=2)
        
    def clear_content(self):
        for widget in self.content_frame.winfo_children()[1:]:
            widget.destroy()
    
    def show_dashboard(self):
        self.clear_content()
        
        dashboard_frame = ttk.Frame(self.content_frame)
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary cards
        summary_frame = ttk.Frame(dashboard_frame)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Get summary data
        total_spent = sum(t['amount'] for t in self.ft.txns)
        avg_spent = total_spent / len(self.ft.txns) if self.ft.txns else 0
        categories = len(set(t['category'] for t in self.ft.txns))
        
        summary_data = [
            ("Total Spent", f"₹{total_spent:,.2f}"),
            ("Avg. Transaction", f"₹{avg_spent:,.2f}"),
            ("Categories", str(categories)),
            ("Transactions", str(len(self.ft.txns)))
        ]
        
        for i, (title, value) in enumerate(summary_data):
            card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=1)
            card.grid(row=0, column=i, padx=5, sticky='nsew')
            summary_frame.columnconfigure(i, weight=1)
            
            ttk.Label(card, text=title, style='Header.TLabel').pack(pady=(5, 0))
            ttk.Label(card, text=value, font=('Arial', 14)).pack(pady=(0, 5))
        
        # Recent transactions
        recent_frame = ttk.LabelFrame(dashboard_frame, text="Recent Transactions", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('date', 'description', 'amount', 'category')
        self.recent_tree = ttk.Treeview(
            recent_frame, 
            columns=columns, 
            show='headings',
            selectmode='browse'
        )
        
        for col in columns:
            self.recent_tree.heading(col, text=col.title())
            self.recent_tree.column(col, width=100)
        
        self.recent_tree.column('description', width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)
        self.recent_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate with recent transactions
        recent_txns = sorted(self.ft.txns, key=lambda x: x['date'], reverse=True)[:10]
        for txn in recent_txns:
            date_str = txn['date'].strftime('%Y-%m-%d') if hasattr(txn['date'], 'strftime') else txn['date']
            self.recent_tree.insert('', tk.END, values=(
                date_str,
                txn['description'],
                f"₹{txn['amount']:,.2f}",
                txn['category']
            ))
    
    def show_add_transaction(self):
        self.clear_content()
        
        add_frame = ttk.Frame(self.content_frame)
        add_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(add_frame, text="Add New Transaction", style='Header.TLabel').pack(pady=(0, 10))
        
        # Form fields
        form_frame = ttk.Frame(add_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(form_frame, text="Amount (₹):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.desc_entry = ttk.Entry(form_frame)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.date_entry = ttk.Entry(form_frame)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.category_var = tk.StringVar()
        categories = sorted(set(t['category'] for t in self.ft.txns))
        self.category_combo = ttk.Combobox(
            form_frame, 
            textvariable=self.category_var,
            values=categories
        )
        self.category_combo.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(add_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add Transaction", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_form).pack(side=tk.LEFT, padx=5)
    
    def add_transaction(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
                
            description = self.desc_entry.get().strip()
            if not description:
                messagebox.showerror("Error", "Description cannot be empty")
                return
                
            date_str = self.date_entry.get().strip()
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                return
                
            category = self.category_combo.get().strip()
            if not category:
                category = self.ft._categorize(description)
                self.category_var.set(category)
                
            # Check for large transaction
            if amount > 50000:
                confirm = messagebox.askyesno(
                    "Confirm Large Transaction",
                    f"Confirm transaction of ₹{amount:,.2f}?"
                )
                if not confirm:
                    return
            
            # Add the transaction
            self.ft.add_transaction(amount, description, date)
            messagebox.showinfo("Success", "Transaction added successfully!")
            self.clear_form()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {str(e)}")
    
    def clear_form(self):
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.category_var.set('')
    
    def show_transactions(self):
        self.clear_content()
        
        trans_frame = ttk.Frame(self.content_frame)
        trans_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(trans_frame, text="Transaction History", style='Header.TLabel').pack(pady=(0, 10))
        
        # Filters
        filter_frame = ttk.Frame(trans_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        
        self.filter_category_var = tk.StringVar()
        categories = ['All'] + sorted(set(t['category'] for t in self.ft.txns))
        ttk.Combobox(
            filter_frame, 
            textvariable=self.filter_category_var,
            values=categories,
            state='readonly',
            width=15
        ).pack(side=tk.LEFT, padx=5)
        self.filter_category_var.set('All')
        
        ttk.Label(filter_frame, text="Date Range:").pack(side=tk.LEFT, padx=5)
        
        self.start_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="to").pack(side=tk.LEFT, padx=5)
        
        self.end_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Apply", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        
        # Transaction table
        table_frame = ttk.Frame(trans_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('date', 'description', 'amount', 'category')
        self.trans_tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show='headings',
            selectmode='extended'
        )
        
        for col in columns:
            self.trans_tree.heading(col, text=col.title())
            self.trans_tree.column(col, width=100)
        
        self.trans_tree.column('description', width=200)
        self.trans_tree.column('amount', anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.trans_tree.yview)
        self.trans_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.trans_tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate with all transactions
        self.update_transaction_table()
        
        # Action buttons
        action_frame = ttk.Frame(trans_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
    
    def update_transaction_table(self):
        # Clear existing data
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        
        # Apply filters
        filtered = self.ft.txns.copy()
        
        # Category filter
        category = self.filter_category_var.get()
        if category != 'All':
            filtered = [t for t in filtered if t['category'] == category]
        
        # Date range filter
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                filtered = [t for t in filtered if 
                          (t['date'] if isinstance(t['date'], datetime) 
                          else datetime.strptime(t['date'], '%Y-%m-%d')) >= start]
            except ValueError:
                pass
                
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                filtered = [t for t in filtered if 
                          (t['date'] if isinstance(t['date'], datetime) 
                          else datetime.strptime(t['date'], '%Y-%m-%d')) <= end]
            except ValueError:
                pass
        
        # Sort by date (newest first)
        filtered.sort(key=lambda x: x['date'], reverse=True)
        
        # Add to treeview
        for txn in filtered:
            date_str = txn['date'].strftime('%Y-%m-%d') if hasattr(txn['date'], 'strftime') else txn['date']
            self.trans_tree.insert('', tk.END, values=(
                date_str,
                txn['description'],
                f"₹{txn['amount']:,.2f}",
                txn['category']
            ))
    
    def apply_filters(self):
        self.update_transaction_table()
    
    def delete_selected(self):
        selected = self.trans_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No transactions selected")
            return
            
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(selected)} selected transactions?"
        )
        if not confirm:
            return
            
        # Get the selected transaction details
        to_delete = []
        for item in selected:
            values = self.trans_tree.item(item, 'values')
            date_str = values[0]
            description = values[1]
            amount = float(values[2][1:].replace(',', ''))
            
            # Find matching transaction in the list
            for txn in self.ft.txns:
                txn_date = txn['date'].strftime('%Y-%m-%d') if hasattr(txn['date'], 'strftime') else txn['date']
                if (txn_date == date_str and 
                    txn['description'] == description and 
                    txn['amount'] == amount):
                    to_delete.append(txn)
                    break
        
        # Remove from the list
        for txn in to_delete:
            self.ft.txns.remove(txn)
        
        # Save changes
        self.ft._save_user_transactions()
        messagebox.showinfo("Success", f"Deleted {len(to_delete)} transactions")
        self.update_transaction_table()
    
    def edit_selected(self):
        selected = self.trans_tree.selection()
        if len(selected) != 1:
            messagebox.showwarning("Warning", "Please select exactly one transaction to edit")
            return
            
        values = self.trans_tree.item(selected[0], 'values')
        date_str = values[0]
        description = values[1]
        amount = float(values[2][1:].replace(',', ''))
        
        # Find the transaction in the list
        original_txn = None
        for txn in self.ft.txns:
            txn_date = txn['date'].strftime('%Y-%m-%d') if hasattr(txn['date'], 'strftime') else txn['date']
            if (txn_date == date_str and 
                txn['description'] == description and 
                txn['amount'] == amount):
                original_txn = txn
                break
        
        if not original_txn:
            messagebox.showerror("Error", "Transaction not found")
            return
            
        # Create edit dialog
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("Edit Transaction")
        edit_dialog.transient(self.root)
        edit_dialog.grab_set()
        
        ttk.Label(edit_dialog, text="Edit Transaction", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(edit_dialog, text="Amount (₹):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        amount_entry = ttk.Entry(edit_dialog)
        amount_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        amount_entry.insert(0, original_txn['amount'])
        
        ttk.Label(edit_dialog, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        desc_entry = ttk.Entry(edit_dialog)
        desc_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        desc_entry.insert(0, original_txn['description'])
        
        ttk.Label(edit_dialog, text="Date (YYYY-MM-DD):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        date_entry = ttk.Entry(edit_dialog)
        date_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        date_entry.insert(0, original_txn['date'].strftime('%Y-%m-%d') if hasattr(original_txn['date'], 'strftime') else original_txn['date'])
        
        ttk.Label(edit_dialog, text="Category:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
        category_var = tk.StringVar()
        categories = sorted(set(t['category'] for t in self.ft.txns))
        category_combo = ttk.Combobox(
            edit_dialog, 
            textvariable=category_var,
            values=categories
        )
        category_combo.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        category_var.set(original_txn['category'])
        
        def save_changes():
            try:
                # Validate inputs
                new_amount = float(amount_entry.get())
                if new_amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                    
                new_desc = desc_entry.get().strip()
                if not new_desc:
                    messagebox.showerror("Error", "Description cannot be empty")
                    return
                    
                new_date_str = date_entry.get().strip()
                try:
                    new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                    return
                    
                new_category = category_var.get().strip()
                if not new_category:
                    new_category = self.ft._categorize(new_desc)
                    category_var.set(new_category)
                
                # Check for large transaction
                if new_amount > 50000:
                    confirm = messagebox.askyesno(
                        "Confirm Large Transaction",
                        f"Confirm transaction of ₹{new_amount:,.2f}?"
                    )
                    if not confirm:
                        return
                
                # Update the transaction
                original_txn['amount'] = new_amount
                original_txn['description'] = new_desc
                original_txn['date'] = new_date
                original_txn['category'] = new_category
                
                # Save changes
                self.ft._save_user_transactions()
                messagebox.showinfo("Success", "Transaction updated successfully!")
                edit_dialog.destroy()
                self.update_transaction_table()
                
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update transaction: {str(e)}")
        
        ttk.Button(edit_dialog, text="Save", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)
    
    def show_reports(self):
        self.clear_content()
        
        report_frame = ttk.Frame(self.content_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(report_frame, text="Financial Reports", style='Header.TLabel').pack(pady=(0, 10))
        
        # Report type selection
        type_frame = ttk.Frame(report_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Report Type:").pack(side=tk.LEFT, padx=5)
        
        self.report_type_var = tk.StringVar(value='monthly')
        ttk.Radiobutton(
            type_frame, 
            text="Monthly", 
            variable=self.report_type_var, 
            value='monthly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame, 
            text="Weekly", 
            variable=self.report_type_var, 
            value='weekly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame, 
            text="By Category", 
            variable=self.report_type_var, 
            value='category'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(type_frame, text="Generate", command=self.generate_report).pack(side=tk.LEFT, padx=10)
        
        # Report display area
        self.report_text = tk.Text(
            report_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            font=('Courier', 10)
        )
        scrollbar = ttk.Scrollbar(report_frame, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_text.pack(fill=tk.BOTH, expand=True)
    
    def generate_report(self):
        report_type = self.report_type_var.get()
        report = self.ft.gen_report(report_type)
        
        if 'error' in report:
            self.report_text.config(state=tk.NORMAL)
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, f"Error: {report['error']}")
            self.report_text.config(state=tk.DISABLED)
            return
            
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        
        # Header
        self.report_text.insert(tk.END, f"{report_type.capitalize()} Spending Report\n")
        self.report_text.insert(tk.END, "="*50 + "\n\n")
        
        # Report data - fixed key access
        for item in report['data']:
            # Handle different report types
            if report_type == 'category':
                period = item['Category']
            else:
                # For weekly/monthly reports, use the first key that isn't 'Amount (₹)'
                keys = [k for k in item.keys() if k != 'Amount (₹)']
                period = item[keys[0]] if keys else 'N/A'
            
            amount = item['Amount (₹)']
            self.report_text.insert(tk.END, f"{period:<20} ₹{amount:>10,.2f}\n")
        
        # Statistics
        self.report_text.insert(tk.END, "\nStatistics\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        stats = report['statistics']
        self.report_text.insert(tk.END, f"Total Spending:      ₹{stats['total']:>10,.2f}\n")
        self.report_text.insert(tk.END, f"Average Transaction: ₹{stats['average']:>10,.2f}\n")
        self.report_text.insert(tk.END, f"Transaction Count:   {stats['count']:>10}\n")
        
        # Insights
        if report['insights']:
            self.report_text.insert(tk.END, "\nInsights\n")
            self.report_text.insert(tk.END, "-"*50 + "\n")
            
            # Largest transactions
            if report['insights']['largest']:
                self.report_text.insert(tk.END, "\nTop 3 Largest Transactions:\n")
                for i, tx in enumerate(report['insights']['largest'], 1):
                    self.report_text.insert(tk.END, 
                        f"{i}. {tx['date']}: {tx['description'][:30]}... - ₹{tx['amount']:,.2f}\n")
            
            # Anomalies
            if report['insights']['anomalies']:
                self.report_text.insert(tk.END, "\nUnusual Transactions Detected:\n")
                for i, anomaly in enumerate(report['insights']['anomalies'][:3], 1):
                    self.report_text.insert(tk.END, 
                        f"{i}. {anomaly['date']}: {anomaly['description'][:30]}... - ₹{anomaly['amount']:,.2f}\n")
            
            # Recommendations
            if report['insights']['recommendations']:
                self.report_text.insert(tk.END, "\nSavings Recommendations:\n")
                for cat, advice in report['insights']['recommendations'].items():
                    self.report_text.insert(tk.END, f"- {cat.title()}: {advice}\n")
        
        self.report_text.config(state=tk.DISABLED)
    
    def show_graphs(self):
        self.clear_content()
        
        graph_frame = ttk.Frame(self.content_frame)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(graph_frame, text="Financial Graphs", style='Header.TLabel').pack(pady=(0, 10))
        
        # Graph type selection
        type_frame = ttk.Frame(graph_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Graph Type:").pack(side=tk.LEFT, padx=5)
        
        self.graph_type_var = tk.StringVar(value='monthly')
        ttk.Radiobutton(
            type_frame, 
            text="Monthly", 
            variable=self.graph_type_var, 
            value='monthly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame, 
            text="Weekly", 
            variable=self.graph_type_var, 
            value='weekly'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_frame, 
            text="Daily", 
            variable=self.graph_type_var, 
            value='daily'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(type_frame, text="Generate", command=self.generate_graphs).pack(side=tk.LEFT, padx=10)
        
        # Graph display area
        self.graph_canvas_frame = ttk.Frame(graph_frame)
        self.graph_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Generate default graphs
        self.generate_graphs()
    
    def generate_graphs(self):
        # Clear previous graphs
        for widget in self.graph_canvas_frame.winfo_children():
            widget.destroy()
            
        if not self.ft.txns:
            ttk.Label(self.graph_canvas_frame, text="No transactions to display").pack()
            return
            
        try:
            # Generate the graphs
            self.ft.gen_graphs(self.graph_type_var.get())
            
            # Display the generated graphs
            user_folder = self.ft.user_manager._get_user_folder(self.ft.user_manager.current_user['username'])
            graph_dir = os.path.join(user_folder, 'graphs')
            
            # Show category pie chart
            pie_img = Image.open(os.path.join(graph_dir, 'category_pie.png'))
            pie_img = pie_img.resize((400, 400), Image.LANCZOS)
            pie_photo = ImageTk.PhotoImage(pie_img)
            
            pie_label = ttk.Label(self.graph_canvas_frame, image=pie_photo)
            pie_label.image = pie_photo
            pie_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Show period trends
            period = self.graph_type_var.get()
            trends_img = Image.open(os.path.join(graph_dir, f'{period}_trends.png'))
            trends_img = trends_img.resize((500, 300), Image.LANCZOS)
            trends_photo = ImageTk.PhotoImage(trends_img)
            
            trends_label = ttk.Label(self.graph_canvas_frame, image=trends_photo)
            trends_label.image = trends_photo
            trends_label.pack(side=tk.LEFT, padx=5, pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate graphs: {str(e)}")
    
    def show_anomalies(self):
        self.clear_content()
        
        anomaly_frame = ttk.Frame(self.content_frame)
        anomaly_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(anomaly_frame, text="Anomaly Detection", style='Header.TLabel').pack(pady=(0, 10))
        
        anomalies = self.ft.detect_anomalies()
        if not anomalies:
            ttk.Label(anomaly_frame, text="No unusual transactions found").pack()
            return
            
        ttk.Label(
            anomaly_frame, 
            text=f"Found {len(anomalies)} unusual transactions (based on spending patterns):"
        ).pack(pady=(0, 10))
        
        # Anomaly list
        list_frame = ttk.Frame(anomaly_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        for i, anomaly in enumerate(anomalies, 1):
            anomaly_item = ttk.LabelFrame(
                list_frame, 
                text=f"Anomaly #{i}",
                padding=10
            )
            anomaly_item.pack(fill=tk.X, pady=5)
            
            date_str = anomaly['date'].strftime('%Y-%m-%d') if hasattr(anomaly['date'], 'strftime') else anomaly['date']
            ttk.Label(anomaly_item, text=f"Date: {date_str}").pack(anchor=tk.W)
            ttk.Label(anomaly_item, text=f"Amount: ₹{anomaly['amount']:,.2f}").pack(anchor=tk.W)
            ttk.Label(anomaly_item, text=f"Category: {anomaly['category']}").pack(anchor=tk.W)
            ttk.Label(anomaly_item, text=f"Description: {anomaly['description']}").pack(anchor=tk.W)
            
            # Action buttons
            action_frame = ttk.Frame(anomaly_item)
            action_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Button(
                action_frame, 
                text="Change Category", 
                command=lambda a=anomaly: self.change_anomaly_category(a)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                action_frame, 
                text="Delete Transaction", 
                command=lambda a=anomaly: self.delete_anomaly(a)
            ).pack(side=tk.LEFT, padx=5)
    
    def change_anomaly_category(self, anomaly):
        new_category = simpledialog.askstring(
            "Change Category",
            f"New category for transaction on {anomaly['date']}:\n{anomaly['description']}",
            parent=self.root
        )
        
        if new_category and new_category.strip():
            # Find and update the transaction
            for txn in self.ft.txns:
                if (txn['description'] == anomaly['description'] and 
                    txn['date'] == anomaly['date'] and 
                    txn['amount'] == anomaly['amount']):
                    txn['category'] = new_category.strip()
                    break
            
            self.ft._save_user_transactions()
            messagebox.showinfo("Success", "Category updated successfully")
            self.show_anomalies()
    
    def delete_anomaly(self, anomaly):
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete transaction on {anomaly['date']}:\n{anomaly['description']}\nAmount: ₹{anomaly['amount']:,.2f}?"
        )
        
        if confirm:
            # Remove the transaction
            self.ft.txns = [
                txn for txn in self.ft.txns 
                if not (txn['description'] == anomaly['description'] and 
                       txn['date'] == anomaly['date'] and 
                       txn['amount'] == anomaly['amount'])
            ]
            self.ft._save_user_transactions()
            messagebox.showinfo("Success", "Transaction deleted")
            self.show_anomalies()
    
    def show_recommendations(self):
        self.clear_content()
        
        rec_frame = ttk.Frame(self.content_frame)
        rec_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(rec_frame, text="Savings Recommendations", style='Header.TLabel').pack(pady=(0, 10))
        
        recs = self.ft.get_recommendations()
        if not recs:
            ttk.Label(rec_frame, text="No recommendations yet (add more transactions)").pack()
            return
            
        for category, advice in recs.items():
            rec_card = ttk.Frame(rec_frame, relief=tk.RIDGE, borderwidth=1, padding=10)
            rec_card.pack(fill=tk.X, pady=5)
            
            ttk.Label(rec_card, text=category.title(), style='Header.TLabel').pack(anchor=tk.W)
            ttk.Label(rec_card, text=advice).pack(anchor=tk.W)
    
    def show_import_export(self):
        self.clear_content()
        
        io_frame = ttk.Frame(self.content_frame)
        io_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(io_frame, text="Import/Export Data", style='Header.TLabel').pack(pady=(0, 10))
        
        # Import section
        import_frame = ttk.LabelFrame(io_frame, text="Import Transactions", padding=10)
        import_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(import_frame, text="Import transactions from CSV file:").pack(anchor=tk.W)
        ttk.Label(import_frame, text="Required columns: amount, description, date").pack(anchor=tk.W)
        
        ttk.Button(
            import_frame, 
            text="Browse...", 
            command=self.import_csv
        ).pack(pady=5)
        
        # Export section
        export_frame = ttk.LabelFrame(io_frame, text="Export Transactions", padding=10)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(export_frame, text="Export transactions to:").pack(anchor=tk.W)
        
        button_frame = ttk.Frame(export_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(
            button_frame, 
            text="CSV File", 
            command=lambda: self.export_csv(False)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Password-protected ZIP", 
            command=lambda: self.export_csv(True)
        ).pack(side=tk.LEFT, padx=5)
    
    def import_csv(self):
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
            
        try:
            if self.ft.import_csv(filepath):
                messagebox.showinfo("Success", f"Imported {len(self.ft.txns)} transactions")
                self.show_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def export_csv(self, protected=False):
        if not self.ft.txns:
            messagebox.showwarning("Warning", "No transactions to export")
            return
            
        default_name = f"transactions_{datetime.now().strftime('%Y%m%d')}"
        if protected:
            filepath = filedialog.asksaveasfilename(
                title="Save Protected Export",
                defaultextension=".zip",
                initialfile=f"{default_name}.zip",
                filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")]
            )
        else:
            filepath = filedialog.asksaveasfilename(
                title="Save CSV File",
                defaultextension=".csv",
                initialfile=f"{default_name}.csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
        
        if not filepath:
            return
            
        try:
            if protected:
                password = simpledialog.askstring(
                    "Password Protection",
                    "Set export password (min 6 characters):",
                    show='*'
                )
                
                if not password or len(password) < 6:
                    messagebox.showerror("Error", "Password must be at least 6 characters")
                    return
                
                # First export CSV
                temp_csv = os.path.join(self.ft.dirs['data'], 'temp_export.csv')
                self.ft.export_csv(temp_csv)
                
                # Then create protected ZIP
                from zipfile import ZipFile, ZIP_DEFLATED
                with ZipFile(filepath, 'w') as z:
                    z.write(
                        temp_csv, 
                        arcname='transactions.csv',
                        compress_type=ZIP_DEFLATED,
                        pwd=password.encode()
                    )
                os.remove(temp_csv)
                messagebox.showinfo("Success", f"Protected export saved to {filepath}")
            else:
                if self.ft.export_csv(filepath):
                    messagebox.showinfo("Success", f"Exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def logout(self):
        self.ft.user_manager.logout()
        self.root.destroy()
        messagebox.showinfo("Logged Out", "You have been logged out successfully")

class LoginGUI:
    def __init__(self, root, user_manager):
        self.root = root
        self.user_manager = user_manager
        self.setup_login_window()
        
    def setup_login_window(self):
        self.root.title("Personal Finance Tracker - Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="Personal Finance Tracker", style='Header.TLabel').pack(pady=(0, 20))
        
        # Login form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.username_entry = ttk.Entry(form_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.password_entry = ttk.Entry(form_frame, show='*')
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sign Up", command=self.show_signup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground='red')
        self.status_label.pack()
        
        # Focus username field
        self.username_entry.focus()
    
    def login(self):
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get()
        
        if not username or not password:
            self.status_label.config(text="Username and password required")
            return
            
        result = self.user_manager.verify_user(username, password)
        
        if result['status'] == 'success':
            self.root.destroy()
            root = tk.Tk()
            finance_tracker = FinanceTracker(self.user_manager)
            FinanceTrackerGUI(root, finance_tracker)
            root.mainloop()
        else:
            self.status_label.config(text=result.get('message', 'Login failed'))
    
    def show_signup(self):
        signup_window = tk.Toplevel(self.root)
        signup_window.title("Sign Up")
        signup_window.geometry("400x350")
        signup_window.transient(self.root)
        signup_window.grab_set()
        
        ttk.Label(signup_window, text="Create New Account", style='Header.TLabel').pack(pady=(10, 20))
        
        # Form fields
        form_frame = ttk.Frame(signup_window)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Username (4-20 alphanumeric chars):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.new_username_entry = ttk.Entry(form_frame)
        self.new_username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Password (min 8 chars with uppercase,").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Label(form_frame, text="number, and special character):").grid(row=2, column=0, padx=5, pady=0, sticky=tk.E)
        self.new_password_entry = ttk.Entry(form_frame, show='*')
        self.new_password_entry.grid(row=1, column=1, padx=5, pady=5, rowspan=2)
        
        ttk.Label(form_frame, text="Confirm Password:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.confirm_password_entry = ttk.Entry(form_frame, show='*')
        self.confirm_password_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(signup_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Create Account", command=self.create_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=signup_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.signup_status_label = ttk.Label(signup_window, text="", foreground='red')
        self.signup_status_label.pack()
    
    def create_account(self):
        username = self.new_username_entry.get().strip().lower()
        password = self.new_password_entry.get()
        confirm = self.confirm_password_entry.get()
        
        # Validate inputs
        if not username or not password:
            self.signup_status_label.config(text="Username and password required")
            return
            
        if password != confirm:
            self.signup_status_label.config(text="Passwords don't match")
            return
            
        # Check username requirements
        if not (4 <= len(username) <= 20 and username.isalnum()):
            self.signup_status_label.config(text="Username must be 4-20 alphanumeric characters")
            return
            
        # Check password strength
        if len(password) < 8:
            self.signup_status_label.config(text="Password must be at least 8 characters")
            return
            
        if not any(c.isupper() for c in password):
            self.signup_status_label.config(text="Password must contain an uppercase letter")
            return
            
        if not any(c.isdigit() for c in password):
            self.signup_status_label.config(text="Password must contain a number")
            return
            
        if password.isalnum():
            self.signup_status_label.config(text="Password must contain a special character")
            return
            
        # Create the account
        result = self.user_manager.create_user(username, password)
        
        if result['status'] == 'success':
            messagebox.showinfo("Success", "Account created successfully! Please login.")
            self.new_username_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            self.signup_status_label.config(text="")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)
            self.password_entry.focus()
            self.root.focus()
        else:
            self.signup_status_label.config(text=result.get('message', 'Account creation failed'))

def main():
    root = tk.Tk()
    user_manager = UserManager()
    LoginGUI(root, user_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
