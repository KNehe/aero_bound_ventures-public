"""Constants for groups, permissions, and other application-wide settings."""

# Constants for groups
ADMIN_GROUP_NAME = "Admins"
ADMIN_GROUP_DESCRIPTION = "Administrator group with full system permissions"

# Permission constants for Bookings
PERM_ADD_BOOKING = ("add_booking", "bookings.add_booking", "Add new bookings")
PERM_VIEW_BOOKING = ("view_booking", "bookings.view_booking", "View bookings")
PERM_CHANGE_BOOKING = ("change_booking", "bookings.change_booking", "Change bookings")
PERM_DELETE_BOOKING = ("delete_booking", "bookings.delete_booking", "Delete bookings")

# Permission constants for Users
PERM_ADD_USER = ("add_user", "users.add_user", "Add new users")
PERM_VIEW_USER = ("view_user", "users.view_user", "View users")
PERM_CHANGE_USER = ("change_user", "users.change_user", "Change users")
PERM_DELETE_USER = ("delete_user", "users.delete_user", "Delete users")

# Permission constants for Flights
PERM_ADD_FLIGHT = ("add_flight", "flights.add_flight", "Add new flights")
PERM_VIEW_FLIGHT = ("view_flight", "flights.view_flight", "View flights")
PERM_CHANGE_FLIGHT = ("change_flight", "flights.change_flight", "Change flights")
PERM_DELETE_FLIGHT = ("delete_flight", "flights.delete_flight", "Delete flights")

# Permission constants for Payments
PERM_ADD_PAYMENT = ("add_payment", "payments.add_payment", "Add new payments")
PERM_VIEW_PAYMENT = ("view_payment", "payments.view_payment", "View payments")
PERM_CHANGE_PAYMENT = ("change_payment", "payments.change_payment", "Change payments")
PERM_DELETE_PAYMENT = ("delete_payment", "payments.delete_payment", "Delete payments")

# Permission constants for Tickets
PERM_ADD_TICKET = ("add_ticket", "tickets.add_ticket", "Add new tickets")
PERM_VIEW_TICKET = ("view_ticket", "tickets.view_ticket", "View tickets")
PERM_CHANGE_TICKET = ("change_ticket", "tickets.change_ticket", "Change tickets")
PERM_DELETE_TICKET = ("delete_ticket", "tickets.delete_ticket", "Delete tickets")

# Permission constants for Admin/Stats
PERM_VIEW_STATS = ("view_stats", "admin.view_stats", "View system statistics")
PERM_VIEW_DASHBOARD = ("view_dashboard", "admin.view_dashboard", "View admin dashboard")

# Consolidated list of all admin permissions
ADMIN_PERMISSIONS = [
    # Booking permissions
    PERM_ADD_BOOKING,
    PERM_VIEW_BOOKING,
    PERM_CHANGE_BOOKING,
    PERM_DELETE_BOOKING,
    # User permissions
    PERM_ADD_USER,
    PERM_VIEW_USER,
    PERM_CHANGE_USER,
    PERM_DELETE_USER,
    # Flight permissions
    PERM_ADD_FLIGHT,
    PERM_VIEW_FLIGHT,
    PERM_CHANGE_FLIGHT,
    PERM_DELETE_FLIGHT,
    # Payment permissions
    PERM_ADD_PAYMENT,
    PERM_VIEW_PAYMENT,
    PERM_CHANGE_PAYMENT,
    PERM_DELETE_PAYMENT,
    # Ticket permissions
    PERM_ADD_TICKET,
    PERM_VIEW_TICKET,
    PERM_CHANGE_TICKET,
    PERM_DELETE_TICKET,
    # Admin permissions
    PERM_VIEW_STATS,
    PERM_VIEW_DASHBOARD,
]

# Password validation constants
MIN_PASSWORD_LENGTH = 8
