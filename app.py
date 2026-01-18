from flask import Flask, request, render_template, redirect, url_for
import csv
import os
import json

app = Flask(__name__)

def generate_id(csv_file, prefix, column_index=0):
    with open(csv_file, mode="r", newline="") as file:
        reader = csv.reader(file)
        return f"{prefix}{len(list(reader)):03d}"

@app.route("/",methods=["GET","POST"])
def main():
    return(render_template("main.html"))

@app.route("/admin",methods=["GET","POST"])
def admin():
    return(render_template("admin.html"))

@app.route("/admin/household_registration", methods=["GET", "POST"])
def household_registration():
    registered = False
    claimed = False
    message = None
    household_id = None
    csv_path = "data/households.csv"

    if request.form.get("register"):
        household_info = request.form.get("q")
        household_id = generate_id(csv_path, prefix="H")

        with open(csv_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([household_id, household_info, "NOT_CLAIMED", 0, ""])

        message = f"Household {household_info} registered successfully! ID: {household_id}"
        registered = True

    elif request.form.get("claim"):
        household_id = request.form.get("household_id")
        balance = 300
        denominations = {"2": 30, "5": 12, "10": 10}

        with open(csv_path, "r", newline="") as file:
            rows = list(csv.reader(file))
            for row in reversed(rows):
                if row[0] == household_id:
                    row[2:5] = ["CLAIMED", balance, json.dumps(denominations)]
                    break

        with open(csv_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        message = f"Household {household_id} successfully claimed!"
        claimed = True

    return render_template(
        "household_registration.html",
        message=message,
        registered=registered,
        claimed=claimed,
        household_id=household_id
    )

@app.route("/admin/merchant_registration",methods=["GET","POST"])
def merchant_registration():
    registered = False
    message = None
    csv_path = "data/merchants.csv"

    if request.form.get("register"):
        merchant_id = generate_id(csv_path, prefix="M")
        merchant_info = request.form.get("q")

        with open(csv_path, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([merchant_id, merchant_info])

        message = f"Merchant {merchant_info} registered successfully! ID: {merchant_id}"
        registered = True

    return render_template("merchant_registration.html", message=message, registered=registered)

@app.route("/household", methods=["GET","POST"])
def household():
    if request.form.get("enter"):
        household_id = request.form.get("q")
        return redirect(url_for("household_detail", household_id=household_id))
    return render_template("household.html")

@app.route("/household/<household_id>")
def household_detail(household_id):
    household_info = None
    csv_path = "data/households.csv"

    with open(csv_path, newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == household_id and row[2] == "CLAIMED":
                household_info = row
                break

    if not household_info:
        return "Household id not found", 404

    vouchers = json.loads(household_info[4])
    return render_template("household_detail.html", household_id=household_id, household_info=household_info, vouchers=vouchers)

@app.route("/household/<household_id>/redeem", methods=["POST"])
def redeem_vouchers(household_id):
    selected_vouchers = request.form.getlist("redeem")
    if not selected_vouchers:
        message = "No vouchers selected!"
        return redirect(url_for("household_detail", household_id=household_id, message=message))
    csv_path = "data/redemptions.csv"
    transaction_id = generate_id(csv_path, prefix="TX")
    total_amount = int(request.form.get("total_amount", 0))
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([transaction_id, household_id, "", total_amount, json.dumps(selected_vouchers), "PENDING"])
    message = f"Please redeem Voucher ID to merchant: {transaction_id}"
    return redirect(url_for("household_detail", household_id=household_id, message=message))

@app.route("/merchant", methods=["GET","POST"])
def merchant():
    if request.form.get("enter"):
        merchant_id = request.form.get("q")
        return redirect(url_for("merchant_detail", merchant_id=merchant_id))
    return render_template("merchant.html")

@app.route("/merchant/<merchant_id>")
def merchant_detail(merchant_id):
    merchant_info = None
    csv_path = "data/merchants.csv"

    with open(csv_path, newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == merchant_id:
                merchant_info = row
                break

    if not merchant_info:
        return "Merchant id not found", 404

    return render_template("merchant_detail.html", merchant_id=merchant_id, merchant_info=merchant_info)

@app.route("/merchant/<merchant_id>/verify", methods=["POST"])
def merchant_verify(merchant_id):
    voucher_id = request.form.get("voucher_id")
    message = None  # for template

    # --- Step 1: Update redemptions CSV ---
    found = False
    csv_path = "data/redemptions.csv"
    with open(csv_path, "r", newline="") as file:
            rows = list(csv.reader(file))

    for row in rows:
        if row[0] == voucher_id and row[5] == "PENDING":
            row[5] = "COMPLETED"
            row[2] = merchant_id
            household_id = row[1]
            total_amount = row[3]
            selected_vouchers = row[4]
            found = True
            break

    if not found:
        message = "Voucher Invalid"
        return render_template("merchant_detail.html", merchant_id=merchant_id, message=message)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # --- Step 2: Update household balance ---
    csv_path = "data/households.csv"
    with open(csv_path, "r", newline="") as file:
        rows = list(csv.reader(file))
        for row in rows:
            if row[0] == household_id:                
                vouchers = json.loads(row[4])
                for v in json.loads(selected_vouchers):
                    vouchers[v] -= 1
                row[3] = str(int(row[3]) - total_amount)  # update balance
                row[4] = json.dumps(vouchers)  # save vouchers as JSON string

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # --- Step 3: Render merchant page with success message ---
    message = "Voucher redeemed successfully!"
    return render_template("merchant_detail.html", merchant_id=merchant_id, message=message)

if __name__ == "__main__":
    app.run()