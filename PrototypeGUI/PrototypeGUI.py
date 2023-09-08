from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.filedialog import asksaveasfile
from jira import JIRA
import csv
import os
from hashlib import blake2b

credentials_file = '../credentials.txt'

def get_child_issues_of_epic(jira, epic_key):
    child_issues = jira.search_issues(
        jql_str=f'"Epic Link" = {epic_key}'
    )
    return child_issues

def get_asset_object_ids(assets):
    return [asset.objectId for asset in assets]

def get_asset_info(pricing_file, object_id):
    with open(pricing_file, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row["objectId"]) == object_id:
                return row["Name"], float(row["Price"])
    return None, None

def move_issue_to_column(jira, issue_key,column_name):
    transition_id=None

    #Get the ID of the transition for moving to the target column
    transitions = jira.transitions(issue_key)
    for transition in transitions:
        if transition['name'] == column_name:
            transition_id = transition['id']
            break

    if transition_id:
        jira.transition_issue(issue_key, transition_id)
        print(f"Issue {issue_key} has been moved to '{column_name}' column.")
    else:
        print(f"Error: Column '{column_name}' not found for issue {issue_key}")

def get_jira_data(password):
    with open(credentials_file, mode='r') as file:
        hash_obj = blake2b()
        hash_obj.update(password.encode())
        hashed_pw = hash_obj.hexdigest()
        if hashed_pw != file.readline().strip():
            messagebox.showerror("Error", "Password does not match!")
            exit(0)
        email = file.readline().strip()
        token = file.readline().strip()

    # JIRA instance URL
    jiraOptions = {'server': "https://team8-if.atlassian.net"}

    jira = JIRA(options=jiraOptions, basic_auth=(email, token))

    # Jira search query to find Epics in the Done column
    jql_query = 'project = "Foundry Digital - IF" AND type = Epic AND status = Done'

    # Search for Epics that match the JQL query
    epics_in_done = jira.search_issues(jql_str=jql_query)

    #csv_file = "jira_issues.csv"

    file_types = [('CSV files', '*.csv'), ('All files', '*.*')]
    file_name = filedialog.asksaveasfilename(filetypes=file_types, defaultextension='.csv')

    if not file_name:
        print("No file selected.")
        return

    # Store the data in a CSV file
    with open(file_name, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Epic Name", "Child Issue Names", "Replaced Parts", "Name", "Price"])

        # Write the Epic names, linked child issue names, and Replaced Parts to the CSV file
        for epic in epics_in_done:
            child_issues = get_child_issues_of_epic(jira, epic.key)
            for issue in child_issues:
                replaced_parts = issue.fields.customfield_10090

                # If replaced_parts is empty or None, set it to an empty list
                if not replaced_parts:
                    replaced_parts = []

                replaced_parts_object_ids = get_asset_object_ids(replaced_parts)

                # Get the Name and Price of each objectId from the pricing data
                for object_id_str in replaced_parts_object_ids:
                    object_id = int(object_id_str)
                    name, price = get_asset_info("pricing.csv", object_id)

                    # Write the data to the CSV file
                    writer.writerow([epic.fields.summary, issue.fields.summary, object_id_str, name, price])

                # If there are no replaced parts, write an empty row
                if not replaced_parts_object_ids:
                    writer.writerow([epic.fields.summary, issue.fields.summary, "", "", ""])
            move_issue_to_column(jira, epic.key, "Invoice Generated")
            for issue in child_issues:
                move_issue_to_column(jira, issue.key,"Invoice Generated")

    print(f"Data has been successfully stored in {file_name}.")

    messagebox.showinfo("Success!", f"Jira issues saved to {file_name}")

def generate_credentials_file(password, email, token):
    if password != repeat_pw_entry.get():
        messagebox.showerror("Error", "Passwords do not match!")
        return

    hash_obj = blake2b()
    hash_obj.update(password.encode())
    hashed_pw = hash_obj.hexdigest()
    with open(credentials_file, mode='w') as file:
        file.writelines((hashed_pw+"\n", email+"\n", token+"\n"))
    messagebox.showinfo("Success", "Credentials file generated!")
    enter_main_screen()

def main_screen(screen_x, screen_y):
    global screen

    # Create the main screen
    screen = Tk()

    # Set the style and theme for the screen
    style = ttk.Style(screen)
    screen.tk.call("source", "forest-dark.tcl")  # Load custom theme from external file
    style.theme_use("forest-dark")

    style.configure('TButton', padding=20)  # Configure padding for buttons
    
    screen.title('Main Screen')
    screen.geometry('400x200')
    screen.resizable(False, False)
    screen.geometry('400x200+{}+{}'.format(screen_x, screen_y))

    frame = Frame(screen)

    # Create buttons for the main screen
    have_creds_button = ttk.Button(frame, text="Download Jira Data", command=lambda: get_jira_data(password_entry.get()))
    password_entry = ttk.Entry(frame, font=(16), show='')
    password_entry.insert(0, "Enter Password")
    show_password_stat = BooleanVar()
    password_entry.bind("<FocusIn>", lambda e: on_entry_click(password_entry, "Enter Password", show_password_stat))
    
    show_password = ttk.Checkbutton(frame, text="Show password", variable=show_password_stat,
                                    command=lambda: on_show_toggle(password_entry, show_password_stat, "New Password"))
    
    password_entry.grid(row=0, column=0, columnspan=2, sticky="news", pady=(20, 5))
    show_password.grid(row=1, column=0, sticky="news")
    have_creds_button.grid(row=2, column=0, sticky="e", pady=15)
    
    frame.pack()
    screen.mainloop()
    

def enter_main_screen():
    # Get the current screen coordinates
    screen_x = screen2.winfo_x()
    screen_y = screen2.winfo_y()

    # Destroy the main screen
    screen2.destroy()

    # Create the credentials entry screen
    main_screen(screen_x, screen_y)


def credentials_entry_screen(screen_x, screen_y):
    global screen2
    global token_entry
    global password_entry
    global repeat_pw_entry
    global email_entry

    # Create the credentials entry screen
    screen2 = Tk()
    screen2.withdraw()
    screen2.bell()

    # Set the style and theme for the screen
    style = ttk.Style(screen2)
    screen2.tk.call("source", "forest-dark.tcl")  # Load custom theme from external file
    style.theme_use("forest-dark")
    messagebox.showwarning("Warning", "Credentials file not found! Enter credentials...")
    screen2.deiconify()

    screen2.title('Credentials')
    screen2.geometry('400x600+{}+{}'.format(screen_x, screen_y))
    screen2.resizable(False, False)

    frame = Frame(screen2)

    # Create labels, entries, and button for the credentials entry screen
    title_label = Label(frame, text="Credentials", font=("Arial", 30))

    email_entry = ttk.Entry(frame, font=(16))
    email_entry.insert(0, "Email")
    email_entry.bind("<FocusIn>", lambda e: on_email_entry_click(email_entry, "Email"))
    email_entry.bind("<FocusOut>", lambda e: entry_leave(email_entry, "Email"))

    token_entry = ttk.Entry(frame, font=(16), show='')
    token_entry.insert(0, "Token")
    show_token_stat = BooleanVar()
    token_entry.bind("<FocusIn>", lambda e: on_entry_click(token_entry, "Token", show_token_stat))
    token_entry.bind("<FocusOut>", lambda e: entry_leave(token_entry, "Token"))

    show_token = ttk.Checkbutton(frame, text="Show token", variable=show_token_stat,
                                    command=lambda: on_show_toggle(token_entry, show_token_stat, "Token"))

    password_entry = ttk.Entry(frame, font=(16), show='')
    password_entry.insert(0, "New Password")
    show_password_stat = BooleanVar()
    password_entry.bind("<FocusIn>", lambda e: on_entry_click(password_entry, "New Password", show_password_stat))
    password_entry.bind("<FocusOut>", lambda e: entry_leave(password_entry, "New Password"))

    
    show_password = ttk.Checkbutton(frame, text="Show password", variable=show_password_stat,
                                    command=lambda: on_show_toggle(password_entry, show_password_stat, "New Password"))

    repeat_pw_entry = ttk.Entry(frame, font=(16), show='')
    repeat_pw_entry.insert(0, "Repeat New Password")
    show_repeat_pw_stat = BooleanVar()
    repeat_pw_entry.bind("<FocusIn>", lambda e: on_entry_click(repeat_pw_entry, "Repeat New Password", show_repeat_pw_stat))
    repeat_pw_entry.bind("<FocusOut>", lambda e: entry_leave(repeat_pw_entry, "Repeat New Password"))

    
    show_repeat_pw = ttk.Checkbutton(frame, text="Show password", variable=show_repeat_pw_stat,
                                    command=lambda: on_show_toggle(repeat_pw_entry, show_repeat_pw_stat, "Repeat New Password"))

    generate_button = ttk.Button(frame, text="Generate Credentials",
                                  command=lambda: generate_credentials_file(password_entry.get(), email_entry.get(), token_entry.get()))

    # Grid layout for the elements
    title_label.grid(row=0, column=0, columnspan=2, sticky="news", pady=40)
    email_entry.grid(row=1, column=1, pady=10)
    token_entry.grid(row=2, column=1, pady=(10, 5))
    show_token.grid(row=3, column=1, sticky="news", pady=(0, 10))
    password_entry.grid(row=4, column=1, pady=(10, 5))
    show_password.grid(row=5, column=1, sticky="news", pady=(0, 10))
    repeat_pw_entry.grid(row=6, column=1, pady=(10, 5))
    show_repeat_pw.grid(row=7, column=1, sticky="news")
    generate_button.grid(row=8, column=0, columnspan=2, pady=30)

    frame.pack()
    screen2.mainloop()

def on_email_entry_click(entry, default_text):
    # Clear the default text when the entry is clicked
    current_text = entry.get()
    if current_text == default_text:
        email_entry.delete('0', 'end')

def entry_leave(entry, default_text):
    current_text = entry.get()
    if len(current_text) == 0:
        entry.configure(show='')
        entry.insert(0, default_text)

def on_entry_click(entry, default_text, show_var):
    # Clear the default text and set the entry to show asterisks for token and password entries
    current_text = entry.get()
    if current_text == default_text:
        entry.delete('0', 'end')
        if not show_var.get():
            entry.configure(show='*')

def on_show_toggle(entry_widget, show_var, default_text):
    # Toggle the show/hide based on the checkbox status
    current_text = entry_widget.get()
    if show_var.get() or current_text == default_text:
        entry_widget.configure(show='')

    else:
        entry_widget.configure(show='*')


# Start the program by calling the main_screen function
if not os.path.isfile("../credentials.txt"):
    
    credentials_entry_screen(0, 0)
else:
    main_screen(0, 0)