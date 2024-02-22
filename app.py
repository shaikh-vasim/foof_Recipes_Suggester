import streamlit as st 
import sqlite3
from datetime import date, timedelta

# Function to create a SQLite connection and cursor
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to fetch chosen foods for the current day from the database
def fetch_chosen_foods(conn, chosen_date, time=None):
    foods = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT recipe_name FROM chosen_recipes WHERE chosen_date=? AND chosen_time=?", (chosen_date, time))
        rows = cursor.fetchall()
        for row in rows:
            foods.append(row[0])
    except sqlite3.Error as e:
        print(e)
    return foods
# Function to fetch all chosen foods from the database and display them
def fetch_chosen_foods_show_all_info(conn):
    try:
        cursor = conn.cursor()
        st.dataframe(cursor.execute("SELECT * FROM chosen_recipes").fetchall())
    except sqlite3.Error as e:
        print(e)

# Function to display chosen foods for morning and evening separately in a list format
def display_suggestions_morning_evening(conn, chosen_date):
    st.write(f"Chosen foods for {chosen_date}:")
    
    # Fetch chosen foods for morning and evening
    morning_foods = fetch_chosen_foods(conn, chosen_date, time="Morning")
    evening_foods = fetch_chosen_foods(conn, chosen_date, time="Evening")

    # Display morning foods
    st.write("Morning Foods:")
    if morning_foods:
        st.write("\n".join(morning_foods))
    else:
        st.write("No morning foods selected.")

    # Display evening foods
    st.write("Evening Foods:")
    if evening_foods:
        st.write("\n".join(evening_foods))
    else:
        st.write("No evening foods selected.")

# Function to check if a recipe has been chosen within the last 3 days
def check_recipe_repetition(conn, recipe_name, current_date):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT chosen_date FROM chosen_recipes WHERE recipe_name=? ORDER BY chosen_date DESC LIMIT 1", (recipe_name,))
        row = cursor.fetchone()
        if row:
            last_chosen_date = date.fromisoformat(row[0])
            current_date = date.fromisoformat(current_date)  # Convert current_date to datetime.date
            if current_date - last_chosen_date <= timedelta(days=3):
                return True
    except sqlite3.Error as e:
        print(e)
    return False

# Function to add a new recipe to the database
def add_recipe(conn, recipe_name):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO recipes (recipe_name) VALUES (?)", (recipe_name,))
        conn.commit()
        st.success(f"Recipe '{recipe_name}' added successfully!")
    except sqlite3.Error as e:
        st.error(f"Error adding recipe: {e}")

# Function to display chosen foods and suggest recipes for the current day
def display_suggestions(conn, chosen_date):
    st.write(f"Chosen foods for {chosen_date}:")
    chosen_foods = fetch_chosen_foods(conn, chosen_date)
    unique_chosen_foods = set(chosen_foods)  # Keep only unique foods
    for food in unique_chosen_foods:
        st.write(food)

    st.write("Recipe suggestions for today:")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT recipe_name FROM recipes")
        rows = cursor.fetchall()
        for i, row in enumerate(rows, start=1):
            recipe_name = row[0]
            if not check_recipe_repetition(conn, recipe_name, chosen_date):
                st.write(f"{i}. {recipe_name}")
    except sqlite3.Error as e:
        print(e)

# Function to display all recipes in the database
def display_all_recipes(conn):
    st.write("All Recipes:")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT recipe_name FROM recipes")
        rows = cursor.fetchall()
        for i, row in enumerate(rows, start=1):
            st.write(f"{i}. {row[0]}")
    except sqlite3.Error as e:
        print(e)

# Main Streamlit app
def main():
    st.title("The Food Suggester app")

    # Create a SQLite connection
    conn = create_connection("food_database.db")
    if conn is None:
        st.error("Error: Unable to establish database connection.")
        return

    # Create tables if they don't exist
    with conn:
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS chosen_foods (food TEXT, chosen_date DATE)")
            conn.execute("CREATE TABLE IF NOT EXISTS chosen_recipes (recipe_name TEXT, chosen_date DATE, chosen_time TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS recipes (recipe_name TEXT)")
        except sqlite3.Error as e:
            st.error(f"Error creating tables: {e}")
            return

    # Determine today's date
    today = date.today().isoformat()

    # Fetch and print all chosen foods (for debugging)
    # fetch_all_chosen_foods(conn)

    # Define Streamlit tabs
    tab_choice = st.sidebar.radio("Navigation", ["Choose Food", "Add Recipe", "View all recipes"])

    if tab_choice == "Choose Food":
        display_suggestions(conn, today)
        display_suggestions_morning_evening(conn, today)
        # Finalize recipe suggestion
        st.write("Finalize Recipe:")
        recipe_choice = st.number_input("Enter the number of the recipe to finalize:")
        time_choice = st.radio("Choose the time", options=["Morning", "Evening"], key="finalize_recipe_time")
        if st.button("Finalize Recipe"):
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT recipe_name FROM recipes")
                rows = cursor.fetchall()
                recipe_to_finalize = None
                for i, row in enumerate(rows, start=1):
                    if i == recipe_choice:
                        recipe_to_finalize = row[0]
                        break
                if recipe_to_finalize:
                    # Insert the chosen recipe along with the chosen time into the chosen_recipes table
                    cursor.execute("INSERT INTO chosen_recipes (recipe_name, chosen_date, chosen_time) VALUES (?, ?, ?)", (recipe_to_finalize, today, time_choice))
                    conn.commit()
                    st.success(f"'{recipe_to_finalize}' finalized for {time_choice.lower()}!")
                else:
                    st.error("Invalid recipe choice.")
            except sqlite3.Error as e:
                st.error(f"Error finalizing recipe: {e}")

    elif tab_choice == "Add Recipe":
        st.write("Add a new recipe:")
        new_recipe = st.text_input("Enter recipe name:")
        if st.button("Add Recipe"):
            add_recipe(conn, new_recipe)
    elif tab_choice == "View all recipes":
        display_all_recipes(conn)

        st.write("all fodd info:- ")
        fetch_chosen_foods_show_all_info(conn)

if __name__ == "__main__":
    main()
