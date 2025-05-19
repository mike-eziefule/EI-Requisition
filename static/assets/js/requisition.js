// Add a new line item
let lineItemIndex = 1;
document.getElementById("add-item").addEventListener("click", function () {
    const lineItemsContainer = document.getElementById("line-items");
    const newItem = document.createElement("div");
    newItem.classList.add("line-item", "row", "mb-3");
    newItem.innerHTML = `
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="item_name">Item Name</label>
                                <input type="text" class="form-control" name="line_items[${lineItemIndex}][item_name]" required>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="form-group">
                                <label for="quantity">Quantity</label>
                                <input type="number" class="form-control" name="line_items[${lineItemIndex}][quantity]" required>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="form-group">
                                <label for="category">Category</label>
                                <select class="form-control" name="line_items[${lineItemIndex}][category]" required>
                                    <option value="">Select Category</option>
                                    <option value="office_supplies">Office Supplies</option>
                                    <option value="electronics">Electronics</option>
                                    <option value="furniture">Furniture</option>
                                    <option value="software">Software</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="item_reason">Item Reason</label>
                                <input type="text" class="form-control" name="line_items[${lineItemIndex}][item_reason]" required>
                            </div>
                        </div>
                        <div class="col-md-1 d-flex align-items-end">
                            <button type="button" class="btn btn-danger remove-item">Remove</button>
                        </div>
                    `;
    lineItemsContainer.appendChild(newItem);
    lineItemIndex++;
});

// Remove a line item
document.addEventListener("click", function (e) {
    if (e.target && e.target.classList.contains("remove-item")) {
        e.target.closest(".line-item").remove();
    }
});

