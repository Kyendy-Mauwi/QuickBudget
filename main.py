import flet as ft
import json
import os
import threading
import time
from datetime import datetime

# --- CONFIGURATION ---
DATA_FILE = "expenses.json"
ASSETS_DIR = "assets"

def main(page: ft.Page):
    # --- APP CONFIG ---
    page.title = "QuickBudget"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 390
    page.window_height = 844
    page.bgcolor = "#F5F7FA"
    
    # --- 1. DATA LOGIC ---
    def load_data():
        if not os.path.exists(DATA_FILE):
            return {"limit": 0.0, "expenses": []}
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {"limit": 0.0, "expenses": []}

    def save_data(data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    app_data = load_data()

    # --- 2. LOGIC HANDLERS ---
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#1A1A1A"
            theme_icon.icon = ft.Icons.LIGHT_MODE
            transactions_title.color = ft.Colors.WHITE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#F5F7FA"
            theme_icon.icon = ft.Icons.DARK_MODE
            transactions_title.color = "#2E3192"
        page.update()

    def reveal_ghost_text(e):
        ghost_text.opacity = 1.0
        ghost_text.color = "#2E3192" if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.CYAN
        ghost_text.scale = 1.2
        ghost_text.update()
        
        def reset():
            time.sleep(2)
            ghost_text.opacity = 0.1
            ghost_text.color = "grey"
            ghost_text.scale = 1.0
            ghost_text.update()
        threading.Thread(target=reset, daemon=True).start()

    def add_expense(e):
        if not price_input.value or not item_input.value:
            return
        try:
            amount = float(price_input.value)
        except ValueError:
            return

        new_expense = {
            "item": item_input.value,
            "amount": amount,
            "category": category_dropdown.value,
            "date": datetime.now().strftime("%b %d")
        }

        app_data["expenses"].insert(0, new_expense)
        save_data(app_data)
        
        bottom_sheet.open = False
        item_input.value = ""
        price_input.value = ""
        page.update()
        refresh_ui()

    # NEW: Edit Expense Logic
    edit_index = [-1] # Use list to store index by reference

    def open_edit_dialog(e, index):
        expense = app_data["expenses"][index]
        edit_index[0] = index
        
        # Pre-fill fields
        edit_item_input.value = expense["item"]
        edit_price_input.value = str(expense["amount"])
        edit_category_dropdown.value = expense["category"]
        
        edit_dialog.open = True
        page.update()

    def save_edited_expense(e):
        idx = edit_index[0]
        if idx == -1: return

        try:
            amount = float(edit_price_input.value)
        except ValueError:
            return

        # Update data
        app_data["expenses"][idx]["item"] = edit_item_input.value
        app_data["expenses"][idx]["amount"] = amount
        app_data["expenses"][idx]["category"] = edit_category_dropdown.value
        
        save_data(app_data)
        edit_dialog.open = False
        page.update()
        refresh_ui()

    def delete_expense(e, index):
        app_data["expenses"].pop(index)
        save_data(app_data)
        refresh_ui()

    def save_new_budget(e):
        try:
            new_limit = float(budget_input.value)
            app_data["limit"] = new_limit
            save_data(app_data)
            budget_dialog.open = False
            page.update()
            refresh_ui()
        except ValueError:
            pass

    # --- 3. UI COMPONENTS ---

    # Theme Icon
    theme_icon = ft.IconButton(
        ft.Icons.DARK_MODE, 
        icon_color=ft.Colors.GREY_500, 
        on_click=toggle_theme
    )

    # Budget Dialog
    budget_input = ft.TextField(label="New Budget Amount", keyboard_type=ft.KeyboardType.NUMBER)
    budget_dialog = ft.AlertDialog(
        title=ft.Text("Set Monthly Budget"),
        content=budget_input,
        actions=[ft.TextButton("Save", on_click=save_new_budget)]
    )

    def open_budget_dialog(e):
        budget_input.value = str(app_data["limit"])
        budget_dialog.open = True
        page.update()
        
    # NEW: Edit Expense Dialog
    edit_item_input = ft.TextField(label="Item Name")
    edit_price_input = ft.TextField(label="Amount (KES)", keyboard_type=ft.KeyboardType.NUMBER)
    edit_category_dropdown = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(x) for x in ["Food", "Transport", "Bills", "Shopping", "Entertainment"]]
    )
    
    edit_dialog = ft.AlertDialog(
        title=ft.Text("Edit Transaction"),
        content=ft.Column([
            edit_item_input,
            edit_price_input,
            edit_category_dropdown
        ], tight=True, width=300),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: setattr(edit_dialog, 'open', False) or page.update()),
            ft.TextButton("Save Changes", on_click=save_edited_expense),
        ]
    )

    # Dashboard Card
    total_text = ft.Text("KES 0.00", size=32, weight=ft.FontWeight.BOLD, color="white")
    progress_bar = ft.ProgressBar(value=0, color="#00D2BA", bgcolor="white24", height=6)
    limit_text = ft.Text("", color="white70", size=12)

    # Logo Logic
    logo_path = f"{ASSETS_DIR}/logo.png"
    if os.path.exists(logo_path):
        app_logo = ft.Image(src=logo_path, width=40, height=40, fit="contain", border_radius=8)
    else:
        app_logo = ft.Icon(ft.Icons.WALLET, size=35, color="white")

    dashboard_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Row([
                    app_logo,
                    ft.Container(width=10),
                    ft.Text("QuickBudget Pro", color="white", weight=ft.FontWeight.BOLD, size=18)
                ]),
                ft.IconButton(ft.Icons.EDIT, icon_color="white70", icon_size=20, on_click=open_budget_dialog)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=20),
            ft.Text("Total Spent", color="white70", size=14),
            total_text,
            ft.Container(height=15),
            progress_bar,
            ft.Container(height=5),
            
            ft.Row([
                limit_text,
                ft.Text("Budget", size=10, color="white30") 
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
        ]),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=["#2E3192", "#1BFFFF"],
        ),
        padding=25,
        border_radius=20,
        margin=ft.Margin(left=20, top=0, right=20, bottom=0),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLUE_GREY_200, offset=ft.Offset(0, 10))
    )

    # Inputs
    item_input = ft.TextField(label="Item Name", border_color=ft.Colors.BLUE_GREY_100, bgcolor=ft.Colors.SURFACE)
    price_input = ft.TextField(label="Amount (KES)", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.Colors.BLUE_GREY_100, bgcolor=ft.Colors.SURFACE)
    category_dropdown = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(x) for x in ["Food", "Transport", "Bills", "Shopping", "Entertainment"]],
        value="Food",
        bgcolor=ft.Colors.SURFACE,
        border_color=ft.Colors.BLUE_GREY_100
    )

    save_button = ft.Button(
        content=ft.Text("Save Expense", size=16, color="white", weight=ft.FontWeight.BOLD),
        style=ft.ButtonStyle(bgcolor="#2E3192", shape=ft.RoundedRectangleBorder(radius=12), padding=15),
        width=400,
        on_click=add_expense
    )

    bottom_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Text("Add New Expense", size=20, weight=ft.FontWeight.BOLD, color="#2E3192"),
                ft.Divider(),
                item_input, price_input, category_dropdown,
                ft.Container(height=10),
                save_button
            ], tight=True),
            padding=30,
            border_radius=ft.BorderRadius.only(top_left=25, top_right=25),
            bgcolor=ft.Colors.SURFACE
        )
    )

    def open_bottom_sheet(e):
        bottom_sheet.open = True
        page.update()

    fab = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE),
        bgcolor="#2E3192",
        on_click=open_bottom_sheet
    )

    ghost_text = ft.Text("Mauwi Made", color="grey", opacity=0.1, size=12, weight=ft.FontWeight.BOLD, animate_opacity=300, animate_scale=300)
    
    expenses_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    transactions_title = ft.Text("Recent Transactions", weight=ft.FontWeight.BOLD, size=18, color="#2E3192")

    def refresh_ui():
        expenses_column.controls.clear()
        total = 0.0
        
        for i, expense in enumerate(app_data["expenses"]):
            total += expense['amount']
            icon_data = ft.Icons.SHOPPING_BAG
            if expense['category'] == "Food": icon_data = ft.Icons.RESTAURANT
            elif expense['category'] == "Transport": icon_data = ft.Icons.DIRECTIONS_CAR
            elif expense['category'] == "Bills": icon_data = ft.Icons.LIGHTBULB
            
            row = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Container(content=ft.Icon(icon_data, color="#2E3192", size=20), padding=10, bgcolor="#EEF0F7", border_radius=50),
                        ft.Column([
                            ft.Text(expense['item'], weight=ft.FontWeight.BOLD, color="#333333"),
                            ft.Text(expense['date'], size=12, color="grey")
                        ], spacing=2),
                    ]),
                    ft.Row([
                        ft.Text(f"- {expense['amount']:.0f}", weight=ft.FontWeight.BOLD, color="#E53935"),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="grey", icon_size=18, on_click=lambda e, idx=i: delete_expense(e, idx))
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15, 
                bgcolor=ft.Colors.WHITE, 
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
                
                # NEW: On click opens the edit dialog
                on_click=lambda e, idx=i: open_edit_dialog(e, idx)
            )
            expenses_column.controls.append(row)

        # Add Ghost Text at the end
        expenses_column.controls.append(
            ft.Container(
                content=ghost_text,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 30, 0, 80),
                on_click=reveal_ghost_text
            )
        )

        total_text.value = f"KES {total:,.2f}"
        limit = app_data["limit"]
        percent = min(total / limit, 1.0) if limit > 0 else 0
        progress_bar.value = percent
        
        remaining = limit - total
        if remaining >= 0:
            limit_text.value = f"KES {remaining:,.2f} Left"
            limit_text.color = "white70"
            progress_bar.color = "#00D2BA"
        else:
            limit_text.value = f"Over Budget by KES {abs(remaining):,.2f}"
            limit_text.color = "#FF8A80" 
            progress_bar.color = "#FF5252"
        
        page.update()

    # --- 4. LAYOUT ASSEMBLY ---
    
    page.overlay.append(bottom_sheet)
    page.overlay.append(budget_dialog)
    # NEW: Add Edit Dialog to overlay
    page.overlay.append(edit_dialog)

    page.add(
        ft.Column([
            ft.Container(height=50),
            
            ft.Container(
                content=ft.Row([
                    ft.Container(width=10), 
                    theme_icon
                ], alignment=ft.MainAxisAlignment.END), 
                padding=ft.Padding(left=10, right=10, top=0, bottom=10)
            ),
            
            dashboard_card,
            
            ft.Container(padding=ft.Padding(left=20, right=20, top=20, bottom=0), content=transactions_title),
            
            ft.Container(content=expenses_column, padding=20, expand=True),
        ], expand=True)
    )
    
    page.floating_action_button = fab
    refresh_ui()

if __name__ == "__main__":
    ft.run(main)