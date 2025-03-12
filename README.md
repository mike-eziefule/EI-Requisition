# EI-Requisition

I'll break it down into steps to help you build this requisition website using Bootstrap, HTML, and FastAPI. The project involves creating several user dashboards (Requester, Storekeeper, Manager, CEO) with a request approval flow and various features such as adding/removing line items, uploading attachments, and status tracking.

## 1. Project Overview & Structure
The project will have four main pages (or dashboards):

*# Requester Dashboard: Where the requester creates a new requisition request.
Storekeeper Dashboard: Where the storekeeper approves or denies the requisition.
Manager Dashboard: Where the manager reviews and approves/denies the request.
CEO Dashboard: The final step, where the CEO can approve/deny the request.
In addition, we'll need to:

Implement a status bar showing the request's approval stages.
Support attachments (like images) for each requisition.
Add comments at each stage for feedback.
2. Project Structure
We will organize the project with the following structure:


