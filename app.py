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
    household_id = None
    registered = False
    claimed = False
    message = None
    csv_path = "data/households.csv"

    if request.form.get("register"):
        household_info = request.form.get("q")
        if household_info:
            household_id = generate_id(csv_path, prefix="H")

            with open(csv_path, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([household_id, household_info, "NOT_CLAIMED", 0, ""])

            message = f"Household {household_info} registered successfully! ID: {household_id}"
            registered = True

    elif request.form.get("claim"):
        household_id = request.form.get("household_id")
        if household_id:
            balance = 300
            denominations = {"2": 30, "5": 12, "10": 10}

            with open(csv_path, "r", newline="") as file:
                rows = list(csv.reader(file))
                for row in rows:
                    if row[0] == household_id:
                        row[2:5] = ["CLAIMED", balance, json.dumps(denominations)]

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
    return(render_template("merchant_registration.html"))

@app.route("/household", methods=["GET","POST"])
def household():
    household_id = request.form.get("q")
    if household_id:
        return redirect(url_for("household_detail", household_id=household_id))
    return render_template("household.html")

@app.route("/household/<household_id>")
def household_detail(household_id):
    return render_template("household_detail.html", household_id=household_id)

@app.route("/merchant", methods=["GET","POST"])
def merchant():
    merchant_id = request.form.get("q")
    if merchant_id:
        return redirect(url_for("merchant_detail", merchant_id=merchant_id))
    return render_template("merchant.html")

@app.route("/merchant/<merchant_id>")
def merchant_detail(merchant_id):
    return render_template("merchant_detail.html", merchant_id=merchant_id)

if __name__ == "__main__":
    app.run()