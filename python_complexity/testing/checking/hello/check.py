import math

# Globals everywhere (code smell)
taxRate = 0.08
discount = 0.05
dataList = []

# Function with dead code, poor naming, long length, magic numbers
def processData(customerData):
    temp = 12345  # unused variable (dead code)
    x = 0  # unclear name
    for i in range(len(customerData)):
        print("Processing item")
        x = x + 1
        # Dead code (this will never run)
        if False:
            print("This never runs")
        price = customerData[i]['price']
        quantity = customerData[i]['qty']
        total = price * quantity
        taxed = total + (total * 0.08)  # magic number
        print("Total: ", taxed)
        final = taxed - (taxed * discount)
        print("Final: ", final)

    for i in range(len(customerData)):  # Duplicate loop (duplicate code)
        price = customerData[i]['price']
        quantity = customerData[i]['qty']
        total = price * quantity
        taxed = total + (total * 0.08)
        print("Recalculated Total: ", taxed)

# Inconsistent style, long method, hardcoded strings
def DoTheThings(user):
    if user == "admin":
        print("Welcome admin")
    elif user == "guest":
        print("Welcome guest")
    elif user == "admin":  # Duplicate condition
        print("Still admin")
    else:
        print("unknown user")

    x = math.pow(2, 3)
    y = math.pow(2, 3)
    z = math.pow(2, 3)
    print(x + y + z)

# God class behavior
class ReportManager:
    def generate(self, data):
        for d in data:
            print("Generating report for", d)
            if d['status'] == 'approved':
                print("Approved!")
            elif d['status'] == 'rejected':
                print("Rejected!")
            else:
                print("Pending...")

        # Dead method
        self.do_nothing()

    def do_nothing(self):
        pass  # Dead code

# Unused function
def neverCalled():
    print("This function is never called")

# Commented out code
# def oldFunction():
#     print("Old logic")

# Tight coupling via global variable
def applyGlobalDiscount(price):
    return price - (price * discount)

# Another long, repetitive function
def calculateInvoices(invoices):
    for inv in invoices:
        subtotal = inv['amount']
        taxed = subtotal + (subtotal * 0.08)
        final = taxed - (taxed * discount)
        print("Invoice final: ", final)

        # Repeated logic
        taxed2 = subtotal + (subtotal * 0.08)
        final2 = taxed2 - (taxed2 * discount)
        print("Repeated invoice final: ", final2)

# Sample data for test
if __name__ == "__main__":
    customers = [
        {"price": 100, "qty": 2},
        {"price": 200, "qty": 1},
    ]
    invoices = [{"amount": 300}, {"amount": 150}]
    processData(customers)
    DoTheThings("admin")
    ReportManager().generate(invoices)
    calculateInvoices(invoices)
    print("Done.")
