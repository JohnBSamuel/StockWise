import decimal
import re
import sys
from tkinter import messagebox
import mysql.connector
from PIL import Image
from customtkinter import *

print("""
System Started...
""")

app = CTk()
app.geometry("500x400")
set_appearance_mode("dark")
set_default_color_theme("blue")
app.title("DBMS")

frame = CTkFrame(master=app)
img_label = CTkLabel(master=app)
wallet_frame = CTkFrame(master=app)
port = CTkFrame(master=app)
stock_frame = CTkFrame(master=app)

def connect_to_database():
    try:
        with open("database_credentials.txt", "r") as file:
            lines = file.readlines()
            credentials = {}
            for line in lines:
                key, value = line.strip().split(": ")
                credentials[key] = value
            return mysql.connector.connect(
                host=credentials["Host"],
                user=credentials["User"],
                password=credentials["Password"],
                database=credentials["Database"]
            )
    except FileNotFoundError:
        print("Database credentials file not found.")
        sys.exit()
    except Exception as e:
        print(f"Failed to connect to the database: {str(e)}")
        sys.exit()

connection = connect_to_database()
cursor = connection.cursor()

def get_wallet_balance(user_id):
    cursor.execute("SELECT balance FROM wallets WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def update_wallet_balance(user_id, new_balance):
    sql = "UPDATE wallets SET balance = %s WHERE user_id = %s"
    val = (new_balance, user_id)
    cursor.fetchall()  # Clear any pending results
    cursor.execute(sql, val)
    connection.commit()

def clear_frames():
    global frames_to_destroy
    frames_to_destroy = [widget for widget in app.winfo_children() if "frame" in widget.winfo_name()]
    for f in frames_to_destroy:
        f.destroy()

def add_money_to_wallet(user_id, amount):
    current_balance = get_wallet_balance(user_id)
    if current_balance is not None:
        try:
            amount_decimal = decimal.Decimal(amount)
        except decimal.InvalidOperation:
            messagebox.showerror("Error", "Please enter a valid number")
            return
        new_balance = current_balance + amount_decimal
        update_wallet_balance(user_id, new_balance)
    else:
        messagebox.showerror("Error", "User wallet not found")

def add(userid):
    new_bal = CTkInputDialog(text="Enter Amount To Add", title="Balance").get_input()
    if new_bal is None:
        return
    add_money_to_wallet(userid, new_bal)

def check_shares(user_id):
    sql = ("SELECT c.company_name, s.shares_owned FROM shares s "
           "JOIN companies c ON s.company_id = c.company_id WHERE user_id = %s")
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()
    
    storage = {
        "Tata Motors": "TATA",
        "Infosys": "INFO",
        "Reliance Industries": "RELIANCE",
        "ICICI Bank": "ICICI",
        "HDFC Ltd": "HDFC"
    }
    
    return {storage[company]: shares for company, shares in results} if results else {}

def update_user_shares(user_id, company_id, new_share_count):
    sql = "UPDATE shares SET shares_owned = %s WHERE user_id = %s AND company_id = %s"
    val = (new_share_count, user_id, company_id)
    cursor.execute(sql, val)
    connection.commit()

def get_stock_price(company_id):
    cursor.execute("SELECT stock_price FROM companies WHERE company_id = %s", (company_id,))
    result = cursor.fetchone()
    return result[0] if result else 0.0

def add_shares_to_portfolio(user_id, company_id, shares):
    sql = "INSERT INTO shares (user_id, company_id, shares_owned) VALUES (%s, %s, %s)"
    val = (user_id, company_id, shares)
    cursor.execute(sql, val)
    connection.commit()

def get_user_shares(user_id, company_id):
    cursor.execute("SELECT shares_owned FROM shares WHERE user_id = %s AND company_id = %s", (user_id, company_id))
    result = cursor.fetchone()
    return result[0] if result else 0

def buy_shares(user_id, company):
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}
    company_id = ids[company]
    
    shares_to_buy = CTkInputDialog(text="Enter Number of Shares To Buy", title=company).get_input()
    if not shares_to_buy:
        return
    
    shares_to_buy = int(shares_to_buy)
    stock_price = get_stock_price(company_id)
    purchase_amount = shares_to_buy * float(stock_price)
    wallet_balance = float(get_wallet_balance(user_id))
    
    if wallet_balance >= purchase_amount:
        new_balance = wallet_balance - purchase_amount
        update_wallet_balance(user_id, new_balance)
        
        current_shares = get_user_shares(user_id, company_id)
        if current_shares > 0:
            new_shares = current_shares + shares_to_buy
            update_user_shares(user_id, company_id, new_shares)
        else:
            add_shares_to_portfolio(user_id, company_id, shares_to_buy)
        
        messagebox.showinfo("Done", f"{company} Shares Bought Successfully")
        clear_frames()
        logged_in(user_id)
    else:
        messagebox.showerror("Error", "Insufficient balance to make the purchase.")

