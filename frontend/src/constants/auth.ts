/**
 * Authentication and Authorization Constants
 * These should match the backend constants in backend/models/constants.py
 */

// Group names - must match backend ADMIN_GROUP_NAME
export const ADMIN_GROUP_NAME = "Admins";

// Permission codenames - must match backend permission constants
export const PERMISSIONS = {
  // Booking permissions
  ADD_BOOKING: "bookings.add_booking",
  VIEW_BOOKING: "bookings.view_booking",
  CHANGE_BOOKING: "bookings.change_booking",
  DELETE_BOOKING: "bookings.delete_booking",
  
  // User permissions
  ADD_USER: "users.add_user",
  VIEW_USER: "users.view_user",
  CHANGE_USER: "users.change_user",
  DELETE_USER: "users.delete_user",
  
  // Flight permissions
  ADD_FLIGHT: "flights.add_flight",
  VIEW_FLIGHT: "flights.view_flight",
  CHANGE_FLIGHT: "flights.change_flight",
  DELETE_FLIGHT: "flights.delete_flight",
  
  // Payment permissions
  ADD_PAYMENT: "payments.add_payment",
  VIEW_PAYMENT: "payments.view_payment",
  CHANGE_PAYMENT: "payments.change_payment",
  DELETE_PAYMENT: "payments.delete_payment",
  
  // Ticket permissions
  ADD_TICKET: "tickets.add_ticket",
  VIEW_TICKET: "tickets.view_ticket",
  CHANGE_TICKET: "tickets.change_ticket",
  DELETE_TICKET: "tickets.delete_ticket",
  
  // Admin permissions
  VIEW_STATS: "admin.view_stats",
  VIEW_DASHBOARD: "admin.view_dashboard",
} as const;

// Validation constants
export const MIN_PASSWORD_LENGTH = 8;
