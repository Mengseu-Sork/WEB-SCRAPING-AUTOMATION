import os
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd

# Function to choose a folder for saving all links and data files
def choose_folder(entry_folder):
    folder_selected = filedialog.askdirectory()  # Open folder dialog to choose directory
    if folder_selected:
        entry_folder.delete(0, tk.END)  # Clear the entry field
        entry_folder.insert(0, folder_selected)  # Insert the selected folder path

# Function to fetch and parse a webpage's HTML content
def fetch_and_parse(url):
    try:
        response = requests.get(url)  # Send a GET request to the URL
        response.raise_for_status()  # Raise an exception for HTTP errors (non-200 responses)
        return BeautifulSoup(response.text, "html.parser")  # Parse the HTML response using BeautifulSoup
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {e}")  # Handle errors and raise an exception

# Function to scrape links and their associated pages from a URL
def scrape_links_and_pages(base_url):
    try:
        soup = fetch_and_parse(base_url)  # Fetch and parse the base URL content
        data = {
            "URL": base_url,
            "Title": soup.title.string if soup.title else "No Title",  # Extract title or set "No Title"
            "Paragraphs": [p.get_text(strip=True) for p in soup.find_all("p")],  # Extract paragraphs
            "Linked Pages": {}  # Dictionary to store data for linked pages
        }

        # Get all linked pages (depth 1), resolve relative URLs using urljoin
        links = [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]
        unique_links = list(set(links))  # Remove duplicate links

        # Scrape each linked page
        for link in unique_links:
            try:
                child_soup = fetch_and_parse(link)  # Fetch and parse the linked page
                data["Linked Pages"][link] = {
                    "Title": child_soup.title.string if child_soup.title else "No Title",  # Title of linked page
                    "Paragraphs": [p.get_text(strip=True) for p in child_soup.find_all("p")]  # Paragraphs of linked page
                }
            except Exception as e:
                data["Linked Pages"][link] = {"Error": str(e)}  # Handle errors for each linked page

        return data  # Return scraped data
    except Exception as e:
        raise Exception(f"Error scraping {base_url}: {e}")  # Handle errors for the base URL


# Refactored save_links function to save data to JSON and CSV files
def save_links():
    try:
        folder = entry_folder.get().strip()  # Get the folder path from entry field
        if not folder or not os.path.exists(folder): 
            messagebox.showwarning("No Folder", "Please choose a folder.")  # Show warning if no folder selected
            return
        
        # Get all URL and filename pairs from user inputs
        urls_filenames = [(entry_url.get(), entry_filename.get()) for entry_url, entry_filename in zip(link_entries, filename_entries) if entry_url.get().strip() and entry_filename.get().strip()]
        if not urls_filenames: 
            messagebox.showwarning("No Data", "Please enter URLs and filenames.")  # Show warning if no data entered
            return
        
        os.makedirs(folder, exist_ok=True)  # Create the folder if it doesn't already exist
        
        # Loop through each URL and filename pair, scrape data, and save it
        for url, filename in urls_filenames:
            scraped_data = scrape_links_and_pages(url)  # Scrape data for the URL
            json_file_path = os.path.join(folder, f"{filename}.json")  # Path for the JSON file
            with open(json_file_path, 'w', encoding='utf-8') as json_file: 
                json.dump(scraped_data, json_file, indent=4, ensure_ascii=False)  # Save data to JSON file
            
            # Create a DataFrame for CSV from the scraped data
            df = pd.DataFrame([{"URL": scraped_data["URL"], "Title": scraped_data["Title"], "Paragraphs": " ".join(scraped_data["Paragraphs"])}] + 
                              [{"URL": link, "Title": data.get("Title", "No Title"), "Paragraphs": " ".join(data.get("Paragraphs", []))} 
                               for link, data in scraped_data["Linked Pages"].items()])
            df.to_csv(os.path.join(folder, f"{filename}.csv"), index=False, encoding='utf-8')  # Save data to CSV
            
        messagebox.showinfo("Success", "Data saved successfully.")  # Show success message
    except Exception as e:
        messagebox.showerror("Error", f"Error saving files: {e}")  # Show error message if an exception occurs

# Function to dynamically create input fields for URLs and filenames
def create_link_entries():
    try:
        num_links = int(entry_num_links.get())  # Get the number of links from user input
        if num_links <= 0:
            messagebox.showwarning("Input Error", "Please enter a valid number of links.")  # Show warning for invalid number
            return

        # Clear previous entries and lists of link entries and filename entries
        for widget in link_frame.winfo_children():
            widget.destroy()
        link_entries.clear()
        filename_entries.clear()

        # Create input fields for URLs and filenames based on the number of links
        for i in range(num_links):
            row_frame = tk.Frame(link_frame, bg="lightblue")
            row_frame.pack(pady=5, fill=tk.X)

            label_url = tk.Label(row_frame, text=f"URL {i + 1}:", bg="lightblue", font=("Arial", 12))
            label_url.pack(side=tk.LEFT, padx=5)
            entry_url = tk.Entry(row_frame, width=30)  # URL entry field
            entry_url.pack(side=tk.LEFT, padx=5)
            link_entries.append(entry_url)

            label_filename = tk.Label(row_frame, text="File Name:", bg="lightblue", font=("Arial", 12))
            label_filename.pack(side=tk.LEFT, padx=5)
            entry_filename = tk.Entry(row_frame, width=30)  # Filename entry field
            entry_filename.pack(side=tk.LEFT, padx=5)
            filename_entries.append(entry_filename)

            entry_url.bind("<KeyRelease>", validate_inputs)  # Bind validation function to input changes
            entry_filename.bind("<KeyRelease>", validate_inputs)

        finish_button.pack(pady=5)  # Show the finish button

    except ValueError:
        messagebox.showwarning("Input Error", "Please enter a valid number.")  # Show warning for invalid input


# Function to show folder selection and save button after input is finished
def finish_input():
    if not any(entry.get().strip() for entry in link_entries):
        messagebox.showwarning("Input Error", "Please enter at least one URL before finishing.")  # Show warning if no URLs entered
        return

    label_folder = tk.Label(link_frame, bg="lightblue", font=("Arial", 12), text="Choose folder for all files:")
    label_folder.pack(pady=5)
    global entry_folder
    entry_folder = tk.Entry(link_frame, width=50)  # Entry field for folder selection
    entry_folder.pack(pady=5)

    folder_button = tk.Button(link_frame, bg="green", fg="white", font=("Arial", 10), text="Choose Folder", command=lambda entry=entry_folder: choose_folder(entry))  # Button to choose folder
    folder_button.pack(pady=2)

    save_button.pack(pady=10)  # Show save button
    finish_button.pack_forget()  # Hide finish button

# Function to validate user inputs and enable/disable the save button based on the validity of the fields
def validate_inputs(event=None):
    if 'entry_folder' in globals():
        folder_value = entry_folder.get().strip()  # Get the folder value from entry field
    else:
        folder_value = ""

    # Enable the save button only when all fields (URLs, filenames, folder) are filled
    if all(entry.get().strip() for entry in link_entries) and all(filename.get().strip() for filename in filename_entries) and folder_value:
        save_button.config(state=tk.NORMAL, bg="green")  # Enable save button
    else:
        save_button.config(state=tk.DISABLED, bg="grey")  # Disable save button

# Tkinter GUI setup
window = tk.Tk()
window.geometry("600x500")
window.title("WEB SCRAPING AUTOMATION")
window.configure(bg="lightblue")

# Label and input for the number of links to input
label_num_links = tk.Label(window, text="How many links do you want to input?", bg="lightblue", font=("Arial", 12))
label_num_links.pack(pady=5)
entry_num_links = tk.Entry(window, width=10)
entry_num_links.pack(pady=5)

# Button to create the link input fields dynamically
create_links_button = tk.Button(window, text="Create Link Fields", command=create_link_entries, font=("Arial", 10), bg="green", fg="white")
create_links_button.pack(pady=10)

# Frame to contain the link input fields
link_frame = tk.Frame(window, bg="lightblue")
link_frame.pack(pady=10)

# Finish button to finalize the input
finish_button = tk.Button(window, bg="green", fg="white", font=("Arial", 10), text="Finish Input", command=finish_input)
finish_button.pack_forget()

# Save button to save the scraped data
save_button = tk.Button(window, text="Save Data", fg="white", font=("Arial", 10), command=save_links, state=tk.DISABLED)
save_button.pack_forget()

link_entries = []  # List to hold URL entry widgets
filename_entries = []  # List to hold filename entry widgets

window.mainloop()  # Start the Tkinter event loop
