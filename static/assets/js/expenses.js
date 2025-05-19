let expenseLineItemIndex = 1;

document.getElementById("add-expense-item").addEventListener("click", function () {
    const lineItemsContainer = document.getElementById("expense-line-items");
    const newItem = document.createElement("div");
    newItem.classList.add("line-item", "row", "mb-3");
    newItem.innerHTML = `
        <div class="col-md-2">
            <div class="form-group">
                <label>Item Name</label>
                <input type="text" class="form-control" name="line_items[${expenseLineItemIndex}][item_name]" required />
            </div>
        </div>
        <div class="col-md-2">
            <div class="form-group">
                <label>Category</label>
                <select class="form-control" name="line_items[${expenseLineItemIndex}][category]" required>
                    <option value="">Select Category</option>
                    <option value="office_supplies">Office Supplies</option>
                    <option value="electronics">Electronics</option>
                    <option value="furniture">Furniture</option>
                    <option value="software">Software</option>
                </select>
            </div>
        </div>
                <div class="col-md-2">
            <div class="form-group">
                <label>Quantity</label>
                <input type="number" class="form-control amount-input" name="line_items[${expenseLineItemIndex}][quantity]" required />
            </div>
        </div>
        <div class="col-md-2">
            <div class="form-group">
                <label>Price</label>
                <input type="number" class="form-control price-input" name="line_items[${expenseLineItemIndex}][price]" required />
            </div>
        </div>
        <div class="col-md-2">
            <div class="form-group">
                <label>Amount</label>
                <input type="number" class="form-control total-input" name="line_items[${expenseLineItemIndex}][amount]" readonly />
            </div>
        </div>
        <div class="col-md-1 d-flex align-items-end">
            <button type="button" class="btn btn-danger remove-item">Remove</button>
        </div>
    `;
    lineItemsContainer.appendChild(newItem);
    expenseLineItemIndex++;
});

// Remove a line item
document.addEventListener("click", function (e) {
    if (e.target && e.target.classList.contains("remove-item")) {
        e.target.closest(".line-item").remove();
        updateGrandTotal();
    }
});

// Auto-calculate total for each line item and update grand total
function updateGrandTotal() {
    const totalInputs = document.querySelectorAll("#expense-line-items .total-input");
    let grandTotal = 0;
    totalInputs.forEach(input => {
        grandTotal += parseFloat(input.value) || 0;
    });
    let grandTotalElem = document.getElementById("grand-total");
    if (!grandTotalElem) {
        // Create grand total display if not present
        grandTotalElem = document.createElement("div");
        grandTotalElem.id = "grand-total";
        grandTotalElem.className = "mt-3 fw-bold";
        document.getElementById("expense-form").appendChild(grandTotalElem);
    }
    grandTotalElem.innerHTML = "Grand Total: <span class='text-primary'>" + grandTotal.toLocaleString() + "</span>";
}

// Auto-calculate total for each line item
document.addEventListener("input", function (e) {
    if (
        e.target.classList.contains("price-input") ||
        e.target.classList.contains("amount-input")
    ) {
        const lineItem = e.target.closest(".line-item");
        const price = parseFloat(lineItem.querySelector(".price-input").value) || 0;
        const amount = parseFloat(lineItem.querySelector(".amount-input").value) || 0;
        const totalInput = lineItem.querySelector(".total-input");
        totalInput.value = price * amount;
        updateGrandTotal();
    }
});