def remove_shares_from_portfolio(user_id, company_id, shares):
    current_shares = get_user_shares(user_id, company_id)
    if current_shares >= shares:
        update_user_shares(user_id, company_id, current_shares - shares)
    else:
        messagebox.showerror("Error", "You do not have enough shares to make the sale.")

def sell_shares(user_id, company):
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}
    company_id = ids[company]
    
    shares_to_sell = CTkInputDialog(text="Enter Number of Shares To Sell", title=company).get_input()
    if not shares_to_sell:
        return
    
    shares_to_sell = int(shares_to_sell)
    user_shares = get_user_shares(user_id, company_id)
    
    if user_shares >= shares_to_sell:
        stock_price = float(get_stock_price(company_id))
        sale_amount = shares_to_sell * stock_price
        new_balance = float(get_wallet_balance(user_id)) + sale_amount
        update_wallet_balance(user_id, new_balance)
        remove_shares_from_portfolio(user_id, company_id, shares_to_sell)
        
        messagebox.showinfo("Done", f"Sold {shares_to_sell} shares of {company}")
        clear_frames()
        logged_in(user_id)
    else:
        messagebox.showerror("Error", "Insufficient shares to complete the sale")

def out():
    for widget in [wallet_frame, port, stock_frame]:
        try:
            widget.destroy()
        except:
            pass
    page1()

def view(user_id, company):
    global top
    try:
        top.destroy()
    except:
        pass
    
    top = CTkToplevel(app)
    top.geometry("300x300")
    top.title(company)
    
    comp = CTkImage(Image.open(f"./images/{company}.png"), size=(200, 220))
    CTkLabel(master=top, image=comp).pack()
    
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}
    price = get_stock_price(ids[company])
    CTkLabel(master=top, text=f"₹ {price}", font=("Roboto", 16)).pack()
    
    CTkButton(master=top, text="Buy", width=120, height=40, hover_color="green",
             command=lambda: buy_shares(user_id, company)).place(x=20, y=250)
    CTkButton(master=top, text="Sell", width=120, height=40, hover_color="red",
             command=lambda: sell_shares(user_id, company)).place(x=160, y=250)

def logged_in(userid):
    global wallet_frame, port, stock_frame
    
    balance = get_wallet_balance(userid)
    wallet_frame = CTkFrame(master=app, width=220, height=50)
    wallet_frame.grid(row=0, column=0, padx=10, pady=10)
    
    CTkLabel(master=wallet_frame, text="Balance: ₹", font=("Roboto", 15)).place(x=20, y=10)
    display = f"{balance/1e6:.2f} M" if balance >= 1e6 else f"{balance/1e3:.2f} K" if balance >= 1e3 else str(balance)
    CTkLabel(master=wallet_frame, text=display, font=("Roboto", 15)).place(x=90, y=10)
    CTkButton(master=wallet_frame, text="Add +", width=60, height=20, command=lambda: add(userid)).place(x=150, y=13)
    
    port = CTkFrame(master=app, width=220, height=320)
    port.grid(row=1, column=0, padx=10, pady=(0, 10))
    CTkLabel(master=port, text="Portfolio", font=("Roboto", 24)).place(x=60, y=5)
    
    shares_data = check_shares(userid)
    for i, (share, qty) in enumerate(shares_data.items()):
        suitcase = CTkImage(dark_image=Image.open("./images/bagw.png"),
                          light_image=Image.open("./images/bagb.png"), size=(20, 15))
        CTkLabel(master=port, image=suitcase).place(x=8, y=58 + 40*i)
        CTkLabel(master=port, text=f"{share}: {qty} shares", font=("Roboto", 16)).place(x=30, y=60 + 40*i)
    
    stock_frame = CTkFrame(master=app, width=250, height=380)
    stock_frame.grid(row=0, column=1, rowspan=2)
    CTkLabel(master=stock_frame, text="Watchlist", font=("Roboto", 24)).place(x=80, y=5)
    
    stocks = [
        {"name": "TATA Motors", "id": "TATA"},
        {"name": "InfoSys", "id": "INFO"},
        {"name": "Reliance", "id": "RELIANCE"},
        {"name": "ICICI Bank", "id": "ICICI"},
        {"name": "HDFC Bank", "id": "HDFC"}
    ]
    
    for i, stock in enumerate(stocks):
        CTkLabel(master=stock_frame, text=stock["name"], font=("Roboto", 16)).place(x=80, y=60 + 60*i)
        eye = CTkImage(Image.open("./images/eye.png"), size=(17, 10))
        CTkButton(master=stock_frame, text="View", width=80, height=20, hover_color="purple",
                 image=eye, command=lambda s=stock["id"]: view(userid, s)).place(x=90, y=95 + 60*i)
    
    CTkButton(master=port, text="Logout", command=out,
             image=CTkImage(Image.open("./images/logout.png"), size=(20, 22))).place(x=40, y=280)

