let expenseLineItemIndex = 1;

document.getElementById("add-expense-item").addEventListener("click", function () {
    const lineItemsContainer = document.getElementById("expense-line-items");
    const newItem = document.createElement("div");
    newItem.classList.add("line-item", "row", "mb-3");
    newItem.innerHTML = `
        <div class="col-md-3">
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
            <button type="button" class="btn btn-danger remove-expense-item">Remove</button>
        </div>
    `;
    lineItemsContainer.appendChild(newItem);
    expenseLineItemIndex++;
});

// Remove a line item
document.addEventListener("click", function (e) {
    if (e.target && e.target.classList.contains("remove-expense-item")) {
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
        const expenseForm = document.getElementById("expense-form");
        const editExpenseForm = document.getElementById("edit-expense-form");
        if (expenseForm) {
            expenseForm.appendChild(grandTotalElem);
        } else if (editExpenseForm) {
            editExpenseForm.appendChild(grandTotalElem);
        }
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


// Handle form submission for editing requisitions
const submitexpenseChangesButton = document.getElementById("submit-expense-changes");
if (submitexpenseChangesButton) {
    submitexpenseChangesButton.addEventListener("click", async function () {
        console.log("Submit Expense Edit Form button clicked");

        const form = document.getElementById("edit-expense-form");
        if (!form) {
            console.error("Edit Expense form not found in the DOM.");
            alert("Form not found. Please refresh the page.");
            return;
        }

        const formData = new FormData(form);

        // Prepare expense data to match Pydantic model in schematic.py
        const expenseData = {
            expense_number: formData.get("expense_number"),
            description: formData.get("description"),
            line_items: [],
        };

        // Collect line items data
        const lineItems = document.querySelectorAll("#expense-line-items .line-item");
        lineItems.forEach((item, index) => {
            const idInput = item.querySelector(`[name="line_items[${index}][id]"]`);
            const item_nameInput = item.querySelector(`[name="line_items[${index}][item_name]"]`);
            const categoryInput = item.querySelector(`[name="line_items[${index}][category]"]`);
            const quantityInput = item.querySelector(`[name="line_items[${index}][quantity]"]`);
            const priceInput = item.querySelector(`[name="line_items[${index}][price]"]`);
            const amountInput = item.querySelector(`[name="line_items[${index}][amount]"]`);

            // Defensive: skip if any required field is missing
            if (!item_nameInput || !categoryInput || !quantityInput || !priceInput || !amountInput) {
                console.warn("Skipping a line item due to missing fields.");
                return;
            }

            const lineItemData = {
                id: idInput ? (idInput.value ? parseInt(idInput.value) : null) : null,
                item_name: item_nameInput.value,
                category: categoryInput.value,
                quantity: parseFloat(quantityInput.value) || 0,
                price: parseFloat(priceInput.value) || 0,
                amount: parseFloat(amountInput.value) || 0,
            };

            expenseData.line_items.push(lineItemData);
        });

        // Calculate grand total
        let grandTotal = 0;
        expenseData.line_items.forEach(item => {
            grandTotal += item.amount;
        });
        expenseData.total = grandTotal;

        const expenseFormData = new FormData();
        expenseFormData.append(
            "expense_input",
            JSON.stringify(expenseData)
        );

        console.log("Request Payload:", JSON.stringify(expenseData)); // Debugging log

        try {
            const response = await fetch(`/expense/edit_expense`, {
                method: "POST",
                body: expenseFormData,
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Server Response:", data);
                alert("Expense updated successfully");
                window.location.href = "/expense/dash";
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.message || "An error occurred"}`);
                console.error("Error Data:", errorData);
            }
        } catch (error) {
            alert("An error occurred while submitting the form.");
            console.error("Error:", error);
        }
    });
} else {
    console.warn("Submit changes button not found in the DOM.");
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
        const response = await fetch("/expense/create", {
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

// // Fetch and display pending expenses for the user
// async function loadPendingExpenses() {
//     try {
//         const response = await fetch("/expense/pending");
//         if (!response.ok) {
//             throw new Error("Failed to fetch pending expenses");
//         }
//         const html = await response.text();
//         document.getElementById("pending-expenses-container").innerHTML = html;
//     } catch (error) {
//         console.error("Error loading pending expenses:", error);
//         document.getElementById("pending-expenses-container").innerHTML = "<p class='text-danger'>Failed to load pending expenses.</p>";
//     }
// }

// <!-- Function to open the expense preview modal and display items -->
function openExpenseModal(expenseId) {
    fetch(`/expense/${expenseId}/preview`)
        .then(response => response.json())
        .then(data => {
            if (data && Array.isArray(data.expense)) {
                // Remove any existing modal to avoid duplicate IDs
                let oldModal = document.getElementById("expensePreviewModal");
                if (oldModal) {
                    oldModal.parentNode.removeChild(oldModal);
                }
                // Create the modal container
                let modalElem = document.createElement("div");
                modalElem.className = "modal fade";
                modalElem.id = "expensePreviewModal";
                modalElem.tabIndex = -1;
                modalElem.setAttribute("aria-labelledby", "expensePreviewModalLabel");
                modalElem.setAttribute("aria-hidden", "true");
                modalElem.innerHTML = `
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="expensePreviewModalLabel">Expense Line Items</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Item Name</th>
                                            <th>Quantity</th>
                                            <th>Category</th>
                                            <th>Price</th>
                                            <th>Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody id="expensePreviewTableBody"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modalElem);

                // Now the table body will always exist
                const tableBody = modalElem.querySelector("#expensePreviewTableBody");
                tableBody.innerHTML = "";
                data.expense.forEach((item, index) => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${item.item_name}</td>
                        <td>${item.quantity}</td>
                        <td>${item.category}</td>
                        <td>${item.price}</td>
                        <td>${item.amount}</td>
                    `;
                    tableBody.appendChild(row);
                });

                if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
                    const modal = new bootstrap.Modal(modalElem);
                    modal.show();
                } else {
                    alert("Bootstrap Modal is not available.");
                }
            } else {
                alert("No expense items found.");
            }
        })
        .catch(err => {
            alert("Error fetching items: " + err);
        });
}

// Function to close the modal
function closeModal() {
    const myModal = new bootstrap.Modal(document.getElementById("myModal"));
    myModal.hide(); // Close the modal using Bootstrap's modal method
}

// Close modal if clicked outside of modal content
window.onclick = function (event) {
    if (event.target == document.getElementById("myModal")) {
        closeModal();
    }
};

// <!-- Populate the reject modal with the expense ID -->
function populateExpenseRejectModal(expenseId) {
    try {
        console.log("populateRejectModal called with expenseId:", expenseId); // Debugging log

        // Ensure the modal exists in the DOM
        const rejectExpenseModal = document.getElementById("rejectExpenseModal");
        if (!rejectExpenseModal) {
            console.error("Error: Reject modal not found in the DOM.");
            return;
        }

        // Ensure the input field exists in the modal
        const expenseIdInput = document.getElementById("expense-id");
        if (expenseIdInput) {
            expenseIdInput.value = expenseId; // Set the expense ID
            console.log("Expense ID set in the modal:", expenseId); // Debugging log
        } else {
            console.error("Error: Expense ID input field not found in the Expense reject modal.");
        }
    } catch (error) {
        console.error("An unexpected error occurred while populating the reject modal:", error);
    }
}

// Function to approve a requisition
function approveExpense(id) {
    $.post("/expense/approve_expense", { id: id })
        .done(function (response) {
            if (response.status === "success") {
                alert(response.message);
                $("#status-" + id).text("Approved");
                window.location.href = "/expense/pending"; // Refresh page
            } else {
                alert(response.message);
            }
        })
        .fail(function () {
            alert("An error occurred while approving the expense.");
        });
}



// <!-- Function to open the expense approval modal -->
function openExpenseApprovalModal(expenseId) {
    fetch(`/expense/${expenseId}/approve`)
        .then(response => response.text())
        .then(html => {
            document.getElementById("expenseApprovalModalContainer").innerHTML = html;
            const modalElem = document.getElementById("expenseApprovalModal");
            if (modalElem) {
                const modal = new bootstrap.Modal(modalElem);
                modal.show();
            }
        })
        .catch(err => {
            alert("Failed to load expense approval.");
        });
}

// <!-- Function to reject an Expense -->
function rejectExpense(id) {
    if (confirm("Are you sure you want to reject this expense?")) {
        $.post("/expense/reject_expense", { id: id })
            .done(function (response) {
                if (response.status === "success") {
                    alert(response.message);
                    $("#status-" + id).text("Rejected");
                    window.location.href = "/expense/pending"; // Refresh page
                } else {
                    alert(response.message);
                }
            })
            .fail(function () {
                alert("An error occurred while rejecting the Expense.");
                window.location.href = "/expense/pending"; // Redirect to another page (dashboard or relevant page)
            });
    }
}


// JavaScript function to handle delete expense
function deleteExpense(id) {
    if (confirm("Are you sure you want to delete this expense?")) {
        fetch(`/expense/delete_expense`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `id=${id}`,
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message);
                if (data.status === "success") {
                    location.reload();
                }
            })
            .catch((error) => console.error("Error:", error));
    }
}

// Call this function from the HTML using onclick="rejectButton()"
function rejectExpenseButton() {
    // Debugging log
    console.log("Reject button clicked");

    const expenseIdInput = document.getElementById("expense-id");
    const expenseCommentInput = document.getElementById("expense-comment");

    if (!expenseIdInput || !expenseCommentInput) {
        console.error("Error: Modal elements not found in the DOM.");
        return;
    }

    const expenseId = expenseIdInput.value;
    const expenseComment = expenseCommentInput.value;

    if (!expenseComment.trim()) {
        alert("Comment is required.");
        return;
    }

    fetch("/expense/reject_expense", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `id=${expenseId}&comment=${encodeURIComponent(expenseComment)}`,
    })
        .then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Failed to reject Expenses");
            }
        })
        .then((data) => {
            alert(data.message);
            location.reload();
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred while rejecting the Expense request.");
        });
}


// View comments for a rejected expense
function viewExpenseComments(expenseId) {
    fetch(`/expense/expense_details/${expenseId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            const expenseModalBody = document.getElementById("expenseCommentsModalBody");
            if (!expenseModalBody) {
                alert("Comments modal body not found in DOM.");
                return;
            }
            // Log the data for debugging
            console.log("Comments API response:", data);

            if (
                data.status === "success" &&
                data.expense &&
                Array.isArray(data.expense.comments) &&
                data.expense.comments.length > 0
            ) {
                expenseModalBody.innerHTML = data.expense.comments.map(comment =>
                    `<div class="mb-3 border-bottom pb-2">
                        <strong>${comment.created_by || "Unknown"}</strong>
                        <span class="text-muted float-end">${comment.created_at ? new Date(comment.created_at).toLocaleString() : ""}</span>
                        <p class="mb-1">${comment.comment || ""}</p>
                    </div>`
                ).join("");
            } else if (data.status === "success") {
                expenseModalBody.innerHTML = "<p class='text-muted'>No comments available for this Espense.</p>";
            } else {
                expenseModalBody.innerHTML = `<p class='text-danger'>${data.message || "Failed to load comments."}</p>`;
            }
            const commentsModalElem = document.getElementById('expenseCommentsModal');
            if (commentsModalElem) {
                const expenseCommentsModal = new bootstrap.Modal(commentsModalElem);
                expenseCommentsModal.show();
            } else {
                alert("Comments modal not found in DOM.");
            }
        })
        .catch(err => {
            console.error("Error loading comments:", err);
            const expenseModalBody = document.getElementById("expenseCommentsModalBody");
            if (expenseModalBody) {
                expenseModalBody.innerHTML = "<p class='text-danger'>Failed to load comments.</p>";
            }
            const expensecommentsModalElem = document.getElementById('expenseCommentsModal');
            if (expensecommentsModalElem) {
                const expenseCommentsModal = new bootstrap.Modal(expensecommentsModalElem);
                expenseCommentsModal.show();
            }
        });
}