// Handle form submission
document.getElementById("submit-expense-form").addEventListener("click", async function () {
    const form = document.getElementById("expense-form");
    const formData = new FormData(form);

    // Prepare expense data
    const expenseData = {
        expense_number: formData.get("expense_number"),
        description: formData.get("description"),
        line_items: [],
    };

    // Collect line items data
    const lineItems = document.querySelectorAll("#expense-line-items .line-item");
    let grandTotal = 0;
    lineItems.forEach((item, index) => {
        const quantity = parseFloat(item.querySelector(`[name="line_items[${index}][quantity]"]`).value) || 0;
        const price = parseFloat(item.querySelector(`[name="line_items[${index}][price]"]`).value) || 0;
        const amount = quantity * price;
        grandTotal += amount;
        expenseData.line_items.push({
            item_name: item.querySelector(`[name="line_items[${index}][item_name]"]`).value,
            category: item.querySelector(`[name="line_items[${index}][category]"]`).value,
            quantity: quantity,
            price: price,
            amount: amount,
        });
    });

    // Optionally, you can add grandTotal to the payload if needed
    expenseData.total = grandTotal;

    // Add file attachment if present
    const attachment = document.getElementById("attachment").files[0];
    if (attachment) {
        expenseData.attachment = attachment;
    }

    // Create the request body as FormData and append the JSON part manually
    const requestFormData = new FormData();
    requestFormData.append("expense_input", JSON.stringify(expenseData));
    if (attachment) {
        requestFormData.append("attachment", attachment);
    }

    // Submit data to the server
    try {
        const response = await fetch("/requisition/create-expense", {
            method: "POST",
            body: requestFormData,
        });

        if (response.ok) {
            const data = await response.json();
            alert("Expense created successfully");
            window.location.href = "/expense/dash";
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.message || "An error occurred"}`);
        }
    } catch (error) {
        alert("An error occurred while submitting the form.");
        console.error(error);
    }
});

// Fetch and display pending expenses for the user
async function loadPendingExpenses() {
    try {
        const response = await fetch("/requisition/pending_expense");
        if (!response.ok) {
            throw new Error("Failed to fetch pending expenses");
        }
        const html = await response.text();
        document.getElementById("pending-expenses-container").innerHTML = html;
    } catch (error) {
        console.error("Error loading pending expenses:", error);
        document.getElementById("pending-expenses-container").innerHTML = "<p class='text-danger'>Failed to load pending expenses.</p>";
    }
}

// Function to open the expense preview modal
function openExpenseModal(expenseId) {
    fetch(`/requisition/expense/${expenseId}/preview`)
        .then(response => response.text())
        .then(html => {
            document.getElementById("expensePreviewModalContainer").innerHTML = html;
            const modalElem = document.getElementById("expensePreviewModal");
            if (modalElem) {
                const modal = new bootstrap.Modal(modalElem);
                modal.show();
            }
        })
        .catch(err => {
            alert("Failed to load expense preview.");
        });
}





// Handle form submission
document.getElementById("submit-expense-form").addEventListener("click", async function () {
    const form = document.getElementById("expense-form");
    const formData = new FormData(form);

    // Prepare expense data
    const expenseData = {
        expense_number: formData.get("expense_number"),
        description: formData.get("description"),
        line_items: [],
    };

    // Collect line items data
    const lineItems = document.querySelectorAll("#expense-line-items .line-item");
    let grandTotal = 0;
    lineItems.forEach((item, index) => {
        const quantity = parseFloat(item.querySelector(`[name="line_items[${index}][quantity]"]`).value) || 0;
        const price = parseFloat(item.querySelector(`[name="line_items[${index}][price]"]`).value) || 0;
        const amount = quantity * price;
        grandTotal += amount;
        expenseData.line_items.push({
            item_name: item.querySelector(`[name="line_items[${index}][item_name]"]`).value,
            category: item.querySelector(`[name="line_items[${index}][category]"]`).value,
            quantity: quantity,
            price: price,
            amount: amount,
        });
    });

    // Optionally, you can add grandTotal to the payload if needed
    expenseData.total = grandTotal;

    // Add file attachment if present
    const attachment = document.getElementById("attachment").files[0];
    if (attachment) {
        expenseData.attachment = attachment;
    }

    // Create the request body as FormData and append the JSON part manually
    const requestFormData = new FormData();
    requestFormData.append("expense_input", JSON.stringify(expenseData));
    if (attachment) {
        requestFormData.append("attachment", attachment);
    }

    // Submit data to the server
    try {
        const response = await fetch("/requisition/create-expense", {
            method: "POST",
            body: requestFormData,
        });

        if (response.ok) {
            const data = await response.json();
            alert("Expense created successfully");
            window.location.href = "/expense/dash";
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.message || "An error occurred"}`);
        }
    } catch (error) {
        alert("An error occurred while submitting the form.");
        console.error(error);
    }
});