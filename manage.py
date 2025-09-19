import os
from supabase import create_client, Client  # pip install supabase
from dotenv import load_dotenv  # pip install python-dotenv
from datetime import datetime  
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)
def add_member(name, email):
    payload = {"name": name,"email": email}
    resp = sb.table("members").insert(payload).execute()
    return resp.data    
def available():
    resp = sb.table("books").select("*").execute()
    return resp.data
def search():
    resp = sb.table("books").select("*").execute()
    return resp.data    
def borrow_details():
    resp = sb.table("borrow_records").select("book_id,member_id,borrow_date").execute()
    return resp.data
def delete_book():
    '''delete book which are not borrowed by anyone'''
    resp = sb.table("books").delete().not_("book_id","in",sb.table("borrow_records").select("book_id")).execute()
    return resp.data
def delete_member():
    '''delete member who have not borrowed any book'''
    resp = sb.table("members").delete().not_("member_id","in",sb.table("borrow_records").select("member_id")).execute()
    return resp.data
def update_stock(title, stock):
    payload = {
        "stock": stock
    }
    resp = sb.table("books").update(payload).eq("title",title).execute()
    return resp.data
def update_email(member_id, email):
    payload = {"email": email}
    resp = sb.table("members").update(payload).eq("member_id",member_id).execute()
    return resp.data
def return_book(bid, mid):
    book = sb.table("books").select("stock").eq("book_id", bid).single().execute()
    if not book.data:
        print("Book not found.")
        return

    stock = book.data["stock"]
    update_record = (
        sb.table("borrow_records")
        .update({"return_date": datetime.now().isoformat()})
        .eq("book_id", bid)
        .eq("member_id", mid)
        .is_("return_date", None)  
        .execute()
    )

    if not update_record.data:
        print(" No active borrow record found.")
        return
    update_stock = (
        sb.table("books")
        .update({"stock": stock + 1})
        .eq("book_id", bid)
        .execute()
    )

    if not update_stock.data:
        print("Failed to update stock. Rolling back borrow record.")
        sb.table("borrow_records").update({"return_date": None}).eq("record_id", update_record.data[0]["record_id"]).execute()
        return

    print(" Book returned successfully.")
def borrow(bid, mid):
     # Step 1: Check stock
    book_resp=sb.table('books').select("stock").eq("book_id",bid).execute()
    if not book_resp.data: 
            print("Book not found.")
            return  
    stock=book_resp.data[0]["stock"]
    if stock < 1:
                print("Book not available.")
                return  
    # Step 2: Transactional borrow
    try:    
        update_res=sb.table("books").update({"stock":stock-1}).eq("book_id",bid).execute()
        if not update_res.data:
            print("Failed to update stock.")
            return
        borrow_data={
            "member_id": mid,   
            "book_id": bid,
            "borrow_date": datetime.now().isoformat(), # keep timestamp 
            "return_date": None
        }
        insert_res=sb.table("borrow_records").insert(borrow_data).execute() 
        if not insert_res.data:
            # rollback stock update
            sb.table("books").update({"stock":stock}).eq("book_id",bid).execute()
            print("Failed to create borrow record. Rolled back stock.")
            return
        
        print("Book borrowed successfully.")
    except Exception as e:
        # rollback stock update if any error
        sb.table("books").update({"stock":stock}).eq("book_id",bid).execute()
        print("Transaction failed:", str(e))
def get_top_5_books():
    resp = sb.rpc("top_5_books").execute()
    if resp.data:
        for row in resp.data:
            print(f"{row['title']} → {row['borrow_count']} borrows")
    else:
        print("No records found.")
def overdue():
    resp = sb.rpc("overdue").execute()
    if resp.data:
        for row in resp.data:
            print(f"{row['name']} → {row['title']} overdue {row['overdue_days']} days")
    else:
        print("No records found.")