def validate_inputs(user, aadhar, pan, phone, pass1, pass2, balance):
    if not all([user, aadhar, pan, phone, pass1, pass2, balance]):
        messagebox.showerror("Error", "All fields are required")
        return False
    
    if not re.match(r'^\d{12}$', aadhar):
        messagebox.showerror("Error", "Invalid Aadhar number")
        return False
    
    if not re.match(r'^[A-Z]{5}\d{4}[A-Z]$', pan):
        messagebox.showerror("Error", "Invalid PAN number")
        return False
    
    if not re.match(r'^[789]\d{9}$', phone):
        messagebox.showerror("Error", "Invalid phone number")
        return False
    
    if pass1 != pass2:
        messagebox.showerror("Error", "Passwords do not match")
        return False
    
    return True

def AddUser(full_name, pan, aadhar, phone, password, balance):
    try:
        cursor.execute(
            "INSERT INTO users (full_name, pan_number, aadhar_number, phone_number, password) "
            "VALUES (%s, %s, %s, %s, %s)",
            (full_name, pan, aadhar, phone, password)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO wallets (user_id, balance) VALUES (%s, %s)",
            (user_id, decimal.Decimal(balance))
        )
        connection.commit()
        messagebox.showinfo("Success", "Registration successful")
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False

def login_check(phone, password):
    cursor.execute("SELECT user_id FROM users WHERE phone_number = %s AND password = %s", (phone, password))
    if result := cursor.fetchone():
        clear_frames()
        logged_in(result[0])
    else:
        messagebox.showerror("Error", "Invalid credentials")

def backfnc():
    clear_frames()
    page1()

def login():
    global frame
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)
    
    CTkLabel(master=frame, text="StockUp", font=("Roboto", 24)).place(x=65, y=20)
    CTkLabel(master=frame, image=CTkImage(Image.open("./images/logo.png"), size=(50, 50))).place(x=15, y=10)
    
    entries = {
        "phone": CTkEntry(master=frame, placeholder_text="Phone Number"),
        "password": CTkEntry(master=frame, placeholder_text="Password", show="*")
    }
    for i, (key, entry) in enumerate(entries.items()):
        entry.place(x=30, y=150 + 40*i)
    
    CTkButton(master=frame, text="Login",
             command=lambda: login_check(entries["phone"].get(), entries["password"].get())).place(x=30, y=230)
    CTkButton(master=frame, text="Back", command=backfnc, hover_color="orange").place(x=30, y=270)

def signup():
    global frame
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)
    
    CTkLabel(master=frame, text="StockUp", font=("Roboto", 24)).place(x=65, y=20)
    CTkLabel(master=frame, image=CTkImage(Image.open("./images/logo.png"), size=(50, 50))).place(x=15, y=10)
    
    fields = [
        CTkEntry(master=frame, placeholder_text="Full Name"),
        CTkEntry(master=frame, placeholder_text="Aadhar Number"),
        CTkEntry(master=frame, placeholder_text="PAN Card"),
        CTkEntry(master=frame, placeholder_text="Phone Number"),
        CTkEntry(master=frame, placeholder_text="Password", show="*"),
        CTkEntry(master=frame, placeholder_text="Confirm Password", show="*"),
        CTkEntry(master=frame, placeholder_text="Initial Balance")
    ]
    
for i, field in enumerate(fields):
    field.place(x=30, y=60 + 40 * i)

CTkButton(
    master=frame,
    text="Sign Up",
    command=lambda: validate_inputs(
        *[f.get() for f in fields]
    ) and AddUser(*([f.get() for f in fields[:5]] + [fields[6].get()])),
).place(x=30, y=335)

CTkButton(master=frame, text="Back", command=backfnc, hover_color="orange").place(x=30, y=370)


def page1():
    global frame, img_label, wallet_frame, port, stock_frame
    
    try:
        frame.destroy()
        img_label.destroy()
        wallet_frame.destroy()
        port.destroy()
        stock_frame.destroy()
    except NameError:
        pass  # Ignore if these variables are not yet defined
    
    img = CTkImage(Image.open("./images/login.jpg"), size=(300, 400))
    img_label = CTkLabel(master=app, image=img, text="")
    img_label.grid(row=0, column=0)
    
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)
    
    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)
    
    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)
    
    l_img = CTkImage(Image.open("./images/loginImg.png"), size=(21, 21))
    login_button = CTkButton(master=frame, text=" Login ", command=login, image=l_img)
    login_button.place(x=30, y=140)
    
    s_img = CTkImage(Image.open("./images/signup.png"), size=(25, 21))
    sign_btn = CTkButton(master=frame, text="Sign-Up", command=signup, image=s_img)
    sign_btn.place(x=30, y=180)
    
    close_btn = CTkButton(master=frame, text="Close App", command=close, fg_color="green", hover_color="red")
    close_btn.place(x=30, y=230)
    
    t = CTkImage(dark_image=Image.open("./images/dark.png"), light_image=Image.open("./images/light.png"), size=(66, 34))
    theme = CTkButton(master=frame, text="", hover=False, width=66, height=34, image=t, fg_color="transparent", command=change_theme)
    theme.place(x=60, y=270)

# Initialize the app
app = CTk()

page1()
app.mainloop()

print("\nApp Closed...\n")
