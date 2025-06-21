from transformers import AutoTokenizer, AutoModelForCausalLM
device = "cuda" # the device to load the model onto

# Now you do not need to add "trust_remote_code=True"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-32B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B", device_map="auto").eval()

# tokenize the input into tokens
input_text = """<|repo_name|>library-system
<|file_sep|>library.py
class Book:
    def __init__(self, title, author, isbn, copies):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.copies = copies

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, Copies: {self.copies}"

class Library:
    def __init__(self):
        self.books = []

    def add_book(self, title, author, isbn, copies):
        book = Book(title, author, isbn, copies)
        self.books.append(book)

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def list_books(self):
        return self.books

<|file_sep|>student.py
class Student:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.borrowed_books = []

    def borrow_book(self, book, library):
        if book and book.copies > 0:
            self.borrowed_books.append(book)
            book.copies -= 1
            return True
        return False

    def return_book(self, book, library):
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
            book.copies += 1
            return True
        return False

<|file_sep|>main.py
from library import Library
from student import Student

def main():
    # Set up the library with some books
    library = Library()
    library.add_book("The Great Gatsby", "F. Scott Fitzgerald", "1234567890", 3)
    library.add_book("To Kill a Mockingbird", "Harper Lee", "1234567891", 2)
    
    # Set up a student
    student = Student("Alice", "S1")
    
    # Student borrows a book
"""
model_inputs = tokenizer([input_text], return_tensors="pt").to(device)

# Use `max_new_tokens` to control the maximum output length.
eos_token_ids = [151659, 151661, 151662, 151663, 151664, 151643, 151645]
generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=1024, do_sample=False, eos_token_id=eos_token_ids)[0]
# The generated_ids include prompt_ids, so we only need to decode the tokens after prompt_ids.
output_text = tokenizer.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

print(f"Prompt: \n{input_text}\n\nGenerated text: \n{output_text.split('<|file_sep|>')[0]}")

# the expected output as following:
"""
Generated text:
    book = library.find_book("1234567890")
    if student.borrow_book(book, library):
        print(f"{student.name} borrowed {book.title}")
    else:
        print(f"{student.name} could not borrow {book.title}")
    
    # Student returns a book
    if student.return_book(book, library):
        print(f"{student.name} returned {book.title}")
    else:
        print(f"{student.name} could not return {book.title}")
    
    # List all books in the library
    print("All books in the library:")
    for book in library.list_books():
        print(book)

if __name__ == "__main__":
    main()

"""
