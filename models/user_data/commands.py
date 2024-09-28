from models import db
# from models.user_data.requests import RequestsModel

class CommandsModel(db.Model):
    __tablename__ = "commands"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    category = db.Column(db.String(500))
    prefix = db.Column(db.String(500), unique=True, nullable=False)
    url = db.Column(db.String(500))
    search_url = db.Column(db.String(500))
    permission_level = db.Column(db.Integer, unique=False, nullable=False, default=999)
    # request_id = db.Column(db.Integer, db.ForeignKey("requests.id"), unique=False, nullable=False)
    requests = db.relationship("RequestsModel", back_populates="command", lazy="dynamic")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}