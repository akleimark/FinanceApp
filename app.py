#!/usr/bin/env python3
import sys
import sqlite3
import matplotlib
matplotlib.use('Qt5Agg')  # Använd Qt5 backend för Matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox, QMenuBar, QAction, QStackedWidget
from PyQt5.QtGui import QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime

class FinanceApp(QMainWindow):
    start_x = 300
    start_y = 300
    end_x = 1200
    end_y = 700

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ekonomi-app")
        self.setGeometry(self.start_x, self.start_y, self.end_x, self.end_y)

        FinanceApp.init_db(self)
        self.init_ui()

        # Ladda transaktionerna när appen startar
        self.load_transactions()

        # Rita grafen när appen startar
        self.plot_graph()

    @staticmethod
    def init_db(self):
        """Skapar en SQLite-databas om den inte finns och ber om ett startvärde om den är tom."""
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                balance REAL NOT NULL
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM transactions")
        if cursor.fetchone()[0] == 0:
            start_balance, ok = QInputDialog.getDouble(self, "Startsaldo", "Ange startvärde för saldot:", 0, 0, 1000000,
                                                       2)
            if ok:
                cursor.execute("INSERT INTO transactions (type, amount, date, time, balance) VALUES (?, ?, ?, ?, ?)",
                               ("Startsaldo", start_balance, datetime.now().strftime("%Y-%m-%d"),
                                datetime.now().strftime("%H:%M:%S"), start_balance))
                conn.commit()

        conn.close()

    def init_ui(self):
        """Skapar meny och UI."""
        self.create_menu()

        self.stacked_widget = QStackedWidget()  # Skapar en QStackedWidget för att hålla olika vyer
        self.setCentralWidget(self.stacked_widget)

        self.transaction_table_widget = QWidget()
        self.graph_widget = QWidget()

        self.init_transaction_table_ui()
        self.init_graph_ui()

        # Lägg till widgets i stacked widget
        self.stacked_widget.addWidget(self.transaction_table_widget)
        self.stacked_widget.addWidget(self.graph_widget)

        self.apply_dark_theme()  # Använd mörkt tema

    def create_menu(self):
        """Skapar menyraden."""
        menubar = self.menuBar()

        transaction_menu = menubar.addMenu("Transaktioner")

        deposit_action = QAction("Insättning", self)
        deposit_action.triggered.connect(self.add_deposit)  # Visa insättningsdialog
        transaction_menu.addAction(deposit_action)

        withdraw_action = QAction("Uttag", self)
        withdraw_action.triggered.connect(self.add_withdrawal)  # Visa uttagsdialog
        transaction_menu.addAction(withdraw_action)

        history_action = QAction("Historik", self)
        history_action.triggered.connect(lambda: self.show_widget(0))  # Visa historik
        transaction_menu.addAction(history_action)

        graph_action = QAction("Visa graf", self)
        graph_action.triggered.connect(lambda: self.show_widget(1))  # Visa grafen
        transaction_menu.addAction(graph_action)

    def show_widget(self, index):
        """Visar den valda widgeten i stacked widget."""
        self.stacked_widget.setCurrentIndex(index)

    def init_transaction_table_ui(self):
        """Skapa transaktionstabellen och lägg till den i stacked widget."""
        layout = QVBoxLayout()

        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(5)
        self.transaction_table.setHorizontalHeaderLabels(["Typ", "Belopp (kr)", "Datum", "Tid", "Nuvärde (kr)"])

        load_button = QAction("Ladda Historik", self)
        load_button.triggered.connect(self.load_transactions)
        self.transaction_table.addAction(load_button)

        layout.addWidget(self.transaction_table)

        self.transaction_table_widget.setLayout(layout)

    def init_graph_ui(self):
        """Skapa grafen och lägg till den i stacked widget."""
        layout = QVBoxLayout()

        self.graph_canvas = FigureCanvas(plt.figure(figsize=(6, 4)))  # Skapa en canvas för grafen

        layout.addWidget(self.graph_canvas)

        self.graph_widget.setLayout(layout)

    def load_transactions(self):
        """Laddar transaktioner från databasen och visar dem i tabellen."""
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT type, amount, date, time, balance FROM transactions ORDER BY date ASC, time ASC")
        transactions = cursor.fetchall()
        conn.close()

        self.transaction_table.setRowCount(len(transactions))
        for row_idx, (trans_type, amount, date, time, balance) in enumerate(transactions):
            self.transaction_table.setItem(row_idx, 0, QTableWidgetItem(trans_type))
            self.transaction_table.setItem(row_idx, 1, QTableWidgetItem(f"{amount:.2f} kr"))
            self.transaction_table.setItem(row_idx, 2, QTableWidgetItem(date))
            self.transaction_table.setItem(row_idx, 3, QTableWidgetItem(time))
            self.transaction_table.setItem(row_idx, 4, QTableWidgetItem(f"{balance:.2f} kr"))

    def plot_graph(self):
        """Ritar en graf över saldot."""
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()

        # Hämta det senaste saldot (det första startvärdet)
        cursor.execute("SELECT balance FROM transactions ORDER BY id ASC LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        # Om ingen transaktion finns, använd ett default startvärde (t.ex. 0 eller annat valfritt värde)
        if result:
            balance = result[0]
        else:
            balance = 0  # Eller något annat lämpligt default-värde

        # Börja lista med startvärdet
        dates = ["Start"]
        balances = [balance]

        # Hämta alla transaktioner och deras saldon
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date, time, balance FROM transactions ORDER BY date ASC, time ASC")
        transactions = cursor.fetchall()
        conn.close()

        # Lägg till alla transaktioner i grafen
        for date, time, balance in transactions:
            dates.append(f"{date} {time}")
            balances.append(balance)

        # Skapa graf
        plt.clf()  # Rensa tidigare graf
        plt.plot(dates, balances, marker='o', color='b')  # Linje med punkter för saldot över tid
        plt.xlabel('Datum och Tid')
        plt.ylabel('Saldo (kr)')
        plt.title('Utveckling av saldo')

        # Sätt bakgrundsfärg till mörk
        plt.gcf().set_facecolor('#2e2e2e')  # Mörk bakgrund på hela grafen
        plt.gca().set_facecolor('#2e2e2e')  # Mörk bakgrund på axlarna

        # Sätt textfärger
        plt.gca().tick_params(axis='x', colors='white')  # X-axelns färg
        plt.gca().tick_params(axis='y', colors='white')  # Y-axelns färg
        plt.xlabel('Datum och Tid', color='white')
        plt.ylabel('Saldo (kr)', color='white')
        plt.title('Utveckling av saldo', color='white')

        # Förbättra läsbarheten för datum och tid
        plt.xticks(rotation=45, ha="right", color='white')

        self.graph_canvas.draw()  # Uppdatera grafen på canvasen

    def apply_dark_theme(self):
        """Använd ett mörkt tema för hela applikationen."""
        dark_palette = QPalette()

        # Ställ in bakgrundsfärger
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))  # Bakgrundsfärg för fönstret
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # Textfärg för fönstret
        dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))  # Basfärg för inmatningsfält
        dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))  # Alternativ bakgrundsfärg
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))  # Textfärg för tips
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))  # Färgen på tooltiptext
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))  # Textfärg för alla widgetar
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))  # Färg på knappar
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # Textfärg på knappar
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))  # Färgen på ljust text
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))  # Färg på länkar

        # Ställ in paletten för hela applikationen
        self.setPalette(dark_palette)

    def add_deposit(self):
        """Funktion för att lägga till en insättning."""
        amount, ok = QInputDialog.getDouble(self, "Insättning", "Ange belopp för insättning:", 0, 0, 1000000, 2)
        if ok:
            if amount <= 0:
                QMessageBox.warning(self, "Ogiltigt belopp", "Beloppet måste vara större än 0!")
                return
            conn = sqlite3.connect("finance.db")
            cursor = conn.cursor()
            current_time = datetime.now()

            # Hämta senaste saldo
            cursor.execute("SELECT balance FROM transactions ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                last_balance = result[0]
            else:
                last_balance = 8600  # Om ingen transaktion finns, starta från 8600

            # Uppdatera saldot
            new_balance = last_balance + amount

            # Sätt in transaktionen i databasen
            cursor.execute("INSERT INTO transactions (type, amount, date, time, balance) VALUES (?, ?, ?, ?, ?)",
                           ("Insättning", amount, current_time.strftime("%Y-%m-%d"), current_time.strftime("%H:%M:%S"), new_balance))
            conn.commit()
            conn.close()
            self.load_transactions()
            self.plot_graph()  # Uppdatera grafen efter insättning

    def add_withdrawal(self):
        """Funktion för att lägga till ett uttag."""
        amount, ok = QInputDialog.getDouble(self, "Uttag", "Ange belopp för uttag:", 0, 0, 1000000, 2)
        if ok:
            if amount <= 0:
                QMessageBox.warning(self, "Ogiltigt belopp", "Beloppet måste vara större än 0!")
                return
            conn = sqlite3.connect("finance.db")
            cursor = conn.cursor()
            current_time = datetime.now()

            # Hämta senaste saldo
            cursor.execute("SELECT balance FROM transactions ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                last_balance = result[0]
            else:
                last_balance = 8600  # Om ingen transaktion finns, starta från 8600

            # Uppdatera saldot
            new_balance = last_balance - amount

            # Sätt in transaktionen i databasen
            cursor.execute("INSERT INTO transactions (type, amount, date, time, balance) VALUES (?, ?, ?, ?, ?)",
                           ("Uttag", amount, current_time.strftime("%Y-%m-%d"), current_time.strftime("%H:%M:%S"), new_balance))
            conn.commit()
            conn.close()
            self.load_transactions()
            self.plot_graph()  # Uppdatera grafen efter uttag

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceApp()
    window.show()
    sys.exit(app.exec())