// Handle form submission for editing requisitions
const submitChangesButton = document.getElementById("submit-changes");
if (submitChangesButton) {
    submitChangesButton.addEventListener("click", async function () {
        console.log("Submit Edit Form button clicked");

        const form = document.getElementById("edit-requisition-form");
        if (!form) {
            console.error("Edit requisition form not found in the DOM.");
            alert("Form not found. Please refresh the page.");
            return;
        }

        const formData = new FormData(form);

        // Prepare requisition data
        const requisitionData = {
            request_number: formData.get("request_number"),
            description: formData.get("description"),
            line_items: [],
        };

        // Collect line items data
        const lineItems = document.querySelectorAll("#line-items .line-item");
        lineItems.forEach((item, index) => {
            const lineItemData = {
                id: item.querySelector(`[name="line_items[${index}][id]"]`)?.value || null,
                item_name: item.querySelector(`[name="line_items[${index}][item_name]"]`).value,
                quantity: parseInt(item.querySelector(`[name="line_items[${index}][quantity]"]`).value),
                category: item.querySelector(`[name="line_items[${index}][category]"]`).value,
                item_reason: item.querySelector(`[name="line_items[${index}][item_reason]"]`).value,
            };

            // Convert empty or invalid `id` to `null`
            if (!lineItemData.id || isNaN(lineItemData.id)) {
                lineItemData.id = null;
            }

            requisitionData.line_items.push(lineItemData);
        });

        console.log("Collected Requisition Data:", requisitionData);

        const attachment = document.getElementById("attachment").files[0];
        if (attachment) {
            requisitionData.attachment = attachment;
        }

        const requestFormData = new FormData();
        requestFormData.append(
            "requisition_input",
            JSON.stringify(requisitionData)
        );
        if (attachment) {
            requestFormData.append("attachment", attachment);
        }
        console.log("Request Payload:", JSON.stringify(requisitionData)); // Debugging log

        try {
            const response = await fetch(`/requisition/edit-requisition`, {
                method: "POST",
                body: requestFormData,
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Server Response:", data);
                alert("Requisition updated successfully");
                window.location.href = "/dashboard/user";
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

// Handle form submission for creating requisitions
document
    .getElementById("submit-form")
    .addEventListener("click", async function () {
        const formData = new FormData(
            document.getElementById("requisition-form")
        );

        // Prepare requisition data
        const requisitionData = {
            request_number: formData.get("request_number"),
            description: formData.get("description"),
            line_items: [],
        };

        // Collect line items data
        for (let i = 0; formData.has(`line_items[${i}][item_name]`); i++) {
            requisitionData.line_items.push({
                item_name: formData.get(`line_items[${i}][item_name]`),
                quantity: parseInt(formData.get(`line_items[${i}][quantity]`)),
                category: formData.get(`line_items[${i}][category]`),
                item_reason: formData.get(`line_items[${i}][item_reason]`),
            });
        }

        // Add file attachment if present
        const attachment = document.getElementById("attachment").files[0];
        if (attachment) {
            requisitionData.attachment = attachment;
        }

        // Create the request body as FormData and append the JSON part manually
        const requestFormData = new FormData();
        requestFormData.append(
            "requisition_input",
            JSON.stringify(requisitionData)
        );

        if (attachment) {
            requestFormData.append("attachment", attachment);
        }

        // Submit data to the server
        try {
            const response = await fetch("/requisition/create-requisition", {
                method: "POST",
                body: requestFormData,
            });

            if (response.ok) {
                // Check if the response is JSON
                const contentType = response.headers.get("Content-Type");
                if (contentType && contentType.includes("application/json")) {
                    const data = await response.json();
                    console.log(data); // Logs the response data from the server

                    // Handle success
                    alert("Requisition created successfully");
                    window.location.href = "/dashboard/user"; // Redirect to another page (dashboard or relevant page)
                } else {
                    alert("Unexpected response format.");
                }
            } else {
                // If response is not ok, try to parse the error message
                const contentType = response.headers.get("Content-Type");
                if (contentType && contentType.includes("application/json")) {
                    const errorData = await response.json();
                    alert(`Error: ${errorData.message || "An error occurred"}`);
                    console.error(errorData);
                } else {
                    alert("An unexpected error occurred.");
                }
            }
        } catch (error) {
            alert("An error occurred while submitting the form.");
            console.error(error);
        }
    });

// Function to open the modal and load items based on the selected category
function openModal(requisition_id) {
    fetch(`/category/${requisition_id}/items`)
        .then((response) => response.json())
        .then((data) => {
            const tableBody = document.querySelector("#itemTable tbody");
            if (!tableBody) {
                alert("Error: Table body not found in the DOM.");
                return;
            }

            tableBody.innerHTML = ""; // Clear existing items in modal

            // Loop through the items and add them to the modal
            data.forEach((item, index) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${item.item_name}</td>
                    <td>${item.quantity}</td>
                    <td>${item.category}</td>
                    <td>${item.item_reason}</td>
                `;
                tableBody.appendChild(row);
            });

            // Show the modal using Bootstrap's modal method
            const myModal = new bootstrap.Modal(
                document.getElementById("myModal")
            );
            myModal.show(); // Open the modal
        })
        .catch((err) => alert("Error fetching items: " + err));
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

// Function to approve a requisition
function approveRequisition(id) {
    $.post("/requisition/approve_requisition", { id: id })
        .done(function (response) {
            if (response.status === "success") {
                alert(response.message);
                $("#status-" + id).text("Approved");
                window.location.href = "/requisition/pending_request"; // Refresh page
            } else {
                alert(response.message);
            }
        })
        .fail(function () {
            alert("An error occurred while approving the requisition.");
        });
}

// Function to reject a requisition
function rejectRequisition(id) {
    if (confirm("Are you sure you want to reject this requisition?")) {
        $.post("/requisition/reject_requisition", { id: id })
            .done(function (response) {
                if (response.status === "success") {
                    alert(response.message);
                    $("#status-" + id).text("Rejected");
                    window.location.href = "/requisition/pending_request"; // Refresh page
                } else {
                    alert(response.message);
                }
            })
            .fail(function () {
                alert("An error occurred while rejecting the requisition.");
                window.location.href = "/requisition/pending_request"; // Redirect to another page (dashboard or relevant page)
            });
    }
}

// Populate the reject modal with the requisition ID
function populateRejectModal(requisitionId) {
    try {
        console.log("populateRejectModal called with requisitionId:", requisitionId); // Debugging log

        // Ensure the modal exists in the DOM
        const rejectModal = document.getElementById("rejectModal");
        if (!rejectModal) {
            console.error("Error: Reject modal not found in the DOM.");
            return;
        }

        // Ensure the input field exists in the modal
        const requisitionIdInput = document.getElementById("requisition-id");
        if (requisitionIdInput) {
            requisitionIdInput.value = requisitionId; // Set the requisition ID
            console.log("Requisition ID set in the modal:", requisitionId); // Debugging log
        } else {
            console.error("Error: Requisition ID input field not found in the reject modal.");
        }
    } catch (error) {
        console.error("An unexpected error occurred while populating the reject modal:", error);
    }
}

// JavaScript function to handle delete requisition
function deleteRequisition(id) {
    if (confirm("Are you sure you want to delete this requisition?")) {
        fetch(`/requisition/delete_requisition`, {
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
function rejectButton() {
    // Debugging log
    console.log("Reject button clicked");

    const requisitionIdInput = document.getElementById("requisition-id");
    const commentInput = document.getElementById("comment");

    if (!requisitionIdInput || !commentInput) {
        console.error("Error: Modal elements not found in the DOM.");
        return;
    }

    const requisitionId = requisitionIdInput.value;
    const comment = commentInput.value;

    if (!comment.trim()) {
        alert("Comment is required.");
        return;
    }

    fetch("/requisition/reject_requisition", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `id=${requisitionId}&comment=${encodeURIComponent(comment)}`,
    })
        .then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Failed to reject requisition");
            }
        })
        .then((data) => {
            alert(data.message);
            location.reload();
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred while rejecting the requisition.");
        });
}

// View comments for a rejected requisition
function viewComments(requisitionId) {
    fetch(`/requisition/requisition_details/${requisitionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            const modalBody = document.getElementById("commentsModalBody");
            if (!modalBody) {
                alert("Comments modal body not found in DOM.");
                return;
            }
            // Log the data for debugging
            console.log("Comments API response:", data);

            if (
                data.status === "success" &&
                data.requisition &&
                Array.isArray(data.requisition.comments) &&
                data.requisition.comments.length > 0
            ) {
                modalBody.innerHTML = data.requisition.comments.map(comment =>
                    `<div class="mb-3 border-bottom pb-2">
                        <strong>${comment.created_by || "Unknown"}</strong>
                        <span class="text-muted float-end">${comment.created_at ? new Date(comment.created_at).toLocaleString() : ""}</span>
                        <p class="mb-1">${comment.comment || ""}</p>
                    </div>`
                ).join("");
            } else if (data.status === "success") {
                modalBody.innerHTML = "<p class='text-muted'>No comments available for this requisition.</p>";
            } else {
                modalBody.innerHTML = `<p class='text-danger'>${data.message || "Failed to load comments."}</p>`;
            }
            const commentsModalElem = document.getElementById('commentsModal');
            if (commentsModalElem) {
                const commentsModal = new bootstrap.Modal(commentsModalElem);
                commentsModal.show();
            } else {
                alert("Comments modal not found in DOM.");
            }
        })
        .catch(err => {
            console.error("Error loading comments:", err);
            const modalBody = document.getElementById("commentsModalBody");
            if (modalBody) {
                modalBody.innerHTML = "<p class='text-danger'>Failed to load comments.</p>";
            }
            const commentsModalElem = document.getElementById('commentsModal');
            if (commentsModalElem) {
                const commentsModal = new bootstrap.Modal(commentsModalElem);
                commentsModal.show();
            }
        });
}