def borrwed():
    resp = sb.rpc("borrowed_books").execute()
    if resp.data:
        for row in resp.data:
            print(f"{row['name']} → total borrowed {row['total_books']}")
    else:
        print("No records found.")
if __name__ == "__main__":
    while True:
        print("\n=== LIBRARY MANAGEMENT SYSTEM ===\n")
        print("1. Add Member")
        print("2. Available Books")
        print("3. Search Books")
        print("4. Borrow Details")
        print("5. Delete Unborrowed Books")
        print("6. Delete Inactive Members")
        print("7. Update Book Stock")       
        print("8. Update Member Email")
        print("9. Borrow Book")
        print("10. Return Book")
        print("11. Top 5 Borrowed Books")
        print("12. Overdue Books")
        print("13. Members with Borrowed Books")
        print("14. Exit")
        choice = input("\nEnter your choice (1-14): ")
        
        if choice == '1':
            print("\n--- Add Member ---\n")
            name = input("Enter member name: ")
            email = input("Enter member email: ")
            result = add_member(name, email)
            print("Member added:", result)
            print("\n--- End of Add Member ---\n")

        elif choice == '2':
            print("\n--- Available Books ---\n")
            books = available()
            for book in books:
                print(book)
            print("\n--- End of Available Books ---\n")

        elif choice == '3':
            print("\n--- Search Books ---\n")
            key = input("Enter search key: ").strip().lower()
            f = 0
            for m in search():
                if key in m['author'].lower() or key in m['title'].lower() or key in m['category'].lower():
                    print("Found:", m)
                    f = 1
            if f == 0:
                print("Not found")  
            print("\n--- End of Search Books ---\n")

        elif choice == '4':
            print("\n--- Borrow Details ---\n")
            details = borrow_details()
            for detail in details:
                print(detail)
            print("\n--- End of Borrow Details ---\n")

        elif choice == '5':
            print("\n--- Delete Unborrowed Books ---\n")
            result = delete_book()
            print("Deleted books:", result)
            print("\n--- End of Delete Unborrowed Books ---\n")

        elif choice == '6':
            print("\n--- Delete Inactive Members ---\n")
            result = delete_member()
            print("Deleted members:", result)
            print("\n--- End of Delete Inactive Members ---\n")

        elif choice == '7':
            print("\n--- Update Book Stock ---\n")
            title = input("Enter book title to update stock: ")
            stock = int(input("Enter new stock value: "))
            result = update_stock(title, stock)
            print("Updated stock:", result)
            print("\n--- End of Update Book Stock ---\n")

        elif choice == '8':
            print("\n--- Update Member Email ---\n")
            member_id = int(input("Enter member ID to update email: "))
            email = input("Enter new email: ")
            result = update_email(member_id, email)
            print("Updated email:", result)
            print("\n--- End of Update Member Email ---\n")

        elif choice == '9':
            print("\n--- Borrow Book ---\n")
            bid = int(input("Enter book ID to borrow: "))
            mid = int(input("Enter member ID borrowing the book: "))
            borrow(bid, mid)
            print("\n--- End of Borrow Book ---\n")

        elif choice == '10':
            print("\n--- Return Book ---\n")
            bid = int(input("Enter book ID to return: "))
            mid = int(input("Enter member ID returning the book: "))
            return_book(bid, mid)
            print("\n--- End of Return Book ---\n")

        elif choice == '11':
            print("\n--- Top 5 Borrowed Books ---\n")
            get_top_5_books()
            print("\n--- End of Top 5 Borrowed Books ---\n")

        elif choice == '12':
            print("\n--- Overdue Books ---\n")
            overdue()
            print("\n--- End of Overdue Books ---\n")

        elif choice == '13':
            print("\n--- Members with Borrowed Books ---\n")
            borrwed()
            print("\n--- End of Members with Borrowed Books ---\n")

        elif choice == '14':
            print("\nExiting...\n")
            break

        else:
            print("\nInvalid choice. Please try again.\n")
            print("\n---\n")
