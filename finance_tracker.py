import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os
import json
import warnings
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Union

warnings.filterwarnings('ignore')

class FinanceTracker:
    def __init__(self, user_manager):
        """Initialize finance tracker with INR only"""
        self.user_manager = user_manager
        self.txns = []
        self.dirs = {
            'data': "data_uploads",
            'graphs': "financial_graphs",
            'models': "ai_models"
        }
        self.currency = "₹"
        self.max_daily_spend = 100000  # ₹100,000 daily limit
        self.max_csv_size = 1024*1024  # 1MB file size limit
        self.max_description_length = 200
        self._setup_secure_dirs()
        self._load_user_transactions()

    def _setup_secure_dirs(self):
        """Create and secure data directories"""
        for d in self.dirs.values():
            try:
                os.makedirs(d, exist_ok=True)
                os.chmod(d, 0o700)
            except Exception as e:
                print(f"Security Warning: Could not secure directory {d}: {str(e)}")

    def _load_user_transactions(self):
        """Load transactions for current user"""
        if self.user_manager.current_user:
            self.txns = [
                {
                    **txn,
                    'date': datetime.strptime(txn['date'], "%Y-%m-%d") if isinstance(txn['date'], str) else txn['date']
                } 
                for txn in self.user_manager.current_user.get('transactions', [])
            ]

    def _save_user_transactions(self):
        """Save transactions for current user"""
        if self.user_manager.current_user:
            self.user_manager.current_user['transactions'] = [
                {
                    **txn,
                    'date': txn['date'].strftime("%Y-%m-%d") if isinstance(txn['date'], datetime) else txn['date']
                }
                for txn in self.txns
            ]
            self.user_manager.save_user_data()

    def _categorize(self, description):
        """Enhanced keyword-based categorization"""
        desc = description.lower().strip()
        
        categories = {
            'food': ['swiggy', 'zomato', 'grocery', 'restaurant'],
            'transport': ['uber', 'ola', 'petrol', 'fuel'],
            'housing': ['rent', 'electricity', 'maintenance'],
            'shopping': ['amazon', 'flipkart', 'myntra'],
            'health': ['hospital', 'pharmacy', 'medicine'],
            'entertainment': ['movie', 'netflix', 'concert'],
            'travel': ['hotel', 'flight', 'vacation'],
            'education': ['course', 'tuition', 'books']
        }
        
        for category, keywords in categories.items():
            if any(kw in desc for kw in keywords):
                return category
        return 'other'

    def add_transaction(self, amount: float, description: str, 
                        date: Union[str, datetime]) -> str:
        """Add transaction with validation"""
        try:
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if len(description) > self.max_description_length:
                raise ValueError(f"Description exceeds {self.max_description_length} chars")
            
            if isinstance(date, str):
                date = datetime.strptime(date, "%Y-%m-%d")
                
            # Daily spending limit check
            today = datetime.now().date()
            daily_total = sum(
                t['amount'] for t in self.txns 
                if isinstance(t['date'], datetime) and 
                t['date'].date() == today
            )
            if daily_total + amount > self.max_daily_spend:
                raise ValueError(f"Daily limit exceeded (₹{daily_total}/{self.max_daily_spend})")
                
            category = self._categorize(description)
            new_txn = {
                'amount': round(float(amount)),
                'description': description,
                'date': date,
                'category': category
            }
            
            if amount > 50000:  # ₹50k threshold
                confirm = input(f"Confirm large transaction of ₹{amount}? (y/n): ")
                if confirm.lower() != 'y':
                    raise ValueError("Transaction cancelled")
            
            self.txns.append(new_txn)
            self._save_user_transactions()
            return category
            
        except Exception as e:
            print(f"Error adding transaction: {e}")
            raise

    def detect_anomalies(self, threshold: float = 2.5) -> List[Dict]:
        """Detect unusual transactions using Z-score"""
        if len(self.txns) < 5:
            return []
            
        amounts = np.array([t['amount'] for t in self.txns])
        mean = np.mean(amounts)
        std = np.std(amounts)
        
        anomalies = []
        for txn in self.txns:
            z_score = (txn['amount'] - mean) / std
            if abs(z_score) > threshold:
                anomalies.append(txn)
        return anomalies

    def predict_spending(self, months: int = 3) -> Dict:
        """Predict future spending with moving average"""
        try:
            if len(self.txns) < 6:
                return {"error": "Need at least 6 months of data"}
                
            df = pd.DataFrame(self.txns)
            monthly = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
            avg = monthly.tail(3).mean()
            
            preds = {}
            last_date = monthly.index[-1].to_timestamp()
            for i in range(1, months + 1):
                dt = last_date + relativedelta(months=i)
                preds[dt.strftime("%Y-%m")] = {
                    'amount': avg * (1 + 0.02 * i),  # 2% monthly inflation
                    'confidence': max(0.7 - (i * 0.15), 0.4)
                }
            return preds
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

    def get_recommendations(self) -> Dict:
        """Generate savings recommendations"""
        try:
            if not self.txns:
                return {}
                
            df = pd.DataFrame(self.txns)
            cat_spend = df.groupby('category')['amount'].sum().to_dict()
            
            recs = {}
            thresholds = {
                'food': (10000, "Cook at home more often"),
                'transport': (5000, "Use public transport"),
                'shopping': (8000, "Wait 24h before purchases")
            }
            
            for cat, (threshold, suggestion) in thresholds.items():
                if cat in cat_spend and cat_spend[cat] > threshold:
                    recs[cat] = suggestion
            
            return recs
        except Exception as e:
            print(f"Recommendation error: {e}")
            return {}

    def gen_report(self, period: str = 'monthly') -> Dict:
        """Generate financial report with proper serialization for all data types"""
        try:
            if not self.txns:
                return {"error": "No transactions available"}

            # Create DataFrame with serializable dates
            df = pd.DataFrame([{
                'amount': txn['amount'],
                'description': txn['description'],
                'date': txn['date'].strftime('%Y-%m-%d') if hasattr(txn['date'], 'strftime') else txn['date'],
                'category': txn['category']
            } for txn in self.txns])

            # Generate period-based report
            if period == 'monthly':
                report_data = df.groupby(df['date'].str[:7])['amount'].sum()  # YYYY-MM
                period_name = "Month"
            elif period == 'weekly':
                df['week'] = pd.to_datetime(df['date']).dt.strftime('%Y-W%U')
                report_data = df.groupby('week')['amount'].sum()
                period_name = "Week"
            else:  # category
                report_data = df.groupby('category')['amount'].sum()
                period_name = "Category"

            # Convert to display-friendly format
            report_df = pd.DataFrame({
                period_name: report_data.index,
                'Amount (₹)': report_data.values.round(2)
            })

            # Prepare full report
            result = {
                'period': period,
                'data': report_df.to_dict('records'),
                'statistics': {
                    'total': float(df['amount'].sum().round(2)),
                    'average': float(df['amount'].mean().round(2)),
                    'count': len(df),
                    'periods': len(report_data)
                },
                'insights': {
                    'largest': df.nlargest(3, 'amount').to_dict('records'),
                    'anomalies': [{
                        **txn,
                        'date': txn['date'] if isinstance(txn['date'], str) else txn['date'].strftime('%Y-%m-%d')
                    } for txn in self.detect_anomalies()],
                    'predictions': self.predict_spending(),
                    'recommendations': self.get_recommendations()
                }
            }

            return result

        except Exception as e:
            return {"error": f"Report generation failed: {str(e)}"}

    def gen_graphs(self, period: str = 'monthly'):
        """Generate graphs in user-specific directory"""
        if not self.user_manager.current_user:
            print("No user logged in")
            return
            
        try:
            # Get user-specific directory paths
            user_folder = self.user_manager._get_user_folder(self.user_manager.current_user['username'])
            graph_dir = os.path.join(user_folder, 'graphs')
            os.makedirs(graph_dir, exist_ok=True)
            
            df = pd.DataFrame(self.txns)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            plt.style.use('ggplot')
            plt.rcParams['figure.facecolor'] = 'white'

            # 1. Category Pie Chart
            plt.figure(figsize=(10, 8))
            df.groupby('category')['amount'].sum().plot.pie(
                autopct=lambda p: f'{p:.1f}%\n(₹{p*sum(df["amount"])/100:.0f})'
            )
            plt.title("Spending by Category")
            plt.savefig(os.path.join(graph_dir, 'category_pie.png'))
            plt.close()

            # 2. Time Period Trends
            if period == 'monthly':
                period_col = df['date'].dt.to_period('M').astype(str)
            elif period == 'weekly':
                period_col = df['date'].dt.to_period('W').astype(str)
            else:  # daily
                period_col = df['date'].dt.strftime('%Y-%m-%d')

            period_totals = df.groupby(period_col)['amount'].sum()
            plt.figure(figsize=(12, 6))
            period_totals.plot.bar(color='#4CAF50', width=0.8)
            plt.title(f"{period.capitalize()} Spending")
            plt.savefig(os.path.join(graph_dir, f'{period}_trends.png'))
            plt.close()

            # 3. Cumulative Spending
            plt.figure(figsize=(12, 6))
            df.set_index('date')['amount'].cumsum().plot()
            plt.title("Cumulative Spending")
            plt.savefig(os.path.join(graph_dir, 'cumulative_line.png'))
            plt.close()

            # 4. Rolling Average
            plt.figure(figsize=(12, 6))
            df.set_index('date')['amount'].rolling('30D').mean().plot()
            plt.title("30-Day Rolling Average")
            plt.savefig(os.path.join(graph_dir, 'rolling_avg.png'))
            plt.close()

            print(f"✓ Graphs saved to {graph_dir}")
            
        except Exception as e:
            print(f"Error generating graphs: {e}")
            

    def import_csv(self, filepath: str) -> bool:
        """Import transactions from CSV"""
        try:
            df = pd.read_csv(filepath)
            required = {'amount', 'description', 'date'}
            if not required.issubset(df.columns):
                print("CSV needs amount, description, date columns")
                return False
                
            new_txns = []
            for _, row in df.iterrows():
                try:
                    new_txns.append({
                        'amount': float(row['amount']),
                        'description': str(row['description']),
                        'date': datetime.strptime(row['date'], "%Y-%m-%d"),
                        'category': self._categorize(row['description'])
                    })
                except Exception as e:
                    print(f"Skipping row {_}: {e}")
                    continue
                    
            self.txns.extend(new_txns)
            self._save_user_transactions()
            print(f"Imported {len(new_txns)} transactions")
            return True
            
        except Exception as e:
            print(f"Import failed: {e}")
            return False

    def export_csv(self, filepath: str) -> bool:
        """Export transactions to CSV"""
        try:
            df = pd.DataFrame(self.txns)
            df.to_csv(filepath, index=False)
            print(f"Exported {len(df)} transactions")
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def show_menu(self):
        """Main menu with session and permission checks"""
        if not self.user_manager.check_session():
            print("\nSession expired. Please log in again.")
            return
            
        menu_options = {
            '1': ('Add Transaction', self._add_txn_flow),
            '2': ('View Report', self._show_report),
            '3': ('Detect Anomalies', self._show_anomalies),
            '4': ('Get Recommendations', self._show_recs),
            '5': ('Predict Spending', self._show_preds),
            '6': ('Generate Graphs', self._graph_generation_flow),
            '7': ('Import CSV', self._import_csv_flow),
            '8': ('Export Data', self._export_csv_flow),
            '9': ('Logout', lambda: None)
        }
        
        while True:
            try:
                print(f"\n=== Finance Tracker ({self.currency}) ===")
                for num, (name, _) in menu_options.items():
                    print(f"{num}. {name}")
                    
                choice = input("\nSelect option (1-9): ").strip()
                
                if choice == '9':
                    self.user_manager.logout()
                    print("Logged out successfully!")
                    return
                    
                if choice not in menu_options:
                    print("Invalid choice! Please enter 1-9")
                    continue
                    
                # Verify session before each action
                if not self.user_manager.check_session():
                    print("\nSession expired. Please log in again.")
                    return
                    
                # Execute selected action
                menu_options[choice][1]()
                
            except KeyboardInterrupt:
                print("\nOperation cancelled")
            except Exception as e:
                print(f"\nError: {str(e)}")
                self._log_activity(f"Menu error: {str(e)}", "ERROR")

    def _add_txn_flow(self):
        """Interactive transaction entry flow (INR only)"""
        print("\nAdd Transaction")
        print("-"*20)
        while True:
            try:
                # Get amount with validation
                while True:
                    amt_input = input("Amount (₹): ")
                    try:
                        amt = float(amt_input)
                        if amt <= 0:
                            print("Amount must be positive")
                            continue
                        break
                    except ValueError:
                        print("Please enter a valid number")
                
                # Get description
                desc = input("Description: ").strip()
                while not desc:
                    print("Description cannot be empty")
                    desc = input("Description: ").strip()
                
                # Get date with validation
                date_in = input("Date (YYYY-MM-DD) [today]: ").strip()
                if not date_in:
                    date = datetime.now()
                else:
                    try:
                        date = datetime.strptime(date_in, "%Y-%m-%d")
                    except ValueError:
                        print("Invalid date format. Using today's date")
                        date = datetime.now()
                
                # Add transaction (INR only)
                cat = self.add_transaction(amt, desc, date)
                print(f"\n✓ Added ₹{amt:.2f} as {cat}")
                print(f"{desc} on {date.strftime('%d %b %Y')}")
                
                if input("\nAdd another? (y/n): ").lower() != 'y':
                    break
                    
            except KeyboardInterrupt:
                print("\nTransaction cancelled")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _show_report(self):
        """Display formatted financial report in console"""
        if not self.txns:
            print("No transactions available to generate report!")
            return

        try:
            # Get report parameters
            period = input("Report period (daily/weekly/monthly) [monthly]: ").strip().lower()
            period = period if period in ['daily', 'weekly', 'monthly'] else 'monthly'

            # Generate the report
            report = self.gen_report(period)
            
            if 'error' in report:
                print(f"\nError: {report['error']}")
                return

            # Print the main report table
            print(f"\n{'='*40}")
            print(f"{period.capitalize()} Spending Report".center(40))
            print('='*40)
            
            # Convert report data to DataFrame for nice formatting
            report_df = pd.DataFrame(report['data'])
            print(report_df.to_string(index=False, float_format=lambda x: f"₹{x:.2f}"))

            # Print statistics
            print(f"\n{' Statistics ':-^40}")
            stats = report['statistics']
            print(f"Total Spending: ₹{stats['total']:.2f}")
            print(f"Average Transaction: ₹{stats['average']:.2f}")
            print(f"Number of Transactions: {stats['count']}")
            print(f"Number of {period.capitalize()}s: {stats['periods']}")

            # Print insights if available
            if report['insights']:
                print(f"\n{' Insights ':-^40}")
                
                # Largest transactions
                if report['insights']['largest']:
                    print("\nTop 3 Largest Transactions:")
                    for i, tx in enumerate(report['insights']['largest'], 1):
                        print(f"{i}. {tx['date']}: {tx['description']} - ₹{tx['amount']:.2f}")

                # Anomalies
                if report['insights']['anomalies']:
                    print("\n⚠️ Unusual Transactions Detected:")
                    for i, anomaly in enumerate(report['insights']['anomalies'][:3], 1):
                        print(f"{i}. {anomaly['date']}: {anomaly['description']} - ₹{anomaly['amount']:.2f}")

                # Recommendations
                if report['insights']['recommendations']:
                    print("\n💡 Savings Recommendations:")
                    for cat, advice in report['insights']['recommendations'].items():
                        print(f"- {cat.title()}: {advice}")

            print("\n" + "="*40)

        except Exception as e:
            print(f"\nError displaying report: {str(e)}")

    def _show_anomalies(self):
        """Display and manage anomaly detection results"""
        anomalies = self.detect_anomalies()
        if not anomalies:
            print("No unusual transactions found")
            return
            
        print(f"\nFound {len(anomalies)} unusual transactions:")
        for i, t in enumerate(anomalies, 1):
            print(f"\n{i}. {t['date']}")
            print(f"   {t['description']}")
            print(f"   Amount: {self.currency}{t['amount']:.2f}")
            print(f"   Category: {t['category']}")
            
            action = input("\n[a] Keep, [c] Change category, [d] Delete, [s] Skip: ").lower()
            
            if action == 'c':
                new_cat = input(f"New category (current: {t['category']}): ").strip()
                if new_cat:
                    # Update the transaction in the main list
                    for txn in self.txns:
                        if (txn['description'] == t['description'] and 
                            txn['date'] == t['date'] and 
                            txn['amount'] == t['amount']):
                            txn['category'] = new_cat
                            break
                    self._save_user_transactions()
                    print("Category updated")
            elif action == 'd':
                # Remove the transaction
                self.txns = [
                    txn for txn in self.txns 
                    if not (txn['description'] == t['description'] and 
                           txn['date'] == t['date'] and 
                           txn['amount'] == t['amount'])
                ]
                self._save_user_transactions()
                print("Transaction deleted")
            elif action == 's':
                continue
                
        print("\nAnomaly review complete")

    def _show_recs(self):
        """Display personalized recommendations"""
        recs = self.get_recommendations()
        if not recs:
            print("No recommendations yet (add more transactions)")
            return
            
        print("\nSavings Recommendations:")
        for cat, advice in recs.items():
            print(f"\n{cat.title()}:")
            print(f"→ {advice}")

    def _show_preds(self):
        """Display spending predictions"""
        months = input("Months to predict (1-12) [3]: ").strip()
        try:
            months = int(months) if months.isdigit() and 1 <= int(months) <= 12 else 3
        except:
            months = 3
            
        preds = self.predict_spending(months)
        if 'error' in preds:
            print(preds['error'])
            return
            
        print(f"\nFuture Spending Predictions (next {months} months):")
        for month, data in preds.items():
            print(f"\n{month}:")
            print(f"Expected: {self.currency}{data['amount']:.2f}")
            print(f"Confidence: {data.get('confidence', 1)*100:.0f}%")

    def _graph_generation_flow(self):
        """Guide user through graph generation"""
        if not self.txns:
            print("No transactions to visualize")
            return
            
        period = input("Graph period (daily/weekly/monthly) [monthly]: ").strip().lower()
        period = period if period in ['daily', 'weekly', 'monthly'] else 'monthly'
        
        print(f"Generating {period} graphs...")
        self.gen_graphs(period)
        
    def _import_csv_flow(self):
        """Secure CSV import process with validation"""
        if not self.user_manager.check_session():
            print("\nSession expired. Please log in again.")
            return
            
        print("\nCSV Import Requirements:")
        print("- Columns: amount,description,date")
        print(f"- Max size: {self.max_csv_size/1024:.0f}KB")
        print("- UTF-8 encoding recommended")
        
        filepath = input("Path to CSV file: ").strip('"')
        
        try:
            # Security validations
            if not os.path.exists(filepath):
                raise ValueError("File not found")
                
            if os.path.islink(filepath):
                raise ValueError("Symbolic links not allowed")
                
            if os.path.getsize(filepath) > self.max_csv_size:
                raise ValueError(f"File exceeds {self.max_csv_size/1024:.0f}KB limit")
                    
            # Process import
            if self.import_csv(filepath):
                print(f"Successfully imported {len(self.txns)} transactions")
                self._log_activity(f"Imported data from {os.path.basename(filepath)}")
                
        except Exception as e:
            print(f"\nImport failed: {str(e)}")
            self._log_activity(f"Import failed: {str(e)}", "ERROR")

    def _export_csv_flow(self):
        """Secure export with optional encryption"""
        if not self.user_manager.check_session():
            print("\nSession expired. Please log in again.")
            return
            
        if not self.txns:
            print("No transactions to export")
            return
            
        print("\nExport Options:")
        print("1. Standard CSV")
        print("2. Password-protected ZIP")
        choice = input("Select export format (1-2): ").strip()
        
        filepath = input("Output path/filename: ").strip('"')
        if not filepath.endswith('.csv'):
            filepath += '.csv'
            
        try:
            # Validate path
            dirname = os.path.dirname(filepath)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
                
            # Handle existing file
            if os.path.exists(filepath):
                confirm = input("File exists. Overwrite? (y/n): ").lower()
                if confirm != 'y':
                    return
                    
            # Perform export
            if choice == '1':
                if self.export_csv(filepath):
                    print(f"Exported to {filepath}")
                    self._log_activity(f"Exported data to {filepath}")
                    
            elif choice == '2':
                from zipfile import ZipFile, ZIP_DEFLATED
                import getpass
                
                pwd = getpass.getpass("Set export password: ")
                if len(pwd) < 6:
                    raise ValueError("Password must be at least 6 characters")
                    
                # First export CSV
                temp_csv = os.path.join(self.dirs['data'], 'temp_export.csv')
                self.export_csv(temp_csv)
                
                # Then create protected ZIP
                zip_path = filepath.replace('.csv', '.zip')
                with ZipFile(zip_path, 'w') as z:
                    z.write(
                        temp_csv, 
                        arcname='transactions.csv',
                        compress_type=ZIP_DEFLATED,
                        pwd=pwd.encode()
                    )
                os.remove(temp_csv)
                print(f"Protected export saved to {zip_path}")
                self._log_activity(f"Created protected export {zip_path}")
                
        except Exception as e:
            print(f"\nExport failed: {str(e)}")
            self._log_activity(f"Export failed: {str(e)}", "ERROR")

    def _log_activity(self, action: str, level: str = "INFO"):
        """Enhanced activity logging with security levels"""
        if not hasattr(self, '_activity_log'):
            self._activity_log = os.path.join(self.dirs['data'], 'activity.log')
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': self.user_manager.current_user['username'] 
                if self.user_manager.current_user else 'unknown',
            'action': action,
            'level': level,
            'ip': os.environ.get('REMOTE_ADDR', 'local')
        }
        
        try:
            # Rotate log if over 1MB
            if os.path.exists(self._activity_log) and \
            os.path.getsize(self._activity_log) > 1024*1024:
                rotated = f"{self._activity_log}.{datetime.now().strftime('%Y%m%d')}"
                os.rename(self._activity_log, rotated)
                
            # Write new entry
            with open(self._activity_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"Warning: Failed to log activity - {str(e)}")