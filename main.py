from tkinter import *
import requests
from bs4 import BeautifulSoup
from tkinter import messagebox
import threading

# Initialize the Tkinter window
root = Tk()
root.title("Web Scraper")
root.geometry("600x500")

# Function to find and save content based on user inputs
def find():
    url = entry_url.get()
    text_to_find = entry_tag.get()
    filename = entry_filename.get()
    
    if not url or not text_to_find or not filename:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return
    
    # Run the scraping task in a separate thread to keep the UI responsive
    threading.Thread(target=fetch_and_display, args=(url, text_to_find, filename)).start()

def fetch_and_display(url, text_to_find, filename):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        
        # Get the title of the page
        page_title = soup.title.string if soup.title else "No title found"
        
        # Find all tags containing the searched text
        found_tags = soup.find_all(lambda tag: tag.name and text_to_find.lower() in tag.get_text().lower())
        
        if found_tags:
            content = "\n\n".join([tag.get_text() for tag in found_tags])
        else:
            content = f"No content found containing the text '{text_to_find}'"
        
        # Update the Tkinter Text widget with the result
        result_text.delete(1.0, END)  # Clear previous results
        result_text.insert(INSERT, f"URL: {url}\nTitle: {page_title}\n\n")
        result_text.insert(INSERT, "Raw HTML content:\n")
        result_text.insert(INSERT, response.text)  # Display the full HTML response
        
        # Optionally, display just the content found in tags
        result_text.insert(INSERT, "\n\nScraped content based on your search:\n")
        result_text.insert(INSERT, content)
        
        # Optionally, save the content to a file
        with open(filename, "w") as file:
            file.write(content)
        
        messagebox.showinfo("Success", f"Content written to '{filename}'.")

        # Print results in Python console
        print(f"URL: {url}")
        print(f"Title: {page_title}")
        print(f"Raw HTML content:\n{response.text[:1000000]}...")  # Print the first 500 characters
        print(f"Scraped content:\n{content[:1000000]}...")  # Print the first 500 characters

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Request Error", f"Error fetching the URL: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create and place labels and entry fields for URL, tag, and filename
label_url = Label(root, text="Enter URL:", font=('Arial', 12))
label_url.place(x=20, y=30)
entry_url = Entry(root, width=50)
entry_url.place(x=150, y=32)

label_tag = Label(root, text="Find Tag:", font=('Arial', 12))
label_tag.place(x=20, y=80)
entry_tag = Entry(root, width=50)
entry_tag.place(x=150, y=82)

label_filename = Label(root, text="Save Filename:", font=('Arial', 12))
label_filename.place(x=20, y=130)
entry_filename = Entry(root, width=50)
entry_filename.place(x=150, y=132)

# Create and place the button to trigger the find function
button = Button(root, text="Fetch and Save", width=15, command=find)
button.place(x=200, y=180)

# Create a Text widget to display the results
result_text = Text(root, width=70, height=15, wrap=WORD, font=('Arial', 10))
result_text.place(x=20, y=220)

root.mainloop()
