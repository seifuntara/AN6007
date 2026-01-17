from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def main():
    return(render_template("main.html"))

@app.route("/admin",methods=["GET","POST"])
def admin():
    return(render_template("admin.html"))

@app.route("/admin/household_registration",methods=["GET","POST"])
def household_registration():
    return(render_template("household_registration.html"))

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