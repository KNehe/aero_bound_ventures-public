from sqlmodel import Session, text


class SqlModelDatabaseHealthProbe:
    service_name = "database"

    def __init__(self, session: Session):
        self.session = session

    def check(self) -> None:
        self.session.exec(text("SELECT 1"))
