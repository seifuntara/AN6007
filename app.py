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
    message = request.args.get("message")
    household_info = None
    csv_path = "data/households.csv"

    with open(csv_path, newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == household_id:
                household_info = row
                break

    if not household_info:
        return "Household id not found", 404

    vouchers = json.loads(household_info[4])
    return render_template("household_detail.html", household_id=household_id, household_info=household_info, vouchers=vouchers, message=message)

@app.route("/household/<household_id>/redeem", methods=["POST"])
def redeem_vouchers(household_id):
    selected = request.form.getlist("redeem")  # selected voucher values
    if not selected:
        message = "No vouchers selected!"
        return redirect(url_for("household_detail", household_id=household_id, message=message))

    # Record transaction
    total_amount=0
    csv_path = "data/redemptions.csv"
    transaction_id = generate_id(csv_path, prefix="TX")
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([transaction_id, household_id, json.dumps(selected), total_amount, "PENDING", ""])

    message = f"Transaction ID: {transaction_id}"
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
    tx_id = request.form.get("tx_id")
    message = None  # for template

    if not tx_id:
        message = "TX ID missing!"
        return render_template("merchant_detail.html", merchant_id=merchant_id, message=message)

    # --- Step 1: Update redemptions CSV ---
    redemptions = []
    found = False
    csv_path = "data/redemptions.csv"
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == tx_id and row[4] == "PENDING":
                row[4] = "COMPLETED"  # update status
                row[5] = merchant_id  # assign merchant
                household_id = row[1]
                selected = row[2]
                found = True
            redemptions.append(row)

    if not found:
        message = f"Transaction {tx_id} not found or already completed!"
        return render_template("merchant_detail.html", merchant_id=merchant_id, message=message)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(redemptions)

    # --- Step 2: Update household balance ---
    rows = []
    household_found = False
    total_amount = 0
    csv_path = "data/households.csv"

    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == household_id:
                household_found = True

                # Load vouchers from household CSV
                vouchers = json.loads(row[4])

                # Convert selected vouchers from transaction CSV
                selected_vouchers = json.loads(selected)

                # Deduct selected vouchers
                for v in selected_vouchers:
                    if vouchers.get(v, 0) > 0:
                        vouchers[v] -= 1
                        total_amount += int(v)

                row[3] = str(int(row[3]) - total_amount)  # update balance
                row[4] = json.dumps(vouchers)  # save vouchers as JSON string

            rows.append(row)

    if not household_found:
        return f"Household {household_id} not found!"

    # Write back CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # --- Step 3: Render merchant page with success message ---
    message = f"Transaction {tx_id} verified successfully!"
    return render_template("merchant_detail.html", merchant_id=merchant_id, message=message)

if __name__ == "__main__":
    app.run()