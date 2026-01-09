# KAFKA TOPIC NAMES
class KafkaTopics:
    USER_EVENTS = "user.events"
    BOOKING_EVENTS = "booking.events"
    PAYMENT_EVENTS = "payment.events"
    TICKET_EVENTS = "ticket.events"


# CONSUMER GROUPS
KAFKA_GROUP_ID = "notification_service_group"


# KAFKA EVENT TYPES
class KafkaEventTypes:
    USER_REGISTERED = "user_registered"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_CHANGED = "password_changed"
    BOOKING_CREATED = "booking_created"
    PAYMENT_SUCCESSFUL = "payment_successful"
    PAYMENT_FAILED = "payment_failed"
    TICKET_UPLOADED = "ticket_uploaded"
